import streamlit as st
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from openai import OpenAI
import os
import requests
import urllib.parse
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
import csv                     # NEW: To save data to a file
from datetime import datetime  # NEW: To know WHEN they left the review
import pandas as pd            # NEW: To read the data into a beautiful table

# Load hidden variables
load_dotenv()

# Gather API Keys
GEMINI_KEYS = [
    os.getenv("GEMINI_KEY_1"),
    os.getenv("GEMINI_KEY_2"),
    os.getenv("GEMINI_KEY_3"),
    os.getenv("GEMINI_KEY_4")
]
GEMINI_KEYS = [k for k in GEMINI_KEYS if k is not None]
GROQ_KEY = os.getenv("GROQ_API_KEY")

CANDID_SYSTEM_PROMPT = """
You are Candid. Answer the user's prompt thoroughly and provide detailed information. 
CRITICAL INSTRUCTION: You must NEVER remove the detailed content, but you must ALWAYS end your response with a section titled '**Conclusion**'. 
In this 1-2 sentence conclusion, provide a direct, tailored recommendation based on use-cases. 
"""

def get_candid_answer(user_message):
    for i, current_key in enumerate(GEMINI_KEYS):
        try:
            genai.configure(api_key=current_key)
            model = genai.GenerativeModel(
                model_name='gemini-2.5-flash', 
                system_instruction=CANDID_SYSTEM_PROMPT
            )
            response = model.generate_content(user_message)
            return response.text  
            
        except ResourceExhausted:
            st.toast(f"Gemini Key {i+1} out of quota. Switching...")
            continue 
        except Exception as e:
            st.toast(f"Error with Gemini Key {i+1}: {e}")
            continue

    if GROQ_KEY:
        try:
            st.toast("Falling back to Groq...")
            client = OpenAI(api_key=GROQ_KEY, base_url="https://api.groq.com/openai/v1")
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": CANDID_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: Groq fallback failed. Details: {e}"

    return "System Error: All API keys have run out of quota!"

def get_optimized_query(user_message):
    try:
        genai.configure(api_key=GEMINI_KEYS[0])
        optimizer_model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"Convert this user question into a highly optimized, 4-to-6 word search engine query. Focus only on the core entities and topics. Return ONLY the keywords, no punctuation, no extra text. Question: '{user_message}'"
        response = optimizer_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return user_message

def smart_research(query):
    optimized_query = get_optimized_query(query)
    st.toast(f"🤖 Candid optimized your search to: '{optimized_query}'")
    
    try:
        safe_query = urllib.parse.quote(query)
        search_url = f"https://hn.algolia.com/api/v1/search?query={safe_query}&hitsPerPage=5"
        response = requests.get(search_url)
        hits = response.json().get("hits", [])
        
        if hits:
            stories_data = []
            for hit in hits:
                title = hit.get("title", "No Title")
                url = hit.get("url", hit.get("story_url", "#"))
                stories_data.append(f"- [{title}]({url})")
            return "HACKER_NEWS", "\n".join(stories_data)
    except Exception as e:
        pass 

    try:
        rss_query = urllib.parse.quote(optimized_query)
        rss_url = f"https://news.google.com/rss/search?q={rss_query}&hl=en-IN&gl=IN&ceid=IN:en"
        response = requests.get(rss_url)
        root = ET.fromstring(response.content)
        items = root.findall('.//channel/item')[:5]
        
        if items:
            web_data = []
            for item in items:
                title = item.find('title').text
                link = item.find('link').text
                pub_date = item.find('pubDate').text
                web_data.append(f"- [{title}]({link}) (Published: {pub_date})")
                
            return "GOOGLE_NEWS", "\n".join(web_data)
        else:
            return "NO_RESULTS", f"Google News found 0 articles for '{optimized_query}'."
            
    except Exception as e:
        return "ERROR", f"News search completely failed: {str(e)}"


# --- STREAMLIT FRONTEND UI ---
st.set_page_config(page_title="Candid AI & Smart Research", page_icon="🤖", layout="centered")

# FEEDBACK SIDEBAR
with st.sidebar:
    st.header("📝 Help Us Improve")
    st.write("We want to make Candid the best AI agent possible. Leave your thoughts below!")
    
    with st.form("feedback_form", clear_on_submit=True): # clear_on_submit empties the boxes after hitting send!
        user_name = st.text_input("What is your name?")
        user_review = st.text_area("How is your experience with Candid so far?")
        user_improvements = st.text_area("What features should we add or improve?")
        
        submitted = st.form_submit_button("Submit Feedback")
        
        if submitted:
            if user_name and (user_review or user_improvements):
                # 1. Get the exact date and time
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # 2. Open the CSV file (mode='a' means 'append' to the end of the file)
                with open('feedback_database.csv', mode='a', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    # Write the new row of data
                    writer.writerow([timestamp, user_name, user_review, user_improvements])
                
                st.success(f"Thank you so much, {user_name}! We have received your feedback.")
            else:
                st.warning("Please provide your name and some feedback before submitting.")
                
    st.divider()
    
    # --- THE SECRET CREATOR DASHBOARD ---
    st.write("🔒 **Creator Access**")
    # type="password" hides what you are typing with dots
    admin_pass = st.text_input("Enter Password", type="password") 
    
    # Change "candid123" to whatever secret password you want!
    if admin_pass == "candid123": 
        st.success("Access Granted. Welcome Creator.")
        
        # Check if the file actually exists yet
        if os.path.exists('feedback_database.csv'):
            # Read the CSV file into a Pandas DataFrame
            df = pd.read_csv('feedback_database.csv', names=['Date', 'Name', 'Review', 'Improvements'])
            # Display it as an interactive table!
            st.dataframe(df)
            
            # Add a button so you can download the data as an Excel/CSV file if you want
            with open('feedback_database.csv', 'rb') as f:
                st.download_button('Download Database', f, file_name='candid_feedback.csv')
        else:
            st.info("No feedback has been submitted yet.")


# --- MAIN PAGE CONTENT ---
st.title("🤖 Talk to Candid")
st.write("Ask a question, or have Candid research the internet for real-time answers.")

user_message = st.text_area("What topic do you want to ask about or research?", height=100)

col1, col2 = st.columns(2)

with col1:
    ask_clicked = st.button("💬 Ask Candid Directly", use_container_width=True)

with col2:
    research_clicked = st.button("🔍 Smart Research (Web/News)", use_container_width=True)

st.divider() 

if ask_clicked:
    if user_message:
        with st.spinner("Candid is thinking..."):
            final_answer = get_candid_answer(user_message)
            st.success("Here is Candid's Answer:")
            st.markdown(final_answer)
    else:
        st.warning("Please type a message first!")

elif research_clicked:
    if user_message:
        with st.spinner(f"Researching '{user_message}' across the web..."):
            source_type, research_data = smart_research(user_message)
            
            if source_type in ["ERROR", "NO_RESULTS"]:
                st.error(research_data)
            else:
                if source_type == "HACKER_NEWS":
                    st.info(f"**Data sourced from Hacker News:**\n{research_data}")
                    prompt_context = "tech community on Hacker News"
                else:
                    st.info(f"**Data sourced from Google News:**\n{research_data}")
                    prompt_context = "current news articles"
                
                review_prompt = f"The user asked about: '{user_message}'. Based ONLY on these top live search results I found, give a detailed review of what the {prompt_context} is saying about this right now. Here is the raw data:\n\n{research_data}"
                
                with st.spinner("Candid is analyzing the live data..."):
                    final_answer = get_candid_answer(review_prompt)
                    st.success("Research Review Complete:")
                    st.markdown(final_answer)
    else:
        st.warning("Please type a topic to search for first!")
