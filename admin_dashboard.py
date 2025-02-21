import streamlit as st
from firebase_config import get_all_users, get_user_sentiments, delete_user

def admin_dashboard():
    st.title("Admin Dashboard")

    users = get_all_users()

    if users:
        st.subheader("User Management")
        for user in users:
            user_data = user.val()
            user_id = user.key()
            email = user_data.get("email")

            with st.expander(f"User: {email}"):
                sentiments = get_user_sentiments(user_id)
                st.write("Total Sentiments Analyzed:", len(sentiments))
                st.json(sentiments)

                if st.button(f"Delete {email}", key=user_id):
                    delete_user(user_id)
                    st.success(f"User {email} deleted successfully.")
    else:
        st.info("No users found.")
