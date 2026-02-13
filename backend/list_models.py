import requests
import json

def list_models():
    response = requests.get("https://openrouter.ai/api/v1/models")
    if response.status_code == 200:
        models = response.json()['data']
        gemini_models = [m['id'] for m in models if 'gemini' in m['id'].lower()]
        print(json.dumps(gemini_models, indent=2))
    else:
        print(f"Error: {response.status_code} {response.text}")

if __name__ == "__main__":
    list_models()
