#!/usr/bin/env python

import os
import re

import yaml
from jinja2 import Environment, FileSystemLoader


def is_intake_key(intake_key: str) -> re.Match[str] | None:
    pattern = "^[a-zA-Z0-9]{16}"
    return re.search(pattern, intake_key)


def parse_size(value: str) -> int:
    # Same size suffixes as rsyslog: lowercase is 1000-based, uppercase is 1024-based
    match = re.fullmatch(r"\s*(\d+)\s*([kmgtKMGT]?)\s*", str(value))
    if not match:
        raise ValueError(f"Invalid size: {value}")
    number, suffix = int(match.group(1)), match.group(2)
    if not suffix:
        return number
    power = "kmgt".index(suffix.lower()) + 1
    return number * (1000 if suffix.islower() else 1024) ** power


def human_size(num_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if num_bytes < 1000:
            return f"{num_bytes:.0f}{unit}"
        num_bytes /= 1000
    return f"{num_bytes:.1f}TB"


def directory_size(path: str) -> int:
    total = 0
    for root, _, files in os.walk(path):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                pass
    return total


def queue_disk_budget() -> int:
    """Disk space the queues may use so the whole disk stays under DISK_MAX_PERCENT."""
    budget = parse_size(os.getenv("DISK_SPACE", "32g"))
    max_percent = float(os.getenv("DISK_MAX_PERCENT", 80))
    if not hasattr(os, "statvfs") or not os.path.isdir(QUEUE_DIR):
        return budget

    st = os.statvfs(QUEUE_DIR)
    used = (st.f_blocks - st.f_bfree) * st.f_frsize
    capacity = used + st.f_bavail * st.f_frsize
    # Existing queue files count toward the budget, not against it
    used_by_others = used - directory_size(QUEUE_DIR)
    limit = int(capacity * max_percent / 100) - used_by_others

    to_print.append(
        f"Disk: {human_size(capacity)} total, {human_size(used_by_others)} used by other files, "
        f"queues capped at {max_percent:g}% of disk"
    )
    if limit < budget:
        to_print.append(
            f"WARNING: DISK_SPACE ({human_size(budget)}) would push the disk past "
            f"{max_percent:g}%, queues limited to {human_size(max(limit, 0))}"
        )
        budget = limit
    return budget


def activate_monitoring(item: dict[str, str]) -> None:
    to_print.append("Forwarder monitoring is active")
    to_print.append("Intake key: " + str(item["intake_key"]))
    to_print.append("Queue size: " + str(item["queue_size"]))
    to_print.append("Queue disk limit: " + human_size(item["disk_space"]))
    to_print.append("")
    config = template_stats.render(item)
    filename = f"/etc/rsyslog.d/stats_{item['name']}.conf"
    # Write the generated content to the file
    with open(filename, "w") as f:
        f.write(config)


QUEUE_DIR = "/var/spool/rsyslog"
# rsyslog can't use a disk queue smaller than a couple of its 1MB queue files
MIN_QUEUE_DISK = 10 * 1000 * 1000

to_print = []

# Open input config file
with open("intakes.yaml", "r") as fyaml:
    data = yaml.safe_load(fyaml)

intakes = data.get("intakes") or []
# MEMORY_MESSAGES is split evenly across intakes unless an intake sets queue_size
default_queue_size = round(int(os.getenv("MEMORY_MESSAGES", 100000)) / max(len(intakes), 1))
# The disk budget is split evenly across every intake queue plus the main queue
disk_per_queue = max(queue_disk_budget() // (len(intakes) + 1), MIN_QUEUE_DISK)

# Generate main rsyslog config file
with open("/etc/rsyslog.conf", "w") as f:
    f.write(
        Environment(loader=FileSystemLoader("."))
        .get_template("rsyslog.conf")
        .render(env=os.environ, disk_space=disk_per_queue)
    )

# Load jinja template
template = Environment(loader=FileSystemLoader(".")).get_template("template.j2")
template_tls = Environment(loader=FileSystemLoader(".")).get_template("template_tls.j2")
template_stats = Environment(loader=FileSystemLoader(".")).get_template(
    "stats_template.j2"
)

# Identify the region, futureproofing for if additional regions are added
region = os.getenv("REGION")
if region:
    region = region.lower()
if region == "usa1":
    endpoint = "intake.mdr.defendify.com"
else:
    endpoint = "intake.mdr.defendify.com"

i = 1
to_print.append("")
to_print.append("These Intakes have been set up")
to_print.append("-----------------------------")

# Generate one file per intake
for item in intakes:
    if not is_intake_key(item["intake_key"]):
        print(
            f"ERROR: The Intake Key provided for Intake Name {item['name']} is incorrect. Exiting..."
        )
        exit(0)

    item["endpoint"] = endpoint
    item["queue_size"] = item.get("queue_size") or default_queue_size
    item["disk_space"] = disk_per_queue

    name_origin = item["name"]
    item["name"] = item["name"].replace(" ", "_").lower()

    if item.get("stats") is not None and item.get("stats") is not False:
        activate_monitoring(item)
        continue

    to_print.append("Intake name: " + str(name_origin))
    to_print.append("Protocol: " + str(item["protocol"]))
    to_print.append("Port: " + str(item["port"]))
    to_print.append("Intake key: " + str(item["intake_key"]))
    to_print.append("Queue size: " + str(item["queue_size"]))
    to_print.append("Queue disk limit: " + human_size(item["disk_space"]))
    to_print.append("")

    if item["protocol"].lower() == "tls":
        config = template_tls.render(item)
    else:
        config = template.render(item)
    filename = f"/etc/rsyslog.d/{i}_{item['name']}.conf"
    # Write the generated content to the file
    with open(filename, "w") as f:
        f.write(config)
    i = i + 1

# Check additional conf
XTENDED_CONF = "/extended_conf/"
if os.path.exists(XTENDED_CONF):
    for file in os.listdir(XTENDED_CONF):
        if file.endswith(".conf"):
            to_print.append(
                "Detected an additonal intake defined in file {}".format(file)
            )

for line in to_print:
    print(line)
