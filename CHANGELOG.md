# Changelog

All notable changes with the Defendify concentrator will be documented in this file.

## [2.8.1]

- Added `action.resumeRetryCount=-1` and `action.resumeInterval=30` to all output actions so queued logs are resent after a network outage instead of the action staying suspended.
- Memory queue is now per intake: `MEMORY_MESSAGES` is split evenly across intakes, and an intake can set its own `queue_size` in `intakes.yaml`.
- `rsyslog.conf` is now rendered by `generate_config.py` (Jinja) instead of `envsubst`.
- Forwarder monitoring stats now reset counters between reports (`ResetCounters="on"`).
- Fixed a stray character at the start of `template_tls.j2` that broke the TLS input.
- `docker-compose.yml` now rotates the container's console logs (3 x 50 MB) so debug output can't fill the host disk.
- Every queue now has a disk limit. Previously only the main queue was capped by `DISK_SPACE`, and the per-intake queues (where nearly all logs go) could grow until the host disk was full. `DISK_SPACE` is now split across all queues, and lowered at startup if needed so the disk stays under `DISK_MAX_PERCENT` (default 80%).
- Forwarder monitoring now sends a `logs_dropped` alert to the forwarder intake when a queue drops logs because it's full.
- New `STATS_INTERVAL` env var (seconds, default 300) controls how often forwarder monitoring reports.
- `/var/log/rsyslog-stats.log` is now actually rotated (10 MB, 3 compressed copies). The logrotate config was shipped but nothing in the container ever ran it.
- Intake queues no longer throttle TCP senders at 70% full (`queue.lightDelayMark`). Previously TCP intakes were slowed to a crawl during an outage before the disk queue ever engaged.
- A full intake queue now drops new logs immediately (`queue.timeoutEnqueue="0"`) instead of holding the input for 2 seconds per log. TCP and TLS inputs share a small worker pool, so two full TCP intakes could stop a healthy TLS intake from receiving anything.
- Known limit: restarting the concentrator during an outage loses the batch the output was retrying (at most 1024 logs per intake). If an intake queue is also at its disk limit, its in-memory logs (up to its `queue_size`) are lost too. Neither is reported in `logs_dropped` alerts.

## [2.8]

- Rewrote container to work in both AMDx64 and ARMx64 environments.
- Fixes to TLS communication code.
- Updated to work off of Ubuntu 24.04

## [2.7.1b]

- Small fixes for output templates.

## [2.7.1]

- Initial public release.
