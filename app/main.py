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

# Zeige Startinformationen
logging.info("=" * 50)
logging.info("HeyBot Security Scanner gestartet")
logging.info(f"Aktuelle Zeit: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
if os.path.exists('.git'):
    try:
        git_branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], text=True).strip()
        git_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
        logging.info(f"Git Branch: {git_branch}")
        logging.info(f"Git Commit: {git_commit}")
    except Exception as e:
        logging.warning(f"Konnte Git-Informationen nicht abrufen: {e}")
logging.info("=" * 50)

# Konstanten für Pfade
BASE_DIR = Path(__file__).parent
ANALYSIS_DIR = BASE_DIR / "analysis"
ANALYSIS_DIR.mkdir(exist_ok=True)

# Environment Variables
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '').strip()
MODEL_HUMOR_PATH = os.getenv('MODEL_HUMOR_PATH')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
CURRENT_COMMIT_ID = os.getenv('CURRENT_COMMIT_ID', 'latest')

# Debug-Ausgabe der Umgebungsvariablen
logging.info(f"Umgebungsvariablen:")
logging.info(f"DISCORD_WEBHOOK_URL ist {'gesetzt' if DISCORD_WEBHOOK_URL else 'NICHT GESETZT'}")
logging.info(f"CURRENT_COMMIT_ID ist {CURRENT_COMMIT_ID}")

# DeepSeek-Konfiguration prüfen
if not MODEL_HUMOR_PATH:
    raise ValueError("MODEL_HUMOR_PATH is missing.")
if not DEEPSEEK_API_KEY:
    raise ValueError("DEEPSEEK_API_KEY is missing.")

client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

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
        logging.info(f"Scanning directory: {temp_dir}")
        logging.info(f"Output file: {output_file}")
        
        # Trivy-Kommando vorbereiten
        trivy_cmd = [
            "trivy", "fs",
            "--format", "json",
            "--severity", "CRITICAL,HIGH,MEDIUM,LOW",
            "--no-progress",
            "--scanners", "vuln,secret,config",  # Aktiviere alle Scanner
            "--output", str(output_file),
            str(temp_dir)
        ]
        
        logging.info(f"Running Trivy command: {' '.join(trivy_cmd)}")
        
        # Live-Logging für Trivy-Ausgabe
        process = subprocess.Popen(
            trivy_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        # Lese und logge Trivy-Ausgabe in Echtzeit
        for line in process.stdout:
            line = line.strip()
            if "error" in line.lower() or "fatal" in line.lower():
                logging.error(f"Trivy: {line}")
            elif "warn" in line.lower():
                logging.warning(f"Trivy: {line}")
            else:
                logging.info(f"Trivy: {line}")
        
        # Warte auf Prozessende
        return_code = process.wait()
        if return_code != 0:
            logging.error(f"Trivy scan failed with return code {return_code}")
        else:
            logging.info(f"Trivy scan completed for commit {commit_id}")
            
            # Prüfe, ob die Ausgabedatei existiert und nicht leer ist
            if output_file.exists():
                file_size = output_file.stat().st_size
                logging.info(f"Trivy output file size: {file_size} bytes")
                if file_size == 0:
                    logging.warning("Trivy output file is empty")
            else:
                logging.error("Trivy output file was not created")
        
    except subprocess.CalledProcessError as e:
        logging.error(f"Trivy scan failed: {str(e)}")
        logging.error(f"Stdout: {e.stdout}")
        logging.error(f"Stderr: {e.stderr}")
        # Erstellt eine leere Ergebnisdatei
        output_file.write_text(json.dumps({"Results": []}))
    except Exception as e:
        logging.error(f"Unexpected error during Trivy scan: {str(e)}")
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
        logging.info(f"OWASP database directory: {data_dir}")
        logging.info(f"Scanning directory: {temp_dir}")
        
        # OWASP-Kommando vorbereiten
        owasp_cmd = [
            "dependency-check",
            "--project", "heybot",
            "--scan", str(temp_dir),
            "--format", "JSON",
            "--out", str(output_file),
            "--failOnCVSS", "11",  # Nie fehlschlagen (Großbuchstaben CVSS)
            "--nodeAuditSkipDevDependencies", "false",  # Auch dev dependencies scannen
            "--data", str(data_dir),  # Persistente Datenbank
            "--log", "info"  # Mehr Logging-Informationen
        ]
        
        logging.info(f"Running OWASP command: {' '.join(owasp_cmd)}")
        
        # Live-Logging für OWASP-Ausgabe
        process = subprocess.Popen(
            owasp_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env={**os.environ}
        )
        
        # Lese und logge OWASP-Ausgabe in Echtzeit
        for line in process.stdout:
            line = line.strip()
            if "ERROR" in line or "FATAL" in line:
                logging.error(f"OWASP: {line}")
            elif "WARN" in line:
                logging.warning(f"OWASP: {line}")
            elif "INFO" in line and ("Progress" in line or "Download" in line or "Processing" in line or "Checking" in line):
                logging.info(f"OWASP Progress: {line}")
        
        # Warte auf Prozessende
        return_code = process.wait()
        if return_code != 0:
            logging.error(f"OWASP scan failed with return code {return_code}")
        else:
            logging.info(f"OWASP scan completed for commit {commit_id}")

            # Prüfen, ob die Zieldatei existiert. Falls nicht, alternative Standardnamen versuchen,
            # wie sie von dependency-check häufig verwendet werden (z. B. dependency-check.json oder
            # dependency-check-[commit_id].json). Falls gefunden, wird die Datei umbenannt.

            alternative_filename_pattern = f"dependency-check-{commit_id}.json"
            alternative_file_path = ANALYSIS_DIR / alternative_filename_pattern
            default_dc_json = ANALYSIS_DIR / "dependency-check.json" # Fallback, falls kein Commit-ID im Namen

            if not output_file.exists():
                if alternative_file_path.exists():
                    logging.info(f"Renaming {alternative_file_path} to {output_file}")
                    shutil.move(str(alternative_file_path), str(output_file))
                elif default_dc_json.exists():
                    logging.info(f"Renaming {default_dc_json} to {output_file}")
                    shutil.move(str(default_dc_json), str(output_file))
                else:
                    logging.warning(f"Expected OWASP output file {output_file} not found, and no known alternatives detected.")
            
    except subprocess.CalledProcessError as e:
        logging.error(f"OWASP scan failed: {str(e)}")
        logging.error(f"Stdout: {e.stdout}")
        logging.error(f"Stderr: {e.stderr}")
        # Erstellt eine leere Ergebnisdatei
        output_file.write_text(json.dumps({"dependencies": []}))
    except Exception as e:
        logging.error(f"Unexpected error during OWASP scan: {str(e)}")
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


def extract_vulnerabilities_for_prompt(trivy_data, owasp_data, max_items=10):
    """
    Extrahiert detaillierte Informationen zu Schwachstellen für den Prompt.
    Erweitert, um mehr Informationen für einen strukturierten Bericht zu liefern.
    """
    # Severities in der richtigen Reihenfolge für Sortierung
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "UNKNOWN": 4}
    
    # Trivy Vulnerabilities
    trivy_vulns = []
    for result in trivy_data.get("Results", []):
        target = result.get("Target", "")
        target_type = result.get("Type", "")
        
        # Vulnerabilities
        for vuln in result.get("Vulnerabilities", []):
            trivy_vulns.append({
                "Package": vuln.get("PkgName", "N/A"),
                "Version": vuln.get("InstalledVersion", "N/A"),
                "FixedVersion": vuln.get("FixedVersion", "Nicht verfügbar"),
                "Severity": vuln.get("Severity", "UNKNOWN"),
                "Title": vuln.get("Title", "N/A"),
                "CVE": vuln.get("VulnerabilityID", "N/A"),
                "Description": vuln.get("Description", ""),
                "Target": target,
                "Type": "Vulnerability"
            })
        
        # Misconfigurations extrahieren
        for misc in result.get("Misconfigurations", []):
            trivy_vulns.append({
                "Package": target,
                "Version": "N/A",
                "FixedVersion": misc.get("Resolution", "Siehe Beschreibung"),
                "Severity": misc.get("Severity", "UNKNOWN"),
                "Title": misc.get("Title", "N/A"),
                "CVE": misc.get("ID", "N/A"),
                "Description": misc.get("Description", ""),
                "Target": target,
                "Type": "Misconfiguration"
            })
        
        # Secrets
        for secret in result.get("Secrets", []):
            trivy_vulns.append({
                "Package": target,
                "Version": "N/A",
                "FixedVersion": "Entfernen Sie das Secret",
                "Severity": "HIGH",
                "Title": f"Secret gefunden: {secret.get('RuleID', 'N/A')}",
                "CVE": "N/A",
                "Description": secret.get("Match", ""),
                "Target": target,
                "Type": "Secret"
            })
    
    # Nach Schweregrad sortieren
    trivy_vulns.sort(key=lambda x: severity_order.get(x.get("Severity", "UNKNOWN"), 5))
    
    # OWASP Vulnerabilities
    owasp_vulns = []
    for dep in owasp_data.get("dependencies", []):
        package_name = dep.get("fileName", "Unknown")
        
        for vuln in dep.get("vulnerabilities", []):
            owasp_vulns.append({
                "Package": package_name,
                "Version": dep.get("version", "N/A"),
                "FixedVersion": ", ".join(vuln.get("versions", [])) or "Nicht verfügbar",
                "Severity": vuln.get("severity", "UNKNOWN").upper(),
                "Title": vuln.get("name", "N/A"),
                "CVE": vuln.get("name", "N/A"),
                "Description": vuln.get("description", ""),
                "Target": "Abhängigkeit",
                "Type": "OWASP"
            })
    
    # Nach Schweregrad sortieren
    owasp_vulns.sort(key=lambda x: severity_order.get(x.get("Severity", "UNKNOWN"), 5))
    
    # Kombiniere und begrenze auf max_items
    all_vulns = trivy_vulns + owasp_vulns
    all_vulns.sort(key=lambda x: severity_order.get(x.get("Severity", "UNKNOWN"), 5))
    
    return all_vulns[:max_items]


def build_prompt_with_logs(trivy_data, owasp_data):
    """
    Erstellt einen strukturierten Prompt mit den Sicherheitsergebnissen.
    Enthält jetzt sowohl eine humorvolle Zusammenfassung als auch strukturierte 
    Informationen für eine detaillierte Berichterstellung.
    """
    try:
        # Lädt das Humor-Template
        humor_base = Path(MODEL_HUMOR_PATH).read_text().strip()
        
        # Extrahiert die relevantesten Vulnerabilitäten
        vulnerabilities = extract_vulnerabilities_for_prompt(trivy_data, owasp_data)
        
        # Berechnet Zusammenfassungen für einen Überblick
        trivy_summary = summarize_trivy_results(trivy_data.get("Results", []))
        owasp_summary = summarize_owasp_results(owasp_data.get("dependencies", []))
        
        # Erstellt eine Übersicht für den Report
        overview = {
            "trivy": {
                "total": sum(trivy_summary.values()),
                **trivy_summary
            },
            "owasp": {
                "total": sum(owasp_summary.values()),
                **owasp_summary
            },
            "total": {
                "critical": trivy_summary["critical"] + owasp_summary["critical"],
                "high": trivy_summary["high"] + owasp_summary["high"],
                "medium": trivy_summary["medium"] + owasp_summary["medium"],
                "low": trivy_summary["low"] + owasp_summary["low"],
            }
        }
        
        # Erstellt einen aufbereiteten Prompt für die KI
        prompt = f"""
{humor_base}

## ÜBERSICHT DER SICHERHEITSPROBLEME

Trivy-Scan:
- Kritisch: {overview['trivy']['critical']}
- Hoch: {overview['trivy']['high']}
- Mittel: {overview['trivy']['medium']}
- Niedrig: {overview['trivy']['low']}

OWASP-Scan:
- Kritisch: {overview['owasp']['critical']}
- Hoch: {overview['owasp']['high']}
- Mittel: {overview['owasp']['medium']}
- Niedrig: {overview['owasp']['low']}

## DETAILLIERTE SICHERHEITSPROBLEME
Die folgenden {len(vulnerabilities)} wichtigsten Sicherheitsprobleme wurden identifiziert:

{json.dumps(vulnerabilities, indent=2)}

## ANWEISUNGEN FÜR DIE KI

Erstelle einen humorvollen und informativen Sicherheitsbericht mit den folgenden Abschnitten:

1. WITZ: Ein humorvoller Einleitungssatz oder Absatz, der die Sicherheitslage zusammenfasst.

2. SICHERHEITSÜBERSICHT: Eine Markdown-Tabelle mit den wichtigsten gefundenen Sicherheitsproblemen. Die Tabelle sollte folgende Spalten haben:
   - Package/Komponente
   - Schweregrad
   - Problem (CVE/ID)
   - Verfügbare Lösung
   - Empfohlene Aktion

3. TECHNISCHE HINWEISE: Kurze technische Details zu den 2-3 kritischsten Problemen (falls vorhanden).

4. EMPFOHLENE SCHRITTE: 2-3 konkrete Schritte zur Behebung der wichtigsten Probleme.

Wenn keine Probleme gefunden wurden, erstelle einen humorvollen Glückwunschtext.
Beende den Bericht immer mit einem kurzen, humorvollen Absatz.
"""
        return prompt
    except Exception as e:
        logging.error(f"Error building prompt: {e}")
        return "Fehler beim Erstellen der Sicherheitszusammenfassung."


def save_message_to_file(message: str):
    """
    Speichert die generierte Nachricht in einer Datei.
    """
    try:
        path = Path(__file__).parent / "security_report.txt"
        path.write_text(message, encoding="utf-8")
        logging.info(f"Security report saved to {path}")
        return path
    except Exception as e:
        logging.error(f"Error saving message: {e}")
        return None


async def send_prompt_to_deepseek(prompt):
    try:
        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a security expert with a sense of humor."},
                {"role": "user", "content": prompt}
            ],
            temperature=1.0
        )
        message = response.choices[0].message.content
        if not message or not isinstance(message, str):
            return "KI-Modell lieferte keine gültige Antwort. Bitte prüfen Sie die Scan-Ergebnisse manuell."
        return message
    except Exception as e:
        logging.error(f"Exception bei DeepSeek: {e}")
        return f"Fehler bei der API-Anfrage an DeepSeek: {str(e)}"


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
            
            # Lädt die Scan-Ergebnisse
            trivy_data, owasp_data = load_scan_results(CURRENT_COMMIT_ID)
            
            # Speichert Ergebnisse für Frontend
            save_analysis_json(trivy_data, owasp_data, CURRENT_COMMIT_ID)

            # Erstellt einen strukturierten Prompt mit den Scan-Ergebnissen
            prompt = build_prompt_with_logs(trivy_data, owasp_data)
            
            # Generiert den Sicherheitsbericht mit DeepSeek
            security_report = await send_prompt_to_deepseek(prompt)
            
            # Speichert den Bericht
            save_message_to_file(security_report)
            
            # Sendet den Bericht an Discord, falls ein Webhook konfiguriert ist
            if DISCORD_WEBHOOK_URL:
                await send_discord(security_report)
                
        logging.info("Security analysis completed successfully")
                
    except Exception as e:
        logging.error(f"Fehler in main(): {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())