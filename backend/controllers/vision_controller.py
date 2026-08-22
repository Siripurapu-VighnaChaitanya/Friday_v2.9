import pyautogui
import base64
import requests
import os
import tempfile

OLLAMA_API = "http://localhost:11434/api/generate"

def capture_and_describe(prompt="What is on my screen?"):
    """
    Captures a screenshot, encodes it to base64, and asks Moondream to describe it.
    """
    temp_path = None
    try:
        # 1. Take Screenshot
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f:
            temp_path = f.name
        
        pyautogui.screenshot(temp_path)
        
        # 2. Encode to Base64
        with open(temp_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
        
        # 3. Call Ollama Moondream
        payload = {
            "model": "moondream",
            "prompt": prompt,
            "stream": False,
            "images": [encoded_image]
        }
        
        response = requests.post(OLLAMA_API, json=payload, timeout=60)
        
        if response.status_code == 200:
            description = response.json().get("response", "").strip()
            return description
        else:
            return f"Error from Ollama: {response.status_code}"
            
    except Exception as e:
        return f"Vision Error: {e}"
        
    finally:
        # 4. Cleanup
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass

if __name__ == "__main__":
    # Test call
    print("Testing Friday Vision...")
    print(capture_and_describe())
