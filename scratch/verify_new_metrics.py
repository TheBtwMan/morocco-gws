import urllib.request
import json
import sys

# Reconfigure stdout/stderr to use UTF-8 to prevent Windows terminal codec encoding crashes
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

output_file = r"C:\Users\PC\PFA\morocco-gws\scratch\new_metrics_verification.txt"

def test_point_data():
    lat, lon, year = 31.6295, -7.9811, 2024 # Marrakech area
    url = f"http://localhost:8000/data/point?lat={lat}&lon={lon}&year={year}"
    
    print(f"Requesting point data: {url}")
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode("utf-8"))
            print("Response:", json.dumps(res, indent=2))
            
            # Check for all 7 keys
            expected_keys = ["gwsa", "gwd", "ndwi", "ndvi", "recharge", "water_quantity", "suitability"]
            missing_keys = [k for k in expected_keys if k not in res]
            
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("New Metrics GEE Point Verification\n")
                f.write("==================================\n\n")
                f.write(f"Point: Lat={lat}, Lon={lon}, Year={year}\n")
                f.write(f"Response: {json.dumps(res, indent=2)}\n\n")
                
                if missing_keys:
                    f.write(f"[FAIL] Missing keys {missing_keys}\n")
                    print(f"[FAIL] Missing keys {missing_keys}")
                else:
                    f.write("[SUCCESS] All 7 metrics returned successfully.\n")
                    print("[SUCCESS] All 7 metrics returned successfully.")
                    
            return res
    except Exception as e:
        print(f"[ERROR] API Point Data Error: {e}")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"[ERROR] API Point Data Error: {e}\n")
        return None

def test_chat_advisor(point_data):
    if not point_data:
        print("Skipping chat advisor verification due to missing point data.")
        return

    url = "http://localhost:8000/chat"
    payload = {
        "message": "Analyze agricultural suitability and water risk for the selected location.",
        "history": [],
        "current_year": 2024,
        "current_index": "Suitability",
        "current_location": {
            "type": "point",
            "title": "📍 Test Farm Area",
            "lat": 31.6295,
            "lon": -7.9811,
            "data": point_data
        }
    }
    
    print("Sending request to Chat Advisor...")
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode("utf-8"))
            print("Chat Response received.")
            with open(output_file, "a", encoding="utf-8") as f:
                f.write("\n=========================================\n")
                f.write("Chat Advisor Response Verification\n")
                f.write("=========================================\n\n")
                f.write(res["response"])
                f.write("\n")
            print("[SUCCESS] Chat Advisor response written to new_metrics_verification.txt")
    except Exception as e:
        print(f"[ERROR] API Chat Advisor Error: {e}")
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"\n[ERROR] API Chat Advisor Error: {e}\n")

if __name__ == "__main__":
    res = test_point_data()
    test_chat_advisor(res)
