# syntax=docker/dockerfile:1.6
FROM ubuntu:24.04

# Optional (just for debugging multi-arch builds)
ARG BUILDPLATFORM
ARG TARGETPLATFORM
ARG TARGETARCH

ENV DEBIAN_FRONTEND=noninteractive

# Base packages (present on both amd64 & arm64)
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates wget rsyslog rsyslog-gnutls gettext-base \
      python3 python3-yaml python3-jinja2 \
  && rm -rf /var/lib/apt/lists/*

# Intake trust (keep if you need it)
RUN wget -O /DEFENDIFY-MDR-intake.pem https://assets.defendify.com/mdr/v2/DEFENDIFY-MDR-intake.pem

# Defaults (override at runtime)
ENV DISK_SPACE=32g \
    MEMORY_MESSAGES=100000 \
    REGION=FRA1

# Rsyslog baseline
RUN rm -f /etc/rsyslog.d/50-default.conf

# App files (DO NOT bake intakes.yaml; mount it at runtime)
COPY generate_config.py /generate_config.py
COPY rsyslog-imstats /etc/logrotate.d/rsyslog-imstats
COPY rsyslog.conf /rsyslog.conf
COPY entrypoint.sh /entrypoint.sh
COPY template.j2 /template.j2
COPY template_tls.j2 /template_tls.j2
COPY stats_template.j2 /stats_template.j2

# Hygiene
RUN set -eux; sed -i 's/\r$//' /entrypoint.sh /generate_config.py || true; chmod +x /entrypoint.sh

# OCI labels (nice for GHCR)
LABEL org.opencontainers.image.title="Defendify Log Concentrator" \
      org.opencontainers.image.source="https://github.com/defendify/defendify-docker-concentrator" \
      org.opencontainers.image.description="Rsyslog-based concentrator/forwarder" \
      org.opencontainers.image.licenses="Apache-2.0"

ENTRYPOINT ["/entrypoint.sh"]
CMD ["rsyslogd","-n"]
