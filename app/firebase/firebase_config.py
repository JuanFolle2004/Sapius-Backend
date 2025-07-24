import firebase_admin
from firebase_admin import credentials, firestore, auth
import os

# Full path to service account key
cred_path = os.path.join(os.path.dirname(__file__), "serviceAccountKey.json")

print(f"🔍 Looking for serviceAccountKey.json at: {cred_path}")
print(f"🔍 File exists? {os.path.exists(cred_path)}")

# Initialize only once
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase initialized successfully.")
    except Exception as e:
        print("❌ Firebase initialization failed:", e)

# Create Firestore client
db = firestore.client()
