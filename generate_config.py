#!/usr/bin/env python

import os
import re

import yaml
from jinja2 import Environment, FileSystemLoader


def is_intake_key(intake_key: str) -> re.Match[str] | None:
    pattern = "^[a-zA-Z0-9]{16}"
    return re.search(pattern, intake_key)


def activate_monitoring(item: dict[str, str]) -> None:
    to_print.append("Forwarder monitoring is active")
    to_print.append("Intake key: " + str(item["intake_key"]))
    to_print.append("")
    config = template_stats.render(item)
    filename = f"/etc/rsyslog.d/stats_{item['name']}.conf"
    # Write the generated content to the file
    with open(filename, "w") as f:
        f.write(config)


# Open input config file
with open("intakes.yaml", "r") as fyaml:
    data = yaml.safe_load(fyaml)

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
to_print = []
to_print.append("These Intakes have been set up")
to_print.append("-----------------------------")

# Generate one file per intake
for item in data.get("intakes", []):
    if not is_intake_key(item["intake_key"]):
        print(
            f"ERROR: The Intake Key provided for Intake Name {item['name']} is incorrect. Exiting..."
        )
        exit(0)

    item["endpoint"] = endpoint

    name_origin = item["name"]
    item["name"] = item["name"].replace(" ", "_").lower()

    if item.get("stats") is not None and item.get("stats") is not False:
        activate_monitoring(item)
        continue

    to_print.append("Intake name: " + str(name_origin))
    to_print.append("Protocol: " + str(item["protocol"]))
    to_print.append("Port: " + str(item["port"]))
    to_print.append("Intake key: " + str(item["intake_key"]))
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
