import logging
import json
import asyncio
import aiohttp
import os
import subprocess
from openai import OpenAI
from pathlib import Path

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

# Initialize DeepSeek client.
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")


def get_last_commit_id():
    commit_file_path = Path(__file__).parent / "latest_commit.txt"

    # Überprüfe, ob die Datei existiert und lese den Inhalt (Commit-ID)
    if commit_file_path.exists():
        with open(commit_file_path, "r", encoding="utf-8") as file:
            return file.read().strip()
    return None


def save_commit_id(commit_id):
    commit_file_path = Path(__file__).parent / "latest_commit.txt"

    try:
        with open(commit_file_path, "w", encoding="utf-8") as file:
            file.write(commit_id)
        logging.info(f"Commit-ID {commit_id} gespeichert unter: {commit_file_path}")
    except Exception as e:
        logging.error(f"Fehler beim Speichern der Commit-ID: {e}")

# Save message for frontend API access
def save_message_to_file(message: str):
    try:
        # Absoluten Pfad zur Datei berechnen – basierend auf dem Speicherort dieser Python-Datei
        base_path = Path(__file__).parent
        file_path = base_path / "latest_deepseek_message.txt"

        with open(file_path, "w", encoding="utf-8") as file:
            file.write(message)

        logging.info(f"DeepSeek-Nachricht gespeichert unter: {file_path}")
    except Exception as e:
        logging.error(f"Fehler beim Speichern: {e}")


def run_trivy_scan():
    try:
        result = subprocess.run(
            ["trivy", "fs", ".", "-f", "json", "-o", "trivy_output.json"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        logging.info("Trivy-Scan abgeschlossen.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Trivy-Scan fehlgeschlagen: {e.stderr.decode()}")

# Load Trivy logs from file
def load_trivy_logs(log_path="trivy_output.json"):
    try:
        with open(log_path, "r", encoding="utf-8") as file:
            raw_data = json.load(file)
            logging.debug(f"Raw Trivy log content: {json.dumps(raw_data, indent=2)}")

            vulnerabilities = []
            if isinstance(raw_data, dict) and "Results" in raw_data:
                for result in raw_data["Results"]:
                    vulns = result.get("Vulnerabilities", [])
                    if isinstance(vulns, list):
                        vulnerabilities.extend(vulns)
            elif isinstance(raw_data, dict) and "vulnerabilities" in raw_data:
                vulnerabilities = raw_data["vulnerabilities"]

            if not isinstance(vulnerabilities, list):
                logging.error("Log format error: Logs should be a list of dictionaries.")
                return []

            logging.info(f"Extracted {len(vulnerabilities)} vulnerability entries.")
            return vulnerabilities
    except Exception as e:
        logging.error(f"Error loading logs: {e}")
        return []


def summarize_vulnerabilities(vulns):
    summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for v in vulns:
        severity = v.get("Severity", "").lower()
        if severity in summary:
            summary[severity] += 1
    return summary


def save_analysis_json(vulns, message, commit_id="latest"):
    try:
        summary = summarize_vulnerabilities(vulns)

        result = {
            "securityScans": [
                {
                    "tool": "trivy",
                    "status": "success",
                    "vulnerabilities": summary,
                    "details": message,
                }
            ]
        }

        base_path = Path(__file__).parent / "analysis"
        base_path.mkdir(parents=True, exist_ok=True)
        out_path = base_path / f"{commit_id}.json"

        with open(out_path, "w", encoding="utf-8") as file:
            json.dump(result, file, indent=2)

        logging.info(f"Analyse-Datei gespeichert unter: {out_path}")
    except Exception as e:
        logging.error(f"Fehler beim Speichern der Analyse-Datei: {e}")

# Build funny + sarcastic prompt with logs
def build_prompt_with_logs(logs):
    try:
        # Read the humor base from file (contains the SYSTEM prompt)
        with open(MODEL_HUMOR_PATH, "r", encoding="utf-8") as file:
            humor_base = file.read().strip()

        # Format each vulnerability log entry
        logs_as_text = "\n\n".join([
            f"🔥 Vulnerability {i+1}: {log.get('Title', 'No Title')}\n"
            f"Severity: {log.get('Severity', 'N/A')} | CVSS: {log.get('CVSS', {}).get('bitnami', {}).get('V3Score', 'N/A')}\n"
            f"CWE: {', '.join(log.get('CweIDs', [])) if log.get('CweIDs') else 'None'}\n"
            f"Fix it (maybe?): {log.get('References', [])[0] if log.get('References') else 'No clue, good luck'}"
            for i, log in enumerate(logs)
        ])

        # Combine everything into the final prompt
        return (
            f"{humor_base}\n\n"  # This contains your SYSTEM prompt
            f"Here are the vulnerabilities that need your sarcastic expertise:\n\n"
            f"{logs_as_text}\n\n"
            f"Now roast each one with:\n"
            f"- Gordon Ramsay-level intensity\n"
            f"- Stand-up comedian timing\n"
            f"- DevOps intern frustration\n"
            f"Bonus points for Sheldon Cooper references!"
        )
    except Exception as e:
        logging.error(f"Error building prompt with humor path: {e}")
        return ""

# Send prompt to DeepSeek
async def send_prompt_to_deepseek(prompt, model="deepseek-chat", temperature=1.0):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a sarcastic security assistant"},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            stream=False
        )
        logging.info("Prompt sent to DeepSeek successfully.")
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"DeepSeek generate error: {e}")
        return "Oops, I tried to be funny, but I crashed harder than your CI pipeline."

# Clean output for Discord
def clean_discord_message(text, max_length=1900):
    try:
        cleaned = text.encode("utf-8", "ignore").decode("utf-8").replace('\u0000', '')
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length] + "\n... (truncated)"
        return cleaned
    except Exception as e:
        logging.error(f"Error cleaning message: {e}")
        return ": Message could not be processed."

# Send to Discord
async def send_discord_message_async(message):
    try:
        payload = {"content": message}
        headers = {"Content-Type": "application/json"}

        logging.debug(f"Discord Payload: {json.dumps(payload)}")

        async with aiohttp.ClientSession() as session:
            async with session.post(DISCORD_WEBHOOK_URL, json=payload, headers=headers) as response:
                if response.status == 204:
                    logging.debug("Message sent to Discord.")
                else:
                    logging.error(f"Discord responded with status: {response.status}")
    except Exception as e:
        logging.error(f"Error sending to Discord: {e}")

# Main entry
async def main():
    try:
        # Gespeicherte Commit-ID holen
        last_commit_id = get_last_commit_id()

        # Wenn es keine gespeicherte Commit-ID gibt oder der Commit sich geändert hat, diesen Prozess ausführen
        if last_commit_id != CURRENT_COMMIT_ID:
            logging.info(
                f"Commit hat sich geändert (letztes Commit: {last_commit_id}, aktuelles Commit: {CURRENT_COMMIT_ID}). Führe den Scan aus.")

            run_trivy_scan()
            logs = load_trivy_logs()
            if not logs:
                logging.info("Keine Schwachstellen gefunden – speichere trotzdem Analyse-Datei.")
                logs = []

            prompt = build_prompt_with_logs(logs)
            if not prompt:
                logging.error("Failed to build prompt.")
                return

            response = await send_prompt_to_deepseek(prompt, temperature=1.1)
            final_message = clean_discord_message(response)

            save_message_to_file(final_message)
            await send_discord_message_async(final_message)

            save_analysis_json(logs, final_message, commit_id=CURRENT_COMMIT_ID)

            # Aktuelle Commit-ID nach erfolgreichem Scan speichern
            save_commit_id(CURRENT_COMMIT_ID)
        else:
            logging.info(f"Commit {CURRENT_COMMIT_ID} bereits verarbeitet. Keine Aktion erforderlich.")

    except Exception as e:
        logging.error(f"Error in main process: {e}")

if __name__ == "__main__":
    asyncio.run(main())