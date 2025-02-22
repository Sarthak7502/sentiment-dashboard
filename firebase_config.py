# filepath: /c:/Users/jains/Desktop/sentiment-dashboard/firebase_config.py
import pyrebase
import firebase_admin
from firebase_admin import credentials, db
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Firebase Config
firebaseConfig = {
    "apiKey": os.getenv("AIzaSyCpwBEbH908USUjjM2MLoc0uIWqYN0Vl1U"),
    "authDomain": os.getenv("sentiment-dashboard-a3e15.firebaseapp.com"),
    "databaseURL": os.getenv("https://sentiment-dashboard-a3e15-default-rtdb.firebaseio.com/"),
    "projectId": os.getenv("sentiment-dashboard-a3e15"),
    "storageBucket": os.getenv("sentiment-dashboard-a3e15.appspot.com"),
    "messagingSenderId": os.getenv("203602648050"),
    "appId": os.getenv("1:203602648050:web:abc8964b083cb11680696b"),
    "measurementId": os.getenv("G-VPDH2Q1CGN"),
}

# Pyrebase Initialization
firebase = pyrebase.initialize_app(firebaseConfig)
db_pyrebase = firebase.database()

# Firebase Admin Initialization
cred = credentials.Certificate(os.getenv(r"C:\Users\jains\Desktop\sentiment-dashboard\sentiment-dashboard-a3e15-firebase-adminsdk-fbsvc-3b6fa0d617.json"))  # Download this from Firebase > Project Settings > Service accounts
firebase_admin.initialize_app(cred, {
    'databaseURL': firebaseConfig['databaseURL']
})

# User ID (Replace with the actual UID from Firebase Authentication)
admin_uid = "J2ulm6PTtDZaieHTvV4ez8g5LXi1"

# Add Admin User Data
admin_data = {
    "email": "jainsarthak.7502@gmail.com",
    "role": "admin"
}

# Store Data in Realtime Database
db.reference(f"/users/{admin_uid}").set(admin_data)
print("Admin added successfully!")

