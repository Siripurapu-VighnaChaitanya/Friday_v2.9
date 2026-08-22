import firebase_admin
from firebase_admin import credentials, firestore
import os

# Configuration
FIREBASE_CONFIG_FILE = "friday-4069f-firebase-adminsdk-fbsvc-2df7994540.json"

_initialization_done = False
_db = None

def get_db():
    """
    Initializes Firebase if not already done and returns the Firestore client.
    """
    global _initialization_done, _db
    
    if not _initialization_done:
        try:
            # Look for config one level up from utils/
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            full_path = os.path.join(base_dir, FIREBASE_CONFIG_FILE)
            
            if os.path.exists(full_path):
                cred = credentials.Certificate(full_path)
                firebase_admin.initialize_app(cred)
                _db = firestore.client()
                _initialization_done = True
                print(f"[OK] Firebase central init successful with {FIREBASE_CONFIG_FILE}")
            else:
                print(f"[WARN] Firebase config not found at {full_path}")
        except Exception as e:
            print(f"[ERROR] Firebase Central Init Error: {e}")
            
    return _db
