import logging
import json
import asyncio
import aiohttp
import os
import subprocess
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Variables from the .env file
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
MODEL_HUMOR_PATH = os.getenv('MODEL_HUMOR_PATH')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
CURRENT_COMMIT_ID = os.getenv('CURRENT_COMMIT_ID', 'latest')

if not DISCORD_WEBHOOK_URL:
    raise ValueError("DISCORD_WEBHOOK_URL is missing in the .env file.")
if not MODEL_HUMOR_PATH:
    raise ValueError("MODEL_HUMOR_PATH is missing in the .env file.")
if not DEEPSEEK_API_KEY:
    raise ValueError("DEEPSEEK_API_KEY is missing in the .env file.")


# Initialize DeepSeek client
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")


def get_last_commit_id():
    path = Path(__file__).parent / "latest_commit.txt"
    return path.read_text().strip() if path.exists() else None


def save_commit_id(cid):
    (Path(__file__).parent / "latest_commit.txt").write_text(cid)
    logging.info(f"Saved commit {cid}")


def run_trivy_scan():
    scan_target = "/app" if Path("/app").exists() else Path(__file__).parent.resolve()
    Path("analysis").mkdir(exist_ok=True)
    subprocess.run([
        "trivy", "fs", str(scan_target), "-f", "json",
        "-o", f"analysis/trivy-{CURRENT_COMMIT_ID}.json"
    ], check=True)
    logging.info("Trivy scan completed.")


def run_owasp_scan():
    scan_path = "/app" if Path("/app").exists() else Path(__file__).parent.resolve()
    Path("analysis").mkdir(exist_ok=True)
    subprocess.run([
        "dependency-check", "--project", "heybot",
        "--scan", str(scan_path), "--format", "JSON",
        "--out", str(Path("analysis") / f"owasp-{CURRENT_COMMIT_ID}.json")
    ], check=True, env={**os.environ})
    logging.info("OWASP Dependency-Check completed.")


def load_trivy_logs():
    try:
        data = json.loads(Path(f"analysis/trivy-{CURRENT_COMMIT_ID}.json").read_text())
        vulns = [v for r in data.get("Results", []) for v in r.get("Vulnerabilities", [])]
        return vulns
    except Exception as e:
        logging.error(f"Failed to load Trivy logs: {e}")
        return []


def load_owasp_logs():
    try:
        data = json.loads(Path(f"analysis/owasp-{CURRENT_COMMIT_ID}.json").read_text())
        return data.get("dependencies", [])
    except Exception as e:
        logging.error(f"Failed to load OWASP logs: {e}")
        return []


def summarize_vulns(vulns):
    cnt = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for v in vulns:
        sev = v.get("Severity", "").lower()
        if sev in cnt:
            cnt[sev] += 1
    return cnt


def save_analysis_json(trivy, owasp):
    trivy_summary = summarize_vulns(trivy)
    owasp_total = sum(len(dep.get("vulnerabilities", [])) for dep in owasp)

    result = {
        "securityScans": [
            {
                "tool": "trivy",
                "status": "success",
                "vulnerabilities": trivy_summary,
                "details": "Ergebnisse des Trivy-Dateisystemscans."
            },
            {
                "tool": "owasp",
                "status": "success",
                "vulnerabilities": {
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": owasp_total
                },
                "details": "Ergebnisse des OWASP Dependency-Check."
            }
        ]
    }
    Path("analysis").mkdir(exist_ok=True)
    out = Path("analysis") / f"{CURRENT_COMMIT_ID}.json"
    out.write_text(json.dumps(result, indent=2))
    logging.info(f"Saved combined analysis JSON to {out}")

# Build funny + sarcastic prompt with logs
def build_prompt_with_logs(trivy_logs, owasp_logs):
    try:
        humor_base = Path(MODEL_HUMOR_PATH).read_text().strip()
        trivy_text = "\n\n".join([
            f"🔥 Trivy {i + 1}: {log.get('Title', 'No Title')}\nSeverity: {log.get('Severity', 'N/A')} | Package: {log.get('PkgName', 'N/A')}"
            for i, log in enumerate(trivy_logs[:5])
        ]) or "✅ Trivy found no vulnerabilities."

        owasp_text = "\n\n".join([
            f"📦 OWASP {i + 1}: {dep.get('fileName', 'Unknown')} — " + \
            ", ".join([v.get("name", "Unknown CVE") for v in dep.get("vulnerabilities", [])])
            for i, dep in enumerate(owasp_logs[:5]) if dep.get("vulnerabilities")
        ]) or "✅ OWASP found no vulnerable dependencies."

        return f"{humor_base}\n\n== Trivy Findings ==\n\n{trivy_text}\n\n== OWASP Findings ==\n\n{owasp_text}"
    except Exception as e:
        logging.error(f"Error building prompt: {e}")
        return "Fehler beim Erstellen der Sicherheitszusammenfassung."


def save_message_to_file(message: str):
    try:
        path = Path(__file__).parent / "main_message.txt"
        path.write_text(message, encoding="utf-8")
        logging.info(f"DeepSeek message saved to {path}")
    except Exception as e:
        logging.error(f"Error saving message: {e}")


async def send_prompt_to_deepseek(prompt):
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a sarcastic security assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=1.0
    )
    return resp.choices[0].message.content

# Clean output for Discord
def clean(msg, mx=1900):
    m = msg.replace('\u0000', '')
    return (m[:mx] + "\n...") if len(m) > mx else m


async def send_discord(msg):
    async with aiohttp.ClientSession() as session:
        await session.post(DISCORD_WEBHOOK_URL, json={"content": msg})

# Main entry
async def main():
    last = get_last_commit_id()
    if last == CURRENT_COMMIT_ID:
        logging.info("Commit already processed.")
        return

    Path("analysis").mkdir(exist_ok=True)
    run_owasp_scan()
    run_trivy_scan()

    trivy = load_trivy_logs()
    owasp = load_owasp_logs()
    save_analysis_json(trivy, owasp)

    prompt = build_prompt_with_logs(trivy, owasp)
    ds_msg = await send_prompt_to_deepseek(prompt)
    ds_msg = clean(ds_msg)

    save_message_to_file(ds_msg)
    await send_discord(ds_msg)
    save_commit_id(CURRENT_COMMIT_ID)


if __name__ == "__main__":
    asyncio.run(main())