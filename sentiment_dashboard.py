import streamlit as st
from firebase_config import db

if "user" not in st.session_state:
    st.warning("Please log in to access this page.")
else:
    st.title("Sentiment Analysis Dashboard")
    user_email = st.session_state["user"]["email"]
    st.write(f"Logged in as: {user_email}")

    # Store user login history
    user_id = st.session_state["user"]["localId"]
    db.child("users").child(user_id).update({"last_login": st.session_state["user"]["lastLoginAt"]})

    # Sentiment Analysis Code Here
