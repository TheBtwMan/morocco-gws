import urllib.request
import json

def test_general_chat(message):
    url = "http://localhost:8000/chat"
    data = {
        "message": message,
        "history": [],
        "current_year": 2024,
        "current_index": "GWSA",
        "current_location": None
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    
    try:
        print(f"Sending query: '{message}'")
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode("utf-8"))
            print("\n--- RESPONSE ---")
            print(res["response"])
            print("----------------\n")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_general_chat("whats the region with the best groundwater region")
    test_general_chat("can you invest in Rabat?") # testing region detection query (should analyze Rabat)
    test_general_chat("what is NDWI?") # testing explain query
