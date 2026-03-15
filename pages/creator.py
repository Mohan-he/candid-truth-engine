import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

# Load the environment variables (This works locally and pulls from Cloud Secrets)
load_dotenv()

# Force the page to be FULL SCREEN
st.set_page_config(page_title="Creator Dashboard", page_icon="🔒", layout="wide")

st.title("🔒 Secret Creator Dashboard")
st.write("Enter your credentials to view raw user telemetry and feedback data.")

# Grab the real password from your GitHub/Streamlit Secrets
SECRET_PASSWORD = os.getenv("CREATOR_PASSWORD")

# Safety check
if not SECRET_PASSWORD:
    st.error("System Error: Creator password not configured securely in your environment secrets.")
    st.stop()

# The Password Lock
admin_pass = st.text_input("Enter Creator Password", type="password")

if admin_pass == SECRET_PASSWORD:
    st.success("Access Granted. Welcome back, Creator.")
    st.divider()
    
    # Check if the CSV file exists (This is what we will upgrade to a real DB later!)
    if os.path.exists('feedback_database.csv'):
        # Read the file
        df = pd.read_csv('feedback_database.csv', names=['Date', 'Name', 'Review', 'Improvements'])
        
        # Display it stretching across the full screen width
        st.dataframe(df, use_container_width=True, height=500)
        
        # Download button for backups
        with open('feedback_database.csv', 'rb') as f:
            st.download_button('⬇️ Download Full Database (CSV)', f, file_name='candid_feedback.csv')
    else:
        st.info("No feedback has been submitted to the database yet.")
        
elif admin_pass != "":
    # If they typed something but it's wrong
    st.error("Incorrect Password. Intrusion logged.")
