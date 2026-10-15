import base64
import requests

# 1. Convertir une image locale en base64
with open("test_facture.jpg", "rb") as image_file:
    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

# 2. Appeler l'API
response = requests.post(
    "http://localhost:8000/extract",
    json={"image_base64": f"data:image/jpeg;base64,{encoded_string}"}
)

# 3. Afficher le résultat
print("Status:", response.status_code)
print("Résultat:", response.json())