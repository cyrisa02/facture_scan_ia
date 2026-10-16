import base64
import requests

# Convertir une image locale en base64
with open("test_facture.jpg", "rb") as image_file:
    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

# Appeler l'API Render (remplace par ta vraie URL)
response = requests.post(
    "https://facture-scan-ia.onrender.com/extract",
    json={"image_base64": f"data:image/jpeg;base64,{encoded_string}"}
)

print("Status:", response.status_code)
print("Résultat:", response.json())