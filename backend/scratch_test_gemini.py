import os
import httpx
import json

def test_gemini():
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    print(f"[*] Listing models...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={gemini_key}"
    try:
        response = httpx.get(url, timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            for m in data.get("models", []):
                print(f"Model Name: {m.get('name')} | Supported Methods: {m.get('supportedGenerationMethods')}")
        else:
            print(f"[!] Error: {response.text}")
    except Exception as e:
        print(f"[!] Connection failed: {e}")

if __name__ == "__main__":
    test_gemini()
