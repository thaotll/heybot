import os
import json
import logging
import asyncio
import subprocess
import tempfile
import shutil
import datetime
from pathlib import Path

import aiohttp
from dotenv import load_dotenv
from openai import AsyncOpenAI


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Startinformationen ausgeben
logging.info("=" * 50)
logging.info("Bazinga CVE Bot gestartet")
logging.info(f"Aktuelle Zeit: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
logging.info("=" * 50)

# Konstanten für Pfade
BASE_DIR = Path(__file__).parent
ANALYSIS_DIR = BASE_DIR / "analysis"
ANALYSIS_DIR.mkdir(exist_ok=True)

# Variables from the .env file
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '').strip()
MODEL_HUMOR_PATH1 = os.getenv('MODEL_HUMOR_PATH1')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
CURRENT_COMMIT_ID = os.getenv('CURRENT_COMMIT_ID', 'latest')

# Logging der Umgebungsvariablen
logging.info(f"DISCORD_WEBHOOK_URL ist {'gesetzt' if DISCORD_WEBHOOK_URL else 'NICHT GESETZT'}")
logging.info(f"CURRENT_COMMIT_ID ist {CURRENT_COMMIT_ID}")

# DeepSeek-Konfiguration prüfen
if not MODEL_HUMOR_PATH1:
    raise ValueError("MODEL_HUMOR_PATH1 is missing.")
if not DEEPSEEK_API_KEY:
    raise ValueError("DEEPSEEK_API_KEY is missing.")

client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

SEVERITY_ORDER = {
    "CRITICAL": 0,
    "HIGH": 1,
    "MEDIUM": 2,
    "LOW": 3,
    "UNKNOWN": 4
}

def load_humor_template():
    """Load the Sheldon Cooper-style humor template"""
    try:
        return Path(MODEL_HUMOR_PATH1).read_text(encoding="utf-8").strip()
    except Exception as e:
        logging.error(f"Fehler beim Laden des Humor-Templates: {e}")
        return "You are Sheldon Cooper..."

def load_trivy_logs():
    try:
        path = Path(f"analysis/trivy-{CURRENT_COMMIT_ID}.json")
        if not path.exists():
            logging.warning(f"{path.name} existiert nicht")
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        return [v for r in data.get("Results", []) for v in r.get("Vulnerabilities", [])]
    except Exception as e:
        logging.error(f"Fehler beim Laden der Trivy-Daten: {e}")
        return []

def load_owasp_logs():
    try:
        path = Path(f"analysis/owasp-{CURRENT_COMMIT_ID}.json")
        if not path.exists():
            logging.warning(f"{path.name} existiert nicht")
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        vulns = []
        for dep in data.get("dependencies", []):
            for v in dep.get("vulnerabilities", []):
                v["Package"] = dep.get("fileName", "unknown")
                vulns.append(v)
        return vulns
    except Exception as e:
        logging.error(f"Fehler beim Laden der OWASP-Daten: {e}")
        return []

def sort_vulns(vulns):
    return sorted(vulns, key=lambda x: SEVERITY_ORDER.get(x.get("Severity", "UNKNOWN").upper(), 99))

async def send_prompt_to_deepseek(prompt):
    try:
        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a sarcastic security assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=1.0
        )
        message = response.choices[0].message.content
        if not message or not isinstance(message, str):
            return "DeepSeek returned no valid response. Even Sheldon is confused. 🔍"
        return message if "Bazinga" in message else message + "\nBazinga! ⚛️"
    except Exception as e:
        logging.error(f"DeepSeek-Exception: {e}")
        return "Fehler bei der Kommunikation mit DeepSeek."

async def generate_report(vulns, template):
    if not vulns:
        return "No vulnerabilities found! Your code is as flawless as Sheldon's routine. Bazinga! ⚛️"

    sorted_vulns = sort_vulns(vulns)

    # Sort vulnerabilities by severity before processing
    prompt = f"""
{template}

Analyze these vulnerabilities (sorted by severity) and generate:
1. A Sheldon Cooper joke.
2. A markdown table with columns: Package, Severity, CVE, Fixed Version, How to Fix.
3. Key technical notes for critical/high vulnerabilities.
4. Actionable remediation steps.

Vulnerabilities (first 5 by severity):
{json.dumps(sorted_vulns[:5], indent=2)}

--- Example Format ---
**Joke**: "This SQL injection is as messy as Penny's apartment! Bazinga! 🛋️"

**Vulnerabilities**:
```
| Package  | Severity | CVE              | Fixed Version | How to Fix                          |
|----------|----------|------------------|---------------|-------------------------------------|
| libaom3  | CRITICAL | CVE-2023-6879    | Not specified | Upgrade via Debian security updates |
| libaom3  | HIGH     | CVE-2023-39616   | Will not fix  | Monitor for future patches          |
```

**Key Notes**:
- libaom3: Heap overflow (CRITICAL) and memory read issue (HIGH).

**Action**:
- Patch CRITICAL issues immediately with `apt upgrade`.
- Restrict untrusted inputs for HIGH-severity unfixable issues.
"""

    response = await send_prompt_to_deepseek(prompt)
    if not response or not isinstance(response, str):
        return "DeepSeek returned no valid response. Even Sheldon is confused. 🔍"
    return response if "Bazinga" in response else response + "\nBazinga! ⚛️"

def save_message_to_file(msg):
    try:
        path = Path("bazinga_message.txt")
        path.write_text(msg, encoding="utf-8")
        logging.info("Bazinga message saved.")
        logging.info(f"Bazinga-Nachricht gespeichert unter: {path.absolute()}")
    except Exception as e:
        logging.error(f"Speichern der Bazinga-Nachricht fehlgeschlagen: {e}")

async def send_discord(msg):
    """
    Sendet eine Nachricht an den Discord-Webhook.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(DISCORD_WEBHOOK_URL, json={"content": msg}) as response:
                if response.status != 204:
                    logging.warning(f"Discord returned status: {response.status}")
                else:
                    logging.info("Discord-Nachricht erfolgreich gesendet.")
    except Exception as e:
        logging.error(f"Fehler beim Senden an Discord: {e}")

async def main():
    trivy = load_trivy_logs()
    owasp = load_owasp_logs()
    combined = trivy + owasp

    template = load_humor_template()
    report = await generate_report(combined, template)

    save_message_to_file(report)
    await send_discord(report)
    logging.info("Bazinga report sent.")

if __name__ == "__main__":
    asyncio.run(main())