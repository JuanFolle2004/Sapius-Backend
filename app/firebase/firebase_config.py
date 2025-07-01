import firebase_admin
from firebase_admin import credentials, firestore, auth
import os

# Get the full path to the serviceAccountKey.json
cred_path = os.path.join(os.path.dirname(__file__), "serviceAccountKey.json")

# Initialize Firebase app (only once)
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

# Create a Firestore client
db = firestore.client()
