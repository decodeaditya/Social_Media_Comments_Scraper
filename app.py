import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
from comments import (
    get_youtube_comments, get_youtube_comments_api,
    get_instagram_comments, get_reddit_comments
)

# --- Streamlit Setup ---
st.set_page_config(page_title="Comment Scraper", page_icon="💬", layout="wide")

# --- Branding ---

st.title("💬 Multi-Platform Comment Scraper")
st.write("Scrape and analyze comments from **YouTube, Instagram, and Reddit** 🚀")

st.markdown("---")

# --- Input ---
link = st.text_input("🔗 Enter Post Link (YouTube / Instagram / Reddit):")

df = None

import os
from dotenv import load_dotenv
load_dotenv()

youtube_api_key = os.getenv("YOUTUBE_API_KEY")

if link:
    # Detect platform
    if "youtube.com" in link or "youtu.be" in link:
        st.subheader("🎥 YouTube Options")
        method = st.radio("Choose scraping method:", ["API", "Web Scraping"], horizontal=True)

        if method == "API":
            api_key = youtube_api_key
            if api_key and st.button("🚀 Scrape via YouTube API", use_container_width=True):
                with st.spinner("Fetching comments..."):
                    video_id = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", link).group(1)
                    df = get_youtube_comments_api(video_id, api_key)

        elif method == "Web Scraping":
            if st.button("🚀 Scrape via Web Scraper", use_container_width=True):
                with st.spinner("Fetching comments..."):
                    df = get_youtube_comments(link)

    elif "instagram.com" in link:
        st.subheader("📸 Instagram Options")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if username and password and st.button("🚀 Scrape Instagram", use_container_width=True):
            with st.spinner("Fetching comments..."):
                df = get_instagram_comments(link, username, password)

    elif "reddit.com" in link:
        st.subheader("👽 Reddit Options")
        if st.button("🚀 Scrape Reddit", use_container_width=True):
            with st.spinner("Fetching comments..."):
                df = get_reddit_comments(link)

    else:
        st.error("❌ Unsupported link provided!")

# --- Results ---
if df is not None and not df.empty:
    st.success(f"✅ Scraped {len(df)} comments!")

    # --- Stats Section ---
    st.subheader("📊 Comment Statistics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Comments", len(df))
    with col2:
        st.metric("Unique Users", df['Username'].nunique() if 'Username' in df.columns else "—")
    with col3:
        st.metric("Most Active User", df['Username'].mode()[0] if 'Username' in df.columns else "—")
    with col4:
        avg_len = int(df['Message'].dropna().str.len().mean())
        st.metric("Avg. Comment Length", f"{avg_len} chars")

   
    # --- Data Preview ---
    st.subheader("📜 Preview of Scraped Comments (First 50)")
    st.dataframe(df.head(50), use_container_width=True)

    # --- Download CSV ---
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Full CSV",
        data=csv,
        file_name="comments.csv",
        mime="text/csv",
        use_container_width=True
    )

     # --- Time Distribution ---
    if "Time" in df.columns:
        st.subheader("⏰ Comment Activity Over Time")
        fig, ax = plt.subplots(figsize=(10, 4))
        df["Time"] = pd.to_datetime(df["Time"], errors="coerce")
        df_time = df.dropna(subset=["Time"])
        sns.histplot(df_time["Time"], bins=20, ax=ax, kde=False)
        ax.set_xlabel("Date")
        ax.set_ylabel("Number of Comments")
        st.pyplot(fig)


# --- Footer ---
st.markdown("---")
st.markdown("👨‍💻 Developed by **Aditya** | Desktop-first UI | 📊 Analytics Ready")
