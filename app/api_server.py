from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path

app = FastAPI()

# CORS erlauben
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
