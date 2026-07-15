import urllib.request
import urllib.parse
import json
import sys

def run_post():
    url = "http://127.0.0.1:8000/api/v1/incidents/report"
    print(f"[*] Posting mock incident to Ingestion API: {url}...")
    
    # Form data payload mapping to report_incident parameters
    data = {
        "text_fallback": "A car crashed on the highway and the driver is bleeding from the head.",
        "latitude": "17.3850",
        "longitude": "78.4867",
        "language_code": "en",
        "incidentMode": "text"
    }
    
    # Encode as application/x-www-form-urlencoded
    encoded_data = urllib.parse.urlencode(data).encode('utf-8')
    
    req = urllib.request.Request(url, data=encoded_data)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = response.read().decode('utf-8')
            res_json = json.loads(res_data)
            print("\n==========================================")
            print("          API POST INGESTION SUCCESS      ")
            print("==========================================")
            print(json.dumps(res_json, indent=2))
            print("==========================================\n")
    except urllib.error.URLError as e:
        print(f"[!] API Post failed: {e}")
        if hasattr(e, 'read'):
            print(f"Details: {e.read().decode('utf-8')}")

if __name__ == "__main__":
    run_post()
