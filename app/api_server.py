from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from typing import Optional
from main import get_commit_analysis
import json
import logging

app = FastAPI()

# CORS erlauben
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In Produktion sollte dies eingeschränkt werden
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Absoluter Pfad zur Datei
BASE_DIR = Path(__file__).parent
MAIN_MESSAGE_FILE = BASE_DIR / "main_message.txt"
BAZINGA_MESSAGE_FILE = BASE_DIR / "bazinga_message.txt"
LEGACY_FILE = BASE_DIR / "latest_deepseek_message.txt"

# GET-Endpunkt: Holt die letzte DeepSeek-Nachricht
@app.get("/deepseek-message")
async def get_deepseek_message(variant: str = Query("main", enum=["main", "bazinga", "legacy"])):
    file_map = {
        "main": MAIN_MESSAGE_FILE,
        "bazinga": BAZINGA_MESSAGE_FILE,
        "legacy": LEGACY_FILE
    }
    path = file_map.get(variant, LEGACY_FILE)

    try:
        return {"message": path.read_text(encoding="utf-8")}
    except FileNotFoundError:
        return {"message": f"No DeepSeek message found for '{variant}'."}

# === Direkter Zugriff für Testing oder alte Routen ===
@app.get("/deepseek-message/main")
async def get_main_message():
    try:
        return {"message": MAIN_MESSAGE_FILE.read_text(encoding="utf-8")}
    except FileNotFoundError:
        return {"message": "Noch keine Main-Nachricht vorhanden."}

@app.get("/deepseek-message/bazinga")
async def get_bazinga_message():
    try:
        return {"message": BAZINGA_MESSAGE_FILE.read_text(encoding="utf-8")}
    except FileNotFoundError:
        return {"message": "Noch keine Bazinga-Nachricht vorhanden."}

@app.get("/deepseek-message/legacy")
async def get_legacy_message():
    try:
        return {"message": LEGACY_FILE.read_text(encoding="utf-8")}
    except FileNotFoundError:
        return {"message": "Noch keine DeepSeek-Nachricht vorhanden."}

# Modell für POST-Nachricht
class DeepSeekMessage(BaseModel):
    message: str

# POST-Endpunkt: Speichert neue DeepSeek-Nachricht
@app.post("/deepseek-message")
async def save_deepseek_message(payload: DeepSeekMessage):
    try:
        LEGACY_FILE.write_text(payload.message, encoding="utf-8")
        return {"status": "success", "message": payload.message}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/security-analysis/{commit_id}")
async def get_security_analysis(commit_id: str):
    """
    Liefert die Sicherheitsanalyse für einen spezifischen Commit.
    Falls keine Analyse vorhanden ist, wird sie automatisch durchgeführt.
    """
    try:
        analysis = get_commit_analysis(commit_id)
        if analysis is None:
            raise HTTPException(
                status_code=404,
                detail=f"Keine Analyse für Commit {commit_id} gefunden"
            )
        return analysis
    except Exception as e:
        logging.error(f"Error analyzing commit {commit_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler bei der Analyse: {str(e)}"
        )

@app.get("/security-analysis/latest")
async def get_latest_analysis():
    """
    Liefert die Sicherheitsanalyse des neuesten Commits.
    """
    try:
        latest_file = BASE_DIR / "analysis" / "latest.json"
        if not latest_file.exists():
            raise HTTPException(status_code=404, detail="Keine aktuelle Analyse verfügbar")
        return json.loads(latest_file.read_text())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
