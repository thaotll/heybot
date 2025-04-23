from fastapi import FastAPI
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
MESSAGE_FILE = BASE_DIR / "latest_deepseek_message.txt"

# GET-Endpunkt: Holt die letzte DeepSeek-Nachricht
@app.get("/deepseek-message")
async def get_deepseek_message():
    try:
        with open(MESSAGE_FILE, "r", encoding="utf-8") as file:
            message = file.read()
        return {"message": message}
    except FileNotFoundError:
        return {"message": "Noch keine DeepSeek-Nachricht vorhanden."}

# Modell für POST-Nachricht
class DeepSeekMessage(BaseModel):
    message: str

# POST-Endpunkt: Speichert neue DeepSeek-Nachricht
@app.post("/deepseek-message")
async def save_deepseek_message(payload: DeepSeekMessage):
    try:
        with open(MESSAGE_FILE, "w", encoding="utf-8") as file:
            file.write(payload.message)
        return {"status": "success", "message": payload.message}
    except Exception as e:
        return {"status": "error", "message": str(e)}
