import streamlit as st
import requests
import google.generativeai as genai
import re # We are importing 're' (Regular Expressions) to clean HTML

# 1. Setup the AI Brain
genai.configure(api_key=st.secrets["AIzaSyDs-3RTFn5ieqqjJS2Lu7sYUW20nomVi90"])
model = genai.GenerativeModel('gemini-2.5-flash')

# 2. Helper tool to strip invisible HTML code from the comments
def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

st.title("🕵️‍♂️ Candid: The Truth Engine")
st.subheader("Bypass SEO spam. Get the brutal, honest consensus from real developers.")

user_query = st.text_input("What do you want to research? (e.g., ChatGPT vs Claude)")

if user_query:
    with st.spinner('Scouring Hacker News comments for the brutal truth...'):
        
        # 3. Search Hacker News directly for COMMENTS
        search_url = f"http://hn.algolia.com/api/v1/search?query={user_query}&tags=comment&hitsPerPage=20"
        response = requests.get(search_url).json()
        
        all_comments = []
        found_stories = set() 
        
        # 4. Extract and CLEAN the comment text
        for hit in response.get('hits', []):
            raw_text = hit.get('comment_text', '') 
            story_title = hit.get('story_title', 'Unknown Thread')
            
            if raw_text:
                # Clean the HTML tags so the AI doesn't get confused
                clean_text = clean_html(raw_text)
                
                # Only keep meaty comments
                if len(clean_text) > 100:
                    all_comments.append(clean_text)
                    if story_title:
                        found_stories.add(story_title)
            
        # --- DEBUG VISUALS: Show the user exactly what we scraped ---
        st.write(f"🛑 **DEBUG: We successfully pulled {len(all_comments)} clean comments.**")
        if len(all_comments) > 0:
            with st.expander("Click here to see the raw data we are feeding the AI"):
                for c in all_comments[:3]: # Show a preview of the first 3
                    st.write(f"- {c}")
        st.markdown("---")
        # -------------------------------------------------------------

        if not all_comments:
            st.error("No deep discussions found on this topic. Try another search.")
        else:
            # 5. Feed the clean, raw comments to Gemini to pick a winner
            raw_data = "\n---\n".join(all_comments)
            prompt = f"""
            You are Candid, an AI that extracts the brutal, honest truth from developer debates.
            A user asked: '{user_query}'.
            Below are the actual comments from Hacker News discussions. 
            Analyze these comments and tell the user WHICH ONE is considered better by the community and WHY. 
            Give a definitive answer based on the consensus. Highlight the main pros/cons, and don't hold back on the criticism.
            
            Raw Comments:
            {raw_data}
            """
            
            ai_consensus = model.generate_content(prompt)
            
            # 6. Display the final result
            st.markdown("### 🔥 The Candid Consensus:")
            st.info(ai_consensus.text)
            
            st.markdown("### 📚 Threads Analyzed:")
            for story in found_stories:
                st.write(f"- {story}")