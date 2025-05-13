import logging
import json
import asyncio
import aiohttp
import os
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Variables from the .env file
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
MODEL_HUMOR_PATH1 = os.getenv('MODEL_HUMOR_PATH1')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
CURRENT_COMMIT_ID = os.getenv('CURRENT_COMMIT_ID', 'latest')

if not DISCORD_WEBHOOK_URL:
    raise ValueError("DISCORD_WEBHOOK_URL is missing in the .env file.")

if not MODEL_HUMOR_PATH1:
    logging.warning("MODEL_HUMOR_PATH1 ist nicht gesetzt. Standard-Humor-Template wird verwendet.")
    # Setze einen Standard-Pfad
    MODEL_HUMOR_PATH1 = "/app/default_humor_template.txt"
    # Erstelle eine Standarddatei, falls sie nicht existiert
    if not os.path.exists(MODEL_HUMOR_PATH1):
        with open(MODEL_HUMOR_PATH1, 'w') as f:
            f.write("You are Sheldon Cooper from Big Bang Theory...")

if not DEEPSEEK_API_KEY:

# Initialize OpenAI client
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# Severity ranking for sorting
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
        logging.error(f"Failed to load humor template: {e}")
        return "You are Sheldon Cooper..."


def load_trivy_logs():
    try:
        path = Path(f"analysis/trivy-{CURRENT_COMMIT_ID}.json")
        data = json.loads(path.read_text(encoding="utf-8"))
        return [v for r in data.get("Results", []) for v in r.get("Vulnerabilities", [])]
    except Exception as e:
        logging.error(f"Failed to load Trivy logs: {e}")
        return []


def load_owasp_logs():
    try:
        path = Path(f"analysis/owasp-{CURRENT_COMMIT_ID}.json")
        data = json.loads(path.read_text(encoding="utf-8"))
        vulns = []
        for dep in data.get("dependencies", []):
            for v in dep.get("vulnerabilities", []):
                v["Package"] = dep.get("fileName", "unknown")
                vulns.append(v)
        return vulns
    except Exception as e:
        logging.error(f"Failed to load OWASP logs: {e}")
        return []


def sort_vulns(vulns):
    return sorted(vulns, key=lambda x: SEVERITY_ORDER.get(x.get("Severity", "UNKNOWN").upper(), 99))


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
    try:
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9
        )
        text = resp.choices[0].message.content
        return text if "Bazinga" in text else text + "\nBazinga! ⚛️"
    except Exception as e:
        logging.error(f"DeepSeek error: {e}")
        return "Couldn't generate report. Even Sheldon couldn't fix this. 🔥"


def save_message_to_file(msg):
    try:
        Path(__file__).parent.joinpath("bazinga_message.txt").write_text(msg, encoding="utf-8")
        logging.info("Bazinga message saved.")
    except Exception as e:
        logging.error(f"Failed to save Bazinga message: {e}")


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
                    logging.info("Message sent to Discord successfully")
    except Exception as e:
        logging.error(f"Error sending Discord message: {e}")


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