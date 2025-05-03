# Use an official Python image.
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# 1) System-Tools (curl, xz-utils, Java, unzip)
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

# 2.2) OWASP Dependency-Check CLI installieren
ARG DC_VER=8.0.2
RUN curl -sSL https://github.com/jeremylong/DependencyCheck/releases/download/v${DC_VER}/dependency-check-${DC_VER}-release.zip \
    -o /tmp/dc.zip && \
    unzip /tmp/dc.zip -d /usr/local && \
    ln -s /usr/local/dependency-check/bin/dependency-check.sh /usr/local/bin/dependency-check && \
    rm /tmp/dc.zip

# 3) Application-Code
COPY ./app /app

# 4) Python-Abhängigkeiten
RUN pip install --no-cache-dir -r /app/requirements.txt

# 5) Start-Skript
COPY app/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# 6) Sicherheitsanalyse-Dateien
COPY app/analysis /app/analysis

CMD ["/app/start.sh"]
