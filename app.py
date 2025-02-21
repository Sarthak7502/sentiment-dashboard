# -------------------- Import Libraries --------------------
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import io
import pyrebase
import time
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from firebase_config import firebaseConfig  # Firebase Configuration
from transformers import pipeline
from PIL import Image
import requests
from io import BytesIO
import re

# -------------------- Firebase Initialization --------------------
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
db = firebase.database()

# -------------------- Streamlit Page Config --------------------
st.set_page_config(page_title="AI Sentiment Analysis Dashboard", layout="wide")

# Sidebar Navigation
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Go to", ["Home", "Login", "Signup", "Dashboard", "Sentiment Analysis", "Reports", "Admin", "Reset Password", "Delete Account"])

# -------------------- Admin Credentials --------------------
ADMIN_EMAIL = "jainsarthak.7502@gmail.com"    # <-- Set your admin email here
ADMIN_PASSWORD = "123456"          # <-- Set your admin password here

# -------------------- Helper Functions --------------------
def analyze_sentiment(text):
    """Analyze sentiment using VADER with enhanced categories"""
    analyzer = SentimentIntensityAnalyzer()
    score = analyzer.polarity_scores(text)
    compound = score['compound']
    if compound >= 0.7:
        return "Very Positive"
    elif compound >= 0.05:
        return "Positive"
    elif compound <= -0.7:
        return "Very Negative"
    elif compound <= -0.05:
        return "Negative"
    else:
        return "Neutral"

def generate_report(data):
    """Generate a downloadable CSV report"""
    df = pd.DataFrame(data)
    towrite = io.BytesIO()
    df.to_csv(towrite, index=False)
    towrite.seek(0)
    return towrite

def refresh_token():
    """Refresh Firebase authentication token if expired"""
    if "user" in st.session_state and st.session_state["user"]:
        try:
            new_token = auth.refresh(st.session_state["user"]["refreshToken"])
            st.session_state["user"]["idToken"] = new_token["idToken"]
            return st.session_state["user"]["idToken"]
        except Exception:
            st.session_state["user"] = None
            st.warning("Session expired. Please log in again.")
            st.rerun()

def generate_wordcloud(texts):
    """Generate a word cloud from a list of texts"""
    text = " ".join(texts)
    wordcloud = WordCloud(width=800, height=400, background_color="white").generate(text)
    plt.figure(figsize=(8, 6))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    st.pyplot(plt)

# Initialize sentiment analysis pipeline for text
text_analyzer = pipeline("sentiment-analysis")

# Initialize image classification pipeline
image_analyzer = pipeline("image-classification")

def analyze_text_sentiment(text):
    """Analyze sentiment using Hugging Face pipeline"""
    result = text_analyzer(text)[0]
    return result['label']

def analyze_image_sentiment(image_url):
    """Analyze sentiment of an image using Hugging Face pipeline"""
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    result = image_analyzer(img)[0]
    return result['label']

# -------------------- Authentication Functions --------------------
def is_strong_password(password):
    """Check if the password is strong"""
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True

def login():
    """User Login Page"""
    st.title("Login to Dashboard")
    email = st.text_input("Enter Email")
    password = st.text_input("Enter Password", type="password")

    if st.button("Login"):
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            user_info = auth.get_account_info(user['idToken'])
            local_id = user_info['users'][0]['localId']

            # Check if admin
            if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
                st.session_state["user"] = {"idToken": user['idToken'], "refreshToken": user['refreshToken'], "localId": local_id, "is_admin": True}
                st.success("Admin Login Successful! Redirecting...")
            else:
                st.session_state["user"] = {"idToken": user['idToken'], "refreshToken": user['refreshToken'], "localId": local_id, "is_admin": False}
                st.success("Login Successful! Redirecting...")
            
            time.sleep(1.5)
            st.rerun()

        except Exception as e:
            error_message = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_json = e.response.json()
                    error_message = error_json.get('error', {}).get('message', str(e))
                except ValueError:
                    pass
            st.error(f"Invalid Credentials! {error_message}")

def signup():
    """User Signup Page"""
    st.title("Create an Account")
    email = st.text_input("Enter Email")
    password = st.text_input("Create Password", type="password")

    if st.button("Signup"):
        if not is_strong_password(password):
            st.error("Password must be at least 8 characters long, contain an uppercase letter, a lowercase letter, a number, and a special character.")
            return

        try:
            auth.create_user_with_email_and_password(email, password)
            st.success("Account Created! You can now log in.")
        except Exception as e:
            st.error(f"Error Creating Account: {e}")

def reset_password():
    """Reset Password Page"""
    st.title("Reset Your Password")
    email = st.text_input("Enter Your Registered Email")

    if st.button("Send Reset Link"):
        try:
            auth.send_password_reset_email(email)
            st.success("Password reset email sent! Check your inbox.")
        except Exception as e:
            st.error(f"Error Sending Email: {e}")

def delete_account():
    """Delete User Account"""
    if not st.session_state["user"]:
        st.warning("Please log in to delete your account.")
        return

    user_id = st.session_state["user"]["localId"]
    email = auth.get_account_info(st.session_state["user"]["idToken"])['users'][0]['email']

    if email == ADMIN_EMAIL:
        st.warning("Admin account cannot be deleted.")
        return

    st.title("Delete Account")
    st.warning("This action is irreversible. All your data will be permanently deleted.")

    if st.button("Delete My Account"):
        try:
            idToken = refresh_token()
            auth.delete_user_account(idToken)
            db.child("users").child(user_id).remove(token=idToken)
            st.session_state["user"] = None
            st.success("Account deleted successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error deleting account: {e}")

# -------------------- User Dashboard --------------------
def user_dashboard():
    """Personalized User Dashboard"""
    if not st.session_state["user"]:
        st.warning("Please log in to access the dashboard.")
        return

    st.title("User Dashboard")
    user_id = st.session_state["user"]["localId"]

    try:
        idToken = refresh_token()
        user_data = db.child("users").child(user_id).child("sentiment_results").get(token=idToken).val()

        if user_data:
            st.subheader("Your Sentiment Analysis History")
            data = [{"Text": entry.get("text", ""), "Sentiment": entry.get("sentiment", ""), "Key": key} for key, entry in user_data.items()]
            df = pd.DataFrame(data)

            st.dataframe(df)

            st.subheader("Sentiment Distribution")
            fig = px.histogram(df, x="Sentiment", color="Sentiment", text_auto=True)
            st.plotly_chart(fig)

            st.subheader("Word Cloud of Analyzed Texts")
            generate_wordcloud(df["Text"].tolist())
        else:
            st.info("No analysis history found.")
    except Exception as e:
        st.error(f"Error fetching user data: {e}")

# -------------------- Sentiment Analysis --------------------
def sentiment_analysis():
    """Sentiment Analysis Page"""
    if not st.session_state["user"]:
        st.warning("Please log in to access Sentiment Analysis.")
        return

    st.title("AI Content Sentiment Analysis")
    user_id = st.session_state["user"]["localId"]

    st.subheader("Text Sentiment Analysis")
    user_text = st.text_area("Enter text to analyze:")
    if st.button("Analyze Text"):
        if user_text:
            result = analyze_text_sentiment(user_text)
            st.write(f"**Sentiment:** {result}")

            try:
                idToken = refresh_token()
                db.child("users").child(user_id).child("sentiment_results").push({"text": user_text, "sentiment": result}, token=idToken)
                st.success("Sentiment saved successfully!")
            except Exception as e:
                st.error(f"Error saving data: {e}")
        else:
            st.warning("Please enter some text.")

    st.subheader("Image Sentiment Analysis")
    image_url = st.text_input("Enter image URL to analyze:")
    if st.button("Analyze Image"):
        if image_url:
            result = analyze_image_sentiment(image_url)
            st.write(f"**Sentiment:** {result}")

            try:
                idToken = refresh_token()
                db.child("users").child(user_id).child("sentiment_results").push({"image_url": image_url, "sentiment": result}, token=idToken)
                st.success("Sentiment saved successfully!")
            except Exception as e:
                st.error(f"Error saving data: {e}")
        else:
            st.warning("Please enter an image URL.")

    st.subheader("Upload a File for Bulk Sentiment Analysis")
    uploaded_file = st.file_uploader("Upload a file (.txt, .csv, .xlsx)", type=["txt", "csv", "xlsx"])
    if uploaded_file is not None:
        file_extension = uploaded_file.name.split(".")[-1]
        try:
            if file_extension == "txt":
                text = uploaded_file.read().decode("utf-8")
                result = analyze_sentiment(text)
                st.write(f"**Sentiment:** {result}")
            elif file_extension == "csv":
                df = pd.read_csv(uploaded_file)
            elif file_extension == "xlsx":
                df = pd.read_excel(uploaded_file)
            else:
                st.warning("Unsupported file format.")
                return

            if "text" not in df.columns:
                st.warning("Uploaded file does not have a 'text' column.")
                st.write("Please specify which column should be used as the 'text' column.")
                column_name = st.selectbox("Select column", df.columns)
                if st.button("Set as Text Column"):
                    df["text"] = df[column_name]

            if "text" in df.columns:
                df["Sentiment"] = df["text"].apply(analyze_sentiment)
                st.dataframe(df)
            else:
                st.warning("Uploaded file must have a 'text' column.")
        except Exception as e:
            st.error(f"Error processing file: {e}")

    st.subheader("Your Sentiment Analysis History")
    try:
        idToken = refresh_token()
        sentiment_data = db.child("users").child(user_id).child("sentiment_results").get(token=idToken).val()

        if sentiment_data:
            data = [{"Text": entry.get("text", ""), "Sentiment": entry.get("sentiment", ""), "Key": key} for key, entry in sentiment_data.items()]

            for entry in data:
                col1, col2 = st.columns([0.9, 0.1])
                col1.write(f"**Text:** {entry['Text']}\n**Sentiment:** {entry['Sentiment']}")
                if col2.button("❌", key=entry["Key"]):
                    db.child("users").child(user_id).child("sentiment_results").child(entry["Key"]).remove(token=idToken)
                    st.success("Entry deleted!")
                    st.rerun()

            if st.button("Clear All History"):
                db.child("users").child(user_id).child("sentiment_results").remove(token=idToken)
                st.success("All entries cleared!")
                st.rerun()
        else:
            st.info("No sentiment analysis history found.")
    except Exception as e:
        st.error(f"Error fetching history: {e}")

# -------------------- Reports Page --------------------
def reports():
    """Reports Page with Enhanced Charts"""
    st.title("Download Sentiment Report")

    if not st.session_state["user"]:
        st.warning("Please log in to access Reports.")
        return

    try:
        user_id = st.session_state["user"]["localId"]
        idToken = refresh_token()
        sentiment_data = db.child("users").child(user_id).child("sentiment_results").get(token=idToken).val()

        if sentiment_data:
            data = [{"Text": entry.get("text", ""), "Sentiment": entry.get("sentiment", "")} for entry in sentiment_data.values()]
            df = pd.DataFrame(data)
            st.dataframe(df)

            st.subheader("Sentiment Pie Chart")
            fig_pie = px.pie(df, names="Sentiment", title="Sentiment Breakdown", color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig_pie)

            st.subheader("Sentiment Over Time (Line Chart)")
            df['Index'] = range(1, len(df) + 1)
            fig_line = go.Figure(go.Scatter(x=df['Index'], y=df['Sentiment'], mode='markers+lines', marker=dict(size=10)))
            st.plotly_chart(fig_line)

            st.subheader("Sentiment Bar Chart")
            fig_bar = px.bar(df, x="Sentiment", title="Sentiment Bar Chart", color="Sentiment", text_auto=True)
            st.plotly_chart(fig_bar)

            st.subheader("Sentiment Scatter Plot")
            fig_scatter = px.scatter(df, x="Index", y="Sentiment", title="Sentiment Scatter Plot", color="Sentiment")
            st.plotly_chart(fig_scatter)

            st.subheader("Sentiment Box Plot")
            fig_box = px.box(df, y="Sentiment", title="Sentiment Box Plot", color="Sentiment")
            st.plotly_chart(fig_box)

            st.subheader("Word Cloud of Analyzed Texts")
            generate_wordcloud(df["Text"].tolist())

            # Save charts as images
            fig_pie.write_image("pie_chart.png")
            fig_line.write_image("line_chart.png")
            fig_bar.write_image("bar_chart.png")
            fig_scatter.write_image("scatter_plot.png")
            fig_box.write_image("box_plot.png")
            wordcloud_path = "wordcloud.png"
            plt.savefig(wordcloud_path)

            # Generate summary
            summary = f"Total Entries: {len(df)}\n"
            summary += df["Sentiment"].value_counts().to_string()

            st.subheader("Download Report")
            if st.button("Generate Report"):
                csv = generate_report(data)
                st.download_button("Download CSV", csv, "sentiment_report.csv", "text/csv")
        else:
            st.info("No reports available. Perform some sentiment analysis first.")
    except Exception as e:
        st.error(f"Error fetching data: {e}")

# -------------------- Admin Dashboard --------------------
def admin_dashboard():
    """Admin Dashboard with user management"""
    if not st.session_state["user"] or not st.session_state["user"].get("is_admin"):
        st.warning("Admin access required.")
        return

    st.title("Admin Dashboard")
    st.subheader("User Management")

    try:
        idToken = refresh_token()
        users_data = db.child("users").get(token=idToken).val()

        if users_data:
            total_users = len(users_data)
            total_analyses = sum(len(user.get("sentiment_results", {})) for user in users_data.values())

            st.write(f"**Total Users:** {total_users}")
            st.write(f"**Total Sentiment Analyses:** {total_analyses}")

            st.subheader("User List")
            for user_id, user_info in users_data.items():
                st.write(f"User ID: {user_id}")
                sentiments = user_info.get("sentiment_results", {})
                st.write(f"Total Sentiment Entries: {len(sentiments)}")

                if sentiments:
                    df = pd.DataFrame([{"Text": entry.get("text", ""), "Sentiment": entry.get("sentiment", "")} for entry in sentiments.values()])
                    st.dataframe(df)

                if st.button("Delete User Data", key=user_id):
                    db.child("users").child(user_id).remove(token=idToken)
                    st.success("User data deleted!")
                    st.rerun()

            if st.button("Clear All User Data"):
                db.child("users").remove(token=idToken)
                st.success("All user data cleared!")
                st.rerun()

        else:
            st.info("No user data available.")

    except Exception as e:
        st.error(f"Error fetching admin data: {e}")

# -------------------- Main Dashboard Pages --------------------
if "user" not in st.session_state:
    st.session_state["user"] = None

if menu == "Home":
    st.title("Welcome to AI Sentiment Analysis Dashboard")
    st.write("Analyze sentiment in text, generate visual reports, and download your analysis.")

elif menu == "Login":
    login()

elif menu == "Signup":
    signup()

elif menu == "Reset Password":
    reset_password()

elif menu == "Dashboard":
    user_dashboard()

elif menu == "Sentiment Analysis":
    sentiment_analysis()

elif menu == "Reports":
    reports()

elif menu == "Admin":
    admin_dashboard()

elif menu == "Delete Account":
    delete_account()

# -------------------- Logout Button --------------------
if st.session_state["user"]:
    if st.sidebar.button("Logout"):
        st.session_state["user"] = None
        st.rerun()