# Use an official Python image.
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# 1) System-Tools installieren (curl + xz-utils für das Trivy-Install-Script)
RUN apt-get update && \
    apt-get install -y \
      curl \
      xz-utils \
    && rm -rf /var/lib/apt/lists/*

# 2) Trivy CLI per Aquasecurity-Script installieren (immer die neueste)
RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh \
  | sh -s -- -b /usr/local/bin

# 3) Applikations-Code kopieren
COPY ./app /app

# 4) Start-Skript hinzufügen
COPY app/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# 5) Python-Dependencies installieren
RUN pip install --no-cache-dir -r /app/requirements.txt

# 6) Start beider Bots
CMD ["/app/start.sh"]
