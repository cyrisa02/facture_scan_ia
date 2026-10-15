import os
import base64
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from groq import Groq
import instructor
from dotenv import load_dotenv

load_dotenv()



app = FastAPI(title="FactureScan IA API")

# 1. Définition stricte du schéma de données (Contrat de sortie)
class LigneFacture(BaseModel):
    description: str
    montant_ht: float

class ImageRequest(BaseModel):
    image_base64: str


class ExtractionFacture(BaseModel):
    date: str = Field(description="Format strict YYYY-MM-DD")
    fournisseur: str
    montant_ht: float
    montant_tva: float
    montant_ttc: float
    numero_facture: Optional[str] = Field(default=None, description="Null si illisible")
    lignes: Optional[List[LigneFacture]] = Field(default=None, description="Détail des lignes si visible")

# 2. Initialisation du client Groq avec le mode JSON d'Instructor
client = instructor.from_groq(
    Groq(api_key=os.getenv("GROQ_API_KEY")),
    mode=instructor.Mode.JSON
)

@app.post("/extract")
async def extract_invoice(request: ImageRequest):
    try:
        image_base64 = request.image_base64
        
        if "," in image_base64:
            image_base64 = image_base64.split(",")[1]
            
        image_data_uri = f"data:image/jpeg;base64,{image_base64}"

        extraction = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            response_model=ExtractionFacture,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extrais les données de cette facture ou ticket de caisse. Si une information est illisible ou absente, retourne null pour les champs optionnels ou 0.0 pour les montants. Ne devine pas les chiffres."
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": image_data_uri}
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        return extraction
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur d'extraction IA : {str(e)}")
        return extraction
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur d'extraction IA : {str(e)}")