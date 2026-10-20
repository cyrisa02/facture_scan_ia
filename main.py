import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from groq import Groq
import instructor
from dotenv import load_dotenv
import httpx

load_dotenv()

app = FastAPI(title="FactureScan IA API")

# --- CONFIGURATION CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURATION CLIENT (VIA .ENV) ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_APPS_SCRIPT_URL = os.getenv("GOOGLE_APPS_SCRIPT_URL") 

if not GROQ_API_KEY or not GOOGLE_APPS_SCRIPT_URL:
    raise ValueError("Variables d'environnement GROQ_API_KEY ou GOOGLE_APPS_SCRIPT_URL manquantes")

# --- SCHÉMAS PYDANTIC ---
class ExtractionFacture(BaseModel):
    date: str = Field(description="Format YYYY-MM-DD")
    fournisseur: str
    montant_ht: float
    montant_tva: float
    montant_ttc: float
    numero_facture: Optional[str] = None
    lignes: Optional[List[dict]] = None

class ImageRequest(BaseModel):
    image_base64: str

# --- CLIENT GROQ ---
client = instructor.from_groq(
    Groq(api_key=GROQ_API_KEY),
    mode=instructor.Mode.JSON
)

# --- FONCTION WEBHOOK ASYNCHRONE ---
async def send_to_google_sheets(payload: dict):
    """Envoie les données vers le Sheet configuré en arrière-plan"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            response = await http_client.post(
                GOOGLE_APPS_SCRIPT_URL, 
                json=payload,
                headers={"Content-Type": "application/json"} 
            )
            print(f"[SHEETS] Status: {response.status_code}")
    except Exception as e:
        print(f"[SHEETS] Erreur critique: {e}")

@app.post("/extract")
async def extract_invoice(request: ImageRequest, background_tasks: BackgroundTasks):
    try:
        image_base64 = request.image_base64
        if "," in image_base64:
            image_base64 = image_base64.split(",")[1]
            
        image_data_uri = f"data:image/jpeg;base64,{image_base64}"

        # Extraction IA
        extraction = client.chat.completions.create(
            model="qwen/qwen3-8b",
            response_model=ExtractionFacture,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extrais les données de cette facture. Retourne null si illisible."},
                        {"type": "image_url", "image_url": {"url": image_data_uri}}
                    ]
                }
            ],
            max_tokens=1000
        )
        
        # Envoi AUTOMATIQUE vers le sheet (non bloquant)
        background_tasks.add_task(send_to_google_sheets, extraction.model_dump())
            
        return extraction
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))