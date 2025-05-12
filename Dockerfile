# Use an official Python image.
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# 1) System-Tools installieren
RUN apt-get update && \
    apt-get install -y \
      curl \
      xz-utils \
      default-jre-headless \
      unzip \
    && rm -rf /var/lib/apt/lists/*

# 2) Trivy CLI installieren
RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh \
  | sh -s -- -b /usr/local/bin

# 2.1) OWASP Dependency-Check installieren
ARG DC_VER=8.0.2
RUN curl -sSL https://github.com/jeremylong/DependencyCheck/releases/download/v${DC_VER}/dependency-check-${DC_VER}-release.zip \
    -o /tmp/dc.zip && \
    unzip /tmp/dc.zip -d /usr/local && \
    ln -s /usr/local/dependency-check/bin/dependency-check.sh /usr/local/bin/dependency-check && \
    rm /tmp/dc.zip

# 3) Set Commit ID
ENV CURRENT_COMMIT_ID=d3fdaf43eb639319cb757f3d19dfbef4b9312ed3

# 4) Code & Requirements
COPY ./app /app
RUN pip install --no-cache-dir -r /app/requirements.txt

# 5) Start-Skript + Analyse-Ordner
RUN chmod +x /app/start.sh
RUN mkdir -p /app/analysis

# 6) Entry
CMD ["/app/start.sh"]
