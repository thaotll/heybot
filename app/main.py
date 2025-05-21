import os
import json
import logging
import asyncio
import subprocess
import tempfile
import shutil
from pathlib import Path
import argparse
from datetime import datetime

import aiohttp
from dotenv import load_dotenv
from openai import AsyncOpenAI
import pytz
import httpx

# Load .env file for local development
load_dotenv(Path(__file__).parent / ".env")

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Zeige Startinformationen
logging.info("=" * 50)
logging.info("HeyBot Security Scanner gestartet")
logging.info(f"Aktuelle Zeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
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
RUN_MODE = os.getenv('RUN_MODE', 'scan')

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
    Führt den Trivy-Scan in einem temporären Verzeichnis durch und gibt die Ergebnisse als Diktionär zurück.
    """
    # Verwende einen temporären Dateinamen für die Trivy-Ausgabe
    # tempfile.NamedTemporaryFile erstellt eine Datei, die nach dem Schließen automatisch gelöscht wird.
    # Wir brauchen den Namen, um ihn an Trivy zu übergeben, und lesen ihn dann, bevor er gelöscht wird.
    trivy_data = {"Results": []} # Standardwert bei Fehlern

    try:
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as tmp_output_file_obj:
            tmp_output_file_name = tmp_output_file_obj.name
        
        logging.info(f"Starting Trivy scan for commit {commit_id}")
        logging.info(f"Scanning directory: {temp_dir}")
        logging.info(f"Temporary Trivy output file: {tmp_output_file_name}")
        
        trivy_cmd = [
            "trivy", "fs",
            "--format", "json",
            "--severity", "CRITICAL,HIGH,MEDIUM,LOW",
            "--no-progress",
            "--scanners", "vuln,secret,misconfig",
            "--output", tmp_output_file_name, # Ausgabe in temporäre Datei
            str(temp_dir)
        ]
        
        logging.info(f"Running Trivy command: {' '.join(trivy_cmd)}")
        
        process = subprocess.Popen(
            trivy_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        for line in process.stdout:
            line = line.strip()
            if "error" in line.lower() or "fatal" in line.lower():
                logging.error(f"Trivy: {line}")
            elif "warn" in line.lower():
                logging.warning(f"Trivy: {line}")
            else:
                logging.info(f"Trivy: {line}")
        
        return_code = process.wait()

        if return_code == 0:
            logging.info(f"Trivy scan completed for commit {commit_id}")
            # Lese die Ergebnisse aus der temporären Datei
            if Path(tmp_output_file_name).exists():
                file_size = Path(tmp_output_file_name).stat().st_size
                if file_size > 0:
                    with open(tmp_output_file_name, 'r') as f:
                        trivy_data = json.load(f)
                    logging.info(f"Successfully loaded Trivy results from {tmp_output_file_name}")
                else:
                    logging.warning(f"Trivy temporary output file {tmp_output_file_name} is empty.")
            else:
                logging.error(f"Trivy temporary output file {tmp_output_file_name} was not created.")
        else:
            logging.error(f"Trivy scan failed with return code {return_code}")
            # trivy_data bleibt {"Results": []}
            
    except subprocess.CalledProcessError as e:
        logging.error(f"Trivy scan failed: {str(e)}")
        if hasattr(e, 'stdout') and e.stdout: logging.error(f"Stdout: {e.stdout}")
        if hasattr(e, 'stderr') and e.stderr: logging.error(f"Stderr: {e.stderr}")
        # trivy_data bleibt {"Results": []}
    except Exception as e:
        logging.error(f"Unexpected error during Trivy scan: {str(e)}")
        # trivy_data bleibt {"Results": []}
    finally:
        # Stelle sicher, dass die temporäre Datei gelöscht wird, falls sie noch existiert
        if 'tmp_output_file_name' in locals() and Path(tmp_output_file_name).exists():
            try:
                Path(tmp_output_file_name).unlink()
                logging.info(f"Cleaned up temporary Trivy output file: {tmp_output_file_name}")
            except OSError as e_unlink:
                logging.error(f"Error deleting temporary Trivy file {tmp_output_file_name}: {e_unlink}")
                
    return trivy_data


def run_owasp_scan(temp_dir, commit_id):
    """
    Führt den OWASP-Scan in einem temporären Verzeichnis durch und gibt die Ergebnisse als Diktionär zurück.
    Die OWASP-Datenbank wird weiterhin im ANALYSIS_DIR gespeichert.
    """
    owasp_data = {"dependencies": []} # Standardwert bei Fehlern
    
    # Temporäres Verzeichnis für die OWASP-Ausgabe dieser spezifischen Analyse
    # Dies ist getrennt vom gescannten `temp_dir`, das den Quellcode enthält.
    with tempfile.TemporaryDirectory(prefix="owasp_output_") as owasp_output_temp_dir_str:
        owasp_output_temp_dir = Path(owasp_output_temp_dir_str)
        # OWASP wird seine JSON-Datei in dieses temporäre Verzeichnis schreiben.
        # Der Name der Datei ist normalerweise dependency-check-report.json oder ähnlich.
        # Wir müssen sie nach dem Scan finden.
        
        # OWASP-Datenbank-Verzeichnis (bleibt im ANALYSIS_DIR für Persistenz)
        data_dir = ANALYSIS_DIR / "owasp-data"
        data_dir.mkdir(exist_ok=True)
        
        try:
            logging.info(f"Starting OWASP scan for commit {commit_id}")
            logging.info(f"OWASP database directory: {data_dir}")
            logging.info(f"Scanning directory (source code): {temp_dir}")
            logging.info(f"Temporary directory for OWASP JSON report: {owasp_output_temp_dir}")
            
            owasp_cmd = [
                "dependency-check",
                "--project", f"heybot-{commit_id}", # Eindeutiger Projektname pro Scan
                "--scan", str(temp_dir),
                "--format", "JSON",
                "--out", str(owasp_output_temp_dir), # Ausgabe in das temporäre Ausgabeverzeichnis
                "--failOnCVSS", "11",
                "--nodeAuditSkipDevDependencies", "false",
                "--data", str(data_dir),
                "--log", "info"
            ]
            
            logging.info(f"Running OWASP command: {' '.join(owasp_cmd)}")
            
            process = subprocess.Popen(
                owasp_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env={**os.environ}
            )
            
            for line in process.stdout:
                line = line.strip()
                if "ERROR" in line or "FATAL" in line:
                    logging.error(f"OWASP: {line}")
                elif "WARN" in line:
                    logging.warning(f"OWASP: {line}")
                elif "INFO" in line and ("Progress" in line or "Download" in line or "Processing" in line or "Checking" in line):
                    logging.info(f"OWASP Progress: {line}")
            
            return_code = process.wait()

            if return_code == 0:
                logging.info(f"OWASP scan completed for commit {commit_id}")
                # Finde die generierte JSON-Datei im temporären Ausgabeverzeichnis
                # Übliche Namen: dependency-check-report.json
                report_file_path = owasp_output_temp_dir / "dependency-check-report.json"

                if not report_file_path.exists():
                    # Fallback: Manchmal wird sie auch einfach als dependency-check.json benannt
                    report_file_path_alt = owasp_output_temp_dir / "dependency-check.json"
                    if report_file_path_alt.exists():
                        report_file_path = report_file_path_alt
                    else:
                        # Versuche, nach einer beliebigen .json-Datei zu suchen, falls die obigen nicht existieren
                        json_files = list(owasp_output_temp_dir.glob('*.json'))
                        if json_files:
                            report_file_path = json_files[0] # Nimm die erste gefundene
                            logging.info(f"Found OWASP report via glob: {report_file_path}")
                        else:
                             logging.error(f"OWASP JSON report not found in {owasp_output_temp_dir}. Expected dependency-check-report.json or similar.")
                             # owasp_data bleibt {"dependencies": []}
                             return owasp_data # Frühzeitiger Ausstieg, da keine Datei zum Lesen vorhanden ist

                if report_file_path.exists():
                    file_size = report_file_path.stat().st_size
                    if file_size > 0:
                        with open(report_file_path, 'r') as f:
                            owasp_data = json.load(f)
                        logging.info(f"Successfully loaded OWASP results from {report_file_path}")
                    else:
                        logging.warning(f"OWASP report file {report_file_path} is empty.")
                # Die temporäre Datei und das Verzeichnis werden durch den with-Kontext von TemporaryDirectory automatisch bereinigt.

            else:
                logging.error(f"OWASP scan failed with return code {return_code}")
                # owasp_data bleibt {"dependencies": []}

        except subprocess.CalledProcessError as e:
            logging.error(f"OWASP scan failed: {str(e)}")
            if hasattr(e, 'stdout') and e.stdout: logging.error(f"Stdout: {e.stdout}")
            if hasattr(e, 'stderr') and e.stderr: logging.error(f"Stderr: {e.stderr}")
            # owasp_data bleibt {"dependencies": []}
        except Exception as e:
            logging.error(f"Unexpected error during OWASP scan: {str(e)}")
            # owasp_data bleibt {"dependencies": []}
        # Das temporäre Verzeichnis owasp_output_temp_dir wird hier automatisch gelöscht.

    return owasp_data


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


def save_deepseek_summary(commit_id, deepseek_message_content, trivy_data, owasp_data):
    """
    Speichert die DeepSeek-Zusammenfassung und die Zählungen der Schwachstellen.
    """
    logging.info(f"Saving DeepSeek summary for commit {commit_id}")
    
    trivy_summary_counts = summarize_trivy_results(trivy_data.get("Results", []))
    owasp_summary_counts = summarize_owasp_results(owasp_data.get("dependencies", []))

    # Determine overall status based on summaries for the new object
    overall_status_for_summary = "success"
    if trivy_summary_counts.get("critical",0) > 0 or trivy_summary_counts.get("high",0) > 0 or \
       owasp_summary_counts.get("critical",0) > 0 or owasp_summary_counts.get("high",0) > 0:
        overall_status_for_summary = "error"
    elif trivy_summary_counts.get("medium",0) > 0 or owasp_summary_counts.get("medium",0) > 0:
        overall_status_for_summary = "warning"

    # Placeholder for repository and branch - consider fetching from git or env
    repo_name = "thaotll/heybot" 
    branch_name = "main"
    try:
        # Attempt to get actual git info if in a git repo
        git_branch_output = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], text=True, cwd=BASE_DIR).strip()
        # For repo name, it's trickier, could parse from `git remote get-url origin`
        # For simplicity, keeping placeholders if direct git commands are not robust enough here or not always applicable
        if git_branch_output:
            branch_name = git_branch_output
    except Exception:
        logging.warning("Could not determine git branch for summary, using placeholder.")


    persisted_summary = {
        "id": commit_id,
        "commitId": commit_id,
        "repository": repo_name, 
        "branch": branch_name, 
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": overall_status_for_summary, # Overall status based on vuln counts
        "deepseek_summary": deepseek_message_content,
        "securityScansSummary": [
            {
                "tool": "trivy",
                "vulnerabilities": trivy_summary_counts
            },
            {
                "tool": "owasp",
                "vulnerabilities": owasp_summary_counts
            }
        ]
        # Add other fields from the original CodeAnalysis object if they are simple and useful for the frontend
        # e.g., author, feedback (commit message) - these might need to be passed in or fetched.
        # For now, keeping it focused on the DeepSeek summary and vuln counts.
    }

    summary_output_file = ANALYSIS_DIR / f"{commit_id}_summary.json"
    summary_output_file.write_text(json.dumps(persisted_summary, indent=2))
    logging.info(f"DeepSeek summary saved to {summary_output_file}")

    # Update latest_summary.json if this is the current commit
    current_commit_env = os.getenv('CURRENT_COMMIT_ID', 'latest') # Ensure latest is default if not set
    if commit_id == current_commit_env:
        latest_summary_file = ANALYSIS_DIR / "latest_summary.json"
        latest_summary_file.write_text(json.dumps(persisted_summary, indent=2))
        logging.info(f"DeepSeek summary also saved as {latest_summary_file}")
        
    return persisted_summary


def save_analysis_json(trivy_data, owasp_data, commit_id):
    """
    Speichert die Analyseergebnisse im JSON-Format.
    Now constructs a more complete CodeAnalysis object.
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

    overall_status = "success"
    if trivy_status == "error" or owasp_status == "error":
        overall_status = "error"
    elif trivy_status == "warning" or owasp_status == "warning":
        overall_status = "warning"

    # Construct the full CodeAnalysis object
    analysis_result_full = {
        "id": commit_id,
        "commitId": commit_id,
        "repository": "thaotll/heybot", # Placeholder
        "branch": "main", # Placeholder
        "timestamp": datetime.utcnow().isoformat() + "Z", # Timestamp of analysis generation
        "status": overall_status,
        "feedback": "HeyBot Analysis", # Placeholder for commit message
        "author": "HeyBot", # Placeholder for commit author
        "issues": [], # Placeholder
        "files": [],  # Placeholder
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
        ],
        "kubernetesStatus": { # Placeholder
            "pods": {"total": 0, "running": 0, "pending": 0, "failed": 0},
            "deployments": {"total": 0, "available": 0, "unavailable": 0},
            "services": 0
        }
    }
    
    return analysis_result_full # Return the full object


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


async def analyze_specific_commit(commit_id, run_mode_arg='scan'):
    if run_mode_arg != 'scan':
        logging.info(f"analyze_specific_commit called in non-scan mode ({run_mode_arg}) for {commit_id}. No actions taken by this function.")
        # Return default/empty structures for compatibility if something in main() still expects them
        # The second element should be the result of calling the modified save_analysis_json
        return None, save_analysis_json({}, {}, commit_id) 

    logging.info(f"Starting 'scan' mode security analysis for commit {commit_id}")

    trivy_data = {} # Default
    owasp_data = {} # Default
    security_report_content = "Scan did not complete successfully or produced no actionable data."
    persisted_summary = None

    # Verwende einen temporären Ordner für die Analyse
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        try:
            # Ignore common patterns that shouldn't be part of the scan, or could cause issues.
            # Especially important to ignore 'analysis' to prevent recursion if BASE_DIR is cwd.
            ignore_patterns = shutil.ignore_patterns('.git', '.idea', '__pycache__', 'node_modules', '.next', 'analysis', '*.tmp', '*.pyc', 'owasp-data')
            shutil.copytree(BASE_DIR, temp_dir, dirs_exist_ok=True, ignore=ignore_patterns)
            logging.info(f"Copied source from {BASE_DIR} to {temp_dir} for scanning, ignoring patterns.")
        except Exception as e:
            logging.error(f"Failed to copy source to temp dir for {commit_id}: {e}")
            legacy_code_analysis = save_analysis_json({}, {}, commit_id) # Construct minimal old object
            return None, legacy_code_analysis 

        logging.info(f"Running Trivy and OWASP scans in {temp_dir} for {commit_id}...")
        trivy_data = run_trivy_scan(temp_dir, commit_id)
        owasp_data = run_owasp_scan(temp_dir, commit_id)

    # Generate DeepSeek report
    # Check if scans actually returned something meaningful beyond default empty
    # Check specifically for the keys that hold results, and if those keys have content.
    trivy_has_results = trivy_data and trivy_data.get("Results") is not None and len(trivy_data.get("Results")) > 0
    owasp_has_results = owasp_data and owasp_data.get("dependencies") is not None and len(owasp_data.get("dependencies")) > 0

    if trivy_has_results or owasp_has_results:
        logging.info(f"Scans for {commit_id} produced data. Building prompt for DeepSeek.")
        prompt = build_prompt_with_logs(trivy_data, owasp_data)
        security_report_content = await send_prompt_to_deepseek(prompt)
    else:
        security_report_content = "Scans ran but returned no specific vulnerabilities or misconfigurations."
        logging.info(f"Scans for {commit_id} returned no specific findings. Generating a clean bill of health message from DeepSeek.")
        # Still generate a prompt for DeepSeek to get an "all clear" type message or handle empty results gracefully.
        prompt = build_prompt_with_logs(trivy_data, owasp_data) # build_prompt_with_logs should handle empty inputs
        security_report_content = await send_prompt_to_deepseek(prompt)
    
    # Speichert den Bericht lokal (Debugging)
    save_message_to_file(security_report_content)

    # Speichert die neue DeepSeek-Zusammenfassung persistent
    persisted_summary = save_deepseek_summary(commit_id, security_report_content, trivy_data, owasp_data)

    # Sendet den Bericht an Discord, falls ein Webhook konfiguriert ist
    if DISCORD_WEBHOOK_URL and security_report_content:
        # Check if the message is more than just a generic failure message before sending
        if "Fehler bei der API-Anfrage an DeepSeek" not in security_report_content and \
           "KI-Modell lieferte keine gültige Antwort" not in security_report_content:
            logging.info(f"Scan mode: Sending analysis summary for {commit_id} to Discord.")
            await send_discord(security_report_content)
        else:
            logging.warning(f"Skipping Discord notification for {commit_id} due to DeepSeek error in report content.")
    
    # Konstruiere das alte CodeAnalysis-Objekt (ohne Dateischreiben) für Rückwärtskompatibilität
    legacy_code_analysis_object = save_analysis_json(trivy_data, owasp_data, commit_id)
    
    return persisted_summary, legacy_code_analysis_object


async def get_commit_analysis(commit_id):
    """
    Holt die Analyseergebnisse für einen Commit.
    Sollte die neue '_summary.json'-Datei laden.
    """
    summary_file_name = f"{commit_id}_summary.json"
    analysis_file = ANALYSIS_DIR / summary_file_name
    
    if commit_id == "latest": # Special handling for "latest"
        analysis_file = ANALYSIS_DIR / "latest_summary.json"
        logging.info(f"Attempting to load latest summary: {analysis_file}")
    else:
        logging.info(f"Attempting to load summary for commit {commit_id}: {analysis_file}")

    if not analysis_file.exists():
        logging.warning(f"Summary file {analysis_file} not found.")
        # Optional: Fallback to old format if API needs to be very robust to old data?
        # For now, sticking to the new format for this function.
        # old_format_file = ANALYSIS_DIR / f"{commit_id}.json"
        # if old_format_file.exists():
        #     logging.warning(f"Found old format file {old_format_file}, but this function expects new summary format.")
        return None 
    
    try:
        logging.info(f"Loading summary from {analysis_file}")
        return json.loads(analysis_file.read_text())
    except Exception as e:
        logging.error(f"Failed to load analysis summary for {analysis_file.stem}: {e}")
        return None


# Main entry
async def main():
    """Hauptfunktion zum Ausführen von Scan oder Server-Modus."""
    logging.info("HeyBot __main__ execution started.")
    
    parser = argparse.ArgumentParser(description="HeyBot Security Scanner")
    parser.add_argument("--mode", type=str, choices=['scan', 'serve'], default='scan', 
                        help="Run mode: 'scan' to perform security analysis, 'serve' to run in server mode (placeholder).")
    parser.add_argument("--commit-id", type=str, default=None, 
                        help="Specific commit ID to analyze. If not provided, defaults to CURRENT_COMMIT_ID env var or git rev-parse HEAD.")
    
    args = parser.parse_args()

    # Determine the commit ID to analyze
    # Priority: command-line arg -> CURRENT_COMMIT_ID env -> git rev-parse
    commit_id_to_analyze = args.commit_id
    if not commit_id_to_analyze:
        commit_id_to_analyze = os.getenv('CURRENT_COMMIT_ID')
    if not commit_id_to_analyze:
        try:
            commit_id_to_analyze = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
        except Exception as e:
            logging.warning(f"Could not determine commit ID from git: {e}. Falling back to 'latest'.")
            commit_id_to_analyze = "latest" # Fallback if git fails

    if not commit_id_to_analyze: # Final fallback if all else fails
        logging.error("CRITICAL: Commit ID could not be determined. Please provide --commit-id or ensure git is available / CURRENT_COMMIT_ID is set.")
        return # Exit if no commit ID

    logging.info(f"Selected commit ID for analysis: {commit_id_to_analyze}")

    if args.mode == 'scan':
        logging.info(f"Running in SCAN mode for commit: {commit_id_to_analyze}")
        # Ensure analyze_specific_commit uses this resolved commit_id
        analysis_result, legacy_report_data = await analyze_specific_commit(commit_id_to_analyze, run_mode_arg='scan')
        
        if analysis_result:
            logging.info(f"Scan completed. Summary for {commit_id_to_analyze} has been saved.")
            # Optionally, print the summary or part of it
            # logging.info(json.dumps(analysis_result, indent=2))
        else:
            logging.error(f"Scan for commit {commit_id_to_analyze} did not produce a result.")

    elif args.mode == 'serve':
        logging.info("Running in SERVE mode.")
        # In 'serve' mode, we expect data to be on the PV.
        # The main.py script, when run with --mode serve by start.sh, 
        # can perform checks or pre-processing if needed.
        # For now, it mainly ensures the ANALYSIS_DIR is used.
        
        # Example: Check if latest_summary.json exists
        latest_summary_path = ANALYSIS_DIR / "latest_summary.json"
        if latest_summary_path.exists():
            logging.info(f"'serve' mode: Found {latest_summary_path}")
            # Potentially load and validate it or other summaries.
            # For now, just confirm it's there.
        else:
            logging.warning(f"'serve' mode: {latest_summary_path} not found. API server might not have latest data.")
            # This might be okay if the PV is initially empty and gets populated by scans later
            # or if specific commit_id files are the primary concern.

        # The actual serving is done by api_server.py, started by start.sh
        # This 'serve' mode in main.py is more for pre-flight checks or data prep on the PV.
        logging.info("'serve' mode tasks in main.py complete. API server will handle requests.")
        pass

if __name__ == "__main__":
    asyncio.run(main())