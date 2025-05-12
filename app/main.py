import logging
import json
import asyncio
import aiohttp
import os
import subprocess
import tempfile
import shutil
from dotenv import load_dotenv
import openai
from pathlib import Path

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Konstanten für Pfade
BASE_DIR = Path(__file__).parent
ANALYSIS_DIR = BASE_DIR / "analysis"
ANALYSIS_DIR.mkdir(exist_ok=True)

# Environment Variables
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
openai.api_key = DEEPSEEK_API_KEY
openai.api_base = "https://api.deepseek.com/v1"


def get_last_commit_id():
    """Liest die letzte Commit-ID aus der Datei."""
    path = Path(__file__).parent / "latest_commit.txt"
    return path.read_text().strip() if path.exists() else None


def save_commit_id(cid):
    """Speichert die aktuelle Commit-ID in einer Datei."""
    (Path(__file__).parent / "latest_commit.txt").write_text(cid)
    logging.info(f"Saved commit {cid}")


def run_trivy_scan(temp_dir, commit_id):
    """
    Führt den Trivy-Scan in einem temporären Verzeichnis durch.
    """
    output_file = ANALYSIS_DIR / f"trivy-{commit_id}.json"
    
    try:
        logging.info(f"Starting Trivy scan for commit {commit_id}")
        subprocess.run([
            "trivy", "fs",
            "--format", "json",
            "--severity", "CRITICAL,HIGH,MEDIUM,LOW",
            "--no-progress",
            "--scanners", "vuln,secret,config",  # Aktiviere alle Scanner
            "--output", str(output_file),
            str(temp_dir)
        ], check=True, capture_output=True, text=True)
        logging.info(f"Trivy scan completed for commit {commit_id}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Trivy scan failed: {str(e)}")
        logging.error(f"Stdout: {e.stdout}")
        logging.error(f"Stderr: {e.stderr}")
        # Erstellt eine leere Ergebnisdatei
        output_file.write_text(json.dumps({"Results": []}))
    
    return output_file


def run_owasp_scan(temp_dir, commit_id):
    """
    Führt den OWASP-Scan in einem temporären Verzeichnis durch.
    """
    output_file = ANALYSIS_DIR / f"owasp-{commit_id}.json"
    
    try:
        # Erstellt ein Verzeichnis für die OWASP-Datenbank
        data_dir = ANALYSIS_DIR / "owasp-data"
        data_dir.mkdir(exist_ok=True)
        
        logging.info(f"Starting OWASP scan for commit {commit_id}")
        subprocess.run([
            "dependency-check",
            "--project", "heybot",
            "--scan", str(temp_dir),
            "--format", "JSON",
            "--out", str(output_file),
            "--failOnCVSS", "11",  # Nie fehlschlagen (Großbuchstaben CVSS)
            "--nodeAuditSkipDevDependencies", "false",  # Auch dev dependencies scannen
            "--data", str(data_dir)  # Persistente Datenbank
        ], check=True, capture_output=True, text=True, env={**os.environ})
        logging.info(f"OWASP scan completed for commit {commit_id}")
    except subprocess.CalledProcessError as e:
        logging.error(f"OWASP scan failed: {str(e)}")
        logging.error(f"Stdout: {e.stdout}")
        logging.error(f"Stderr: {e.stderr}")
        # Erstellt eine leere Ergebnisdatei
        output_file.write_text(json.dumps({"dependencies": []}))
    
    return output_file


def load_scan_results(commit_id):
    """
    Lädt die Scan-Ergebnisse für einen bestimmten Commit.
    """
    try:
        trivy_file = ANALYSIS_DIR / f"trivy-{commit_id}.json"
        owasp_file = ANALYSIS_DIR / f"owasp-{commit_id}.json"
        
        # Standardwerte für den Fall, dass die Dateien nicht existieren
        trivy_data = {"Results": []}
        owasp_data = {"dependencies": []}
        
        if trivy_file.exists():
            trivy_data = json.loads(trivy_file.read_text())
        else:
            logging.warning(f"Trivy file for commit {commit_id} not found")
            
        if owasp_file.exists():
            owasp_data = json.loads(owasp_file.read_text())
        else:
            logging.warning(f"OWASP file for commit {commit_id} not found")
        
        return trivy_data, owasp_data
    except Exception as e:
        logging.error(f"Failed to load scan results for commit {commit_id}: {e}")
        return {"Results": []}, {"dependencies": []}


def summarize_trivy_results(results):
    """
    Vollständige Zusammenfassung aller Trivy-Ergebnisse, einschließlich Vulnerabilities und Misconfigurations.
    """
    summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    
    for result in results:
        # Traditionelle Schwachstellen
        if "Vulnerabilities" in result:
            for vuln in result.get("Vulnerabilities", []):
                sev = vuln.get("Severity", "").lower()
                if sev in summary:
                    summary[sev] += 1
        
        # Fehlkonfigurationen einbeziehen
        if "Misconfigurations" in result:
            for misc in result.get("Misconfigurations", []):
                sev = misc.get("Severity", "").lower()
                if sev in summary:
                    summary[sev] += 1
        
        # Geheimnisse einbeziehen
        if "Secrets" in result:
            for secret in result.get("Secrets", []):
                # Geheimnisse werden oft als "CRITICAL" oder "HIGH" eingestuft
                summary["high"] += 1
    
    return summary


def summarize_owasp_results(dependencies):
    """
    Zusammenfassung der OWASP-Ergebnisse.
    """
    summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    
    for dep in dependencies:
        for vuln in dep.get("vulnerabilities", []):
            severity = vuln.get("severity", "low").lower()
            if severity in summary:
                summary[severity] += 1
    
    return summary


def save_analysis_json(trivy_data, owasp_data, commit_id):
    """
    Speichert die Analyseergebnisse im JSON-Format.
    """
    # Vollständige Trivy-Daten analysieren
    trivy_summary = summarize_trivy_results(trivy_data.get("Results", []))
    
    # OWASP-Daten analysieren
    owasp_summary = summarize_owasp_results(owasp_data.get("dependencies", []))

    # Status basierend auf Schweregrad bestimmen
    trivy_status = "success"
    if trivy_summary["critical"] > 0 or trivy_summary["high"] > 0:
        trivy_status = "error"
        trivy_details = "Kritische oder schwerwiegende Probleme gefunden (inkl. Fehlkonfigurationen)."
    elif trivy_summary["medium"] > 0:
        trivy_status = "warning"
        trivy_details = "Mittelschwere Probleme gefunden (inkl. Fehlkonfigurationen)."
    else:
        trivy_details = "Ergebnisse des Trivy-Dateisystemscans."
    
    owasp_status = "success"
    if owasp_summary["critical"] > 0 or owasp_summary["high"] > 0:
        owasp_status = "error"
        owasp_details = "Kritische oder schwerwiegende Abhängigkeitsprobleme gefunden."
    elif owasp_summary["medium"] > 0:
        owasp_status = "warning"
        owasp_details = "Mittelschwere Abhängigkeitsprobleme gefunden."
    else:
        owasp_details = "Ergebnisse des OWASP Dependency-Check."

    result = {
        "securityScans": [
            {
                "tool": "trivy",
                "status": trivy_status,
                "vulnerabilities": trivy_summary,
                "details": trivy_details
            },
            {
                "tool": "owasp",
                "status": owasp_status,
                "vulnerabilities": owasp_summary,
                "details": owasp_details
            }
        ]
    }
    
    # Speichert die Ergebnisse
    output_file = ANALYSIS_DIR / f"{commit_id}.json"
    output_file.write_text(json.dumps(result, indent=2))
    logging.info(f"Analysis results saved to {output_file}")
    
    # Wenn es der aktuelle Commit ist, speichert auch als latest
    if commit_id == CURRENT_COMMIT_ID:
        latest_file = ANALYSIS_DIR / "latest.json"
        latest_file.write_text(json.dumps(result, indent=2))
        logging.info("Analysis results saved as latest")
    
    return result


def extract_vulnerabilities_for_prompt(trivy_data, owasp_data, max_items=5):
    """
    Extrahiert die wichtigsten Vulnerabilitäten für den Prompt.
    """
    trivy_logs = []
    
    # Vulnerabilities extrahieren
    for result in trivy_data.get("Results", []):
        for vuln in result.get("Vulnerabilities", []):
            trivy_logs.append({
                "Title": vuln.get("Title", "No Title"),
                "Severity": vuln.get("Severity", "N/A"),
                "PkgName": vuln.get("PkgName", "N/A"),
                "Type": "Vulnerability"
            })
        
        # Misconfigurations extrahieren
        for misc in result.get("Misconfigurations", []):
            trivy_logs.append({
                "Title": misc.get("Title", "No Title"),
                "Severity": misc.get("Severity", "N/A"),
                "PkgName": misc.get("ID", "N/A"),
                "Type": "Misconfiguration"
            })
    
    # Nach Schweregrad sortieren (kritisch zuerst)
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "UNKNOWN": 4}
    trivy_logs.sort(key=lambda x: severity_order.get(x.get("Severity", "UNKNOWN"), 5))
    
    # OWASP-Vulnerabilities extrahieren
    owasp_logs = []
    for dep in owasp_data.get("dependencies", []):
        if dep.get("vulnerabilities"):
            owasp_logs.append(dep)
    
    return trivy_logs[:max_items], owasp_logs[:max_items]


def build_prompt_with_logs(trivy_data, owasp_data):
    """
    Erstellt einen humorvollen Prompt mit den Sicherheitsergebnissen.
    """
    try:
        humor_base = Path(MODEL_HUMOR_PATH).read_text().strip()
        
        # Extrahiert die relevantesten Vulnerabilitäten
        trivy_logs, owasp_logs = extract_vulnerabilities_for_prompt(trivy_data, owasp_data)
        
        trivy_text = "\n\n".join([
            f"🔥 Trivy {i + 1}: {log.get('Title', 'No Title')}\n"
            f"Severity: {log.get('Severity', 'N/A')} | Type: {log.get('Type', 'N/A')} | ID: {log.get('PkgName', 'N/A')}"
            for i, log in enumerate(trivy_logs)
        ]) or "✅ Trivy found no vulnerabilities."

        owasp_text = "\n\n".join([
            f"📦 OWASP {i + 1}: {dep.get('fileName', 'Unknown')} — " + \
            ", ".join([v.get("name", "Unknown CVE") for v in dep.get("vulnerabilities", [])])
            for i, dep in enumerate(owasp_logs) if dep.get("vulnerabilities")
        ]) or "✅ OWASP found no vulnerable dependencies."

        return f"{humor_base}\n\n== Trivy Findings ==\n\n{trivy_text}\n\n== OWASP Findings ==\n\n{owasp_text}"
    except Exception as e:
        logging.error(f"Error building prompt: {e}")
        return "Fehler beim Erstellen der Sicherheitszusammenfassung."


def save_message_to_file(message: str):
    """
    Speichert die generierte Nachricht in einer Datei.
    """
    try:
        path = Path(__file__).parent / "main_message.txt"
        path.write_text(message, encoding="utf-8")
        logging.info(f"DeepSeek message saved to {path}")
        return path
    except Exception as e:
        logging.error(f"Error saving message: {e}")
        return None


async def send_prompt_to_deepseek(prompt):
    """
    Sendet den Prompt an die DeepSeek-API und gibt die generierte Antwort zurück.
    """
    try:
        resp = openai.ChatCompletion.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a sarcastic security assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=1.0
        )
        return resp.choices[0].message.content
    except Exception as e:
        logging.error(f"Error calling DeepSeek API: {e}")
        return "Fehler bei der API-Anfrage an DeepSeek."


# Clean output for Discord
def clean(msg, mx=1900):
    """
    Bereinigt die Nachricht für Discord und kürzt sie bei Bedarf.
    """
    m = msg.replace('\u0000', '')
    return (m[:mx] + "\n...") if len(m) > mx else m


async def send_discord(msg):
    """
    Sendet eine Nachricht an den Discord-Webhook.
    """
    try:
        async with aiohttp.ClientSession() as session:
            response = await session.post(DISCORD_WEBHOOK_URL, json={"content": clean(msg)})
            if response.status != 204:
                response_text = await response.text()
                logging.error(f"Discord webhook failed with status {response.status}: {response_text}")
            else:
                logging.info("Message sent to Discord successfully")
    except Exception as e:
        logging.error(f"Error sending Discord message: {e}")


async def analyze_specific_commit(commit_id):
    """
    Analysiert einen spezifischen Commit in einem temporären Verzeichnis.
    """
    # Erstellt ein temporäres Verzeichnis
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        try:
            logging.info(f"Starting analysis for commit {commit_id}")
            
            # Clone das Repository in das temporäre Verzeichnis
            subprocess.run([
                "git", "clone", "--depth", "1", str(BASE_DIR.parent), str(temp_path)
            ], check=True, capture_output=True, text=True)
            
            # Wechsel zum gewünschten Commit
            subprocess.run([
                "git", "-C", str(temp_path), "checkout", commit_id
            ], check=True, capture_output=True, text=True)
            
            # Installiere Dependencies
            if (temp_path / "package.json").exists():
                subprocess.run([
                    "npm", "install",
                    "--prefix", str(temp_path),
                    "--ignore-scripts",  # Keine Build-Skripte ausführen
                    "--omit=dev",  # Keine Dev-Dependencies (inkl. @types)
                ], check=True, capture_output=True, text=True)
            
            if (temp_path / "requirements.txt").exists():
                try:
                    subprocess.run([
                        "pip", "install",
                        "-r", str(temp_path / "requirements.txt"),
                        "--target", str(temp_path / "pip_modules")
                    ], check=True, capture_output=True, text=True)
                except subprocess.CalledProcessError as e:
                    logging.warning(f"Pip install failed, continuing analysis: {e}")
            
            # Führt die Scans durch
            run_trivy_scan(temp_path, commit_id)
            run_owasp_scan(temp_path, commit_id)
            
            # Ladet und speichert die Ergebnisse
            trivy_data, owasp_data = load_scan_results(commit_id)
            result = save_analysis_json(trivy_data, owasp_data, commit_id)
            
            return result
            
        except subprocess.CalledProcessError as e:
            logging.error(f"Command failed: {str(e)}")
            logging.error(f"Stdout: {e.stdout}")
            logging.error(f"Stderr: {e.stderr}")
            raise Exception(f"Command failed: {str(e)}")
        except Exception as e:
            logging.error(f"Analysis failed: {str(e)}")
            raise


async def get_commit_analysis(commit_id):
    """
    Holt die Analyseergebnisse für einen Commit.
    Führt die Analyse durch, falls noch nicht vorhanden.
    """
    analysis_file = ANALYSIS_DIR / f"{commit_id}.json"
    
    if not analysis_file.exists():
        logging.info(f"No existing analysis for commit {commit_id}, running new analysis")
        return await analyze_specific_commit(commit_id)
    
    try:
        return json.loads(analysis_file.read_text())
    except Exception as e:
        logging.error(f"Failed to load analysis for commit {commit_id}: {e}")
        return None


# Main entry
async def main():
    try:
        logging.info("Starting security analysis")
        
        # Erstellt ein temporäres Verzeichnis für die Analyse
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Führt Analyse für aktuellen Commit durch
            trivy_file = run_trivy_scan(temp_path, CURRENT_COMMIT_ID)
            owasp_file = run_owasp_scan(temp_path, CURRENT_COMMIT_ID)
            
            # Ladet die Scan-Ergebnisse
            trivy_data, owasp_data = load_scan_results(CURRENT_COMMIT_ID)
            
            # Speichert Ergebnisse
            save_analysis_json(trivy_data, owasp_data, CURRENT_COMMIT_ID)

            # Erstellt und sendet Nachricht
            prompt = build_prompt_with_logs(trivy_data, owasp_data)
            message = await send_prompt_to_deepseek(prompt)
            save_message_to_file(message)
            
            if DISCORD_WEBHOOK_URL:
                await send_discord(message)
                
        logging.info("Security analysis completed successfully")
                
    except Exception as e:
        logging.error(f"Fehler in main(): {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())