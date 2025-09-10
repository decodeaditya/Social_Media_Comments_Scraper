import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
from googleapiclient.discovery import build

# --- YouTube ---
import requests
from youtube_comment_downloader import YoutubeCommentDownloader

# --- Instagram ---
import os
from dotenv import load_dotenv
load_dotenv()

youtube_api_key = os.getenv("YOUTUBE_API_KEY")


# --- Polishing Function ---
def polish_message(msg):
    return msg.strip().capitalize()


# --- Scrape YouTube Comments ---
def get_youtube_comments(video_url):
    downloader = YoutubeCommentDownloader()
    comments = []
    
    for comment in downloader.get_comments_from_url(video_url, sort_by=0):
        comments.append({
            "Name": comment["author"],
            "Date": comment["time"],
            "Message": polish_message(comment["text"]),
            "IsReply": comment["reply"],
            "Likes": comment["votes"]
        })
    
    return pd.DataFrame(comments)

def get_youtube_comments_api(video_id, api_key, max_comments=None):    
    youtube = build("youtube", "v3", developerKey=api_key)
    comments = []
    next_page_token = None
    while True:
        request = youtube.commentThreads().list(
            part="snippet,replies",
            videoId=video_id,
            pageToken=next_page_token,
            maxResults=200,  # max per request
            order="time"     # newest first
        )
        response = request.execute()

        for item in response["items"]:
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "Username": snippet["authorDisplayName"],
                "Message": polish_message(snippet["textDisplay"]),
                "Time": pd.to_datetime(snippet["publishedAt"])
            })

        # --- Replies ---
            if "replies" in item:
                for reply in item["replies"]["comments"]:
                    reply_snip = reply["snippet"]
                    comments.append({
                        "ParentID": snippet["authorDisplayName"],  # parent comment author
                        "Username": reply_snip["authorDisplayName"],
                        "Message": "↳ " + polish_message(reply_snip["textDisplay"]),
                        "Time": pd.to_datetime(reply_snip["publishedAt"])
                    })    

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    return pd.DataFrame(comments[:max_comments])


# --- Scrape Instagram Comments (using session file) ---
def get_instagram_comments(post_url, username, password, max_comments=200):
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)

    # Step 1: Login
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(3)

    user_input = driver.find_element(By.NAME, "username")
    pass_input = driver.find_element(By.NAME, "password")
    user_input.send_keys(username)
    pass_input.send_keys(password)
    pass_input.send_keys(Keys.RETURN)
    time.sleep(5)

    # Step 2: Go to post
    driver.get(post_url)
    time.sleep(5)

    # Step 3: Load comments
    comments_data = []
    while len(comments_data) < max_comments:
        try:
            load_more = driver.find_element(By.XPATH, "//button[contains(text(),'Load more comments')]")
            load_more.click()
            time.sleep(2)
        except:
            pass  # No more "Load more comments"

        comment_elements = driver.find_elements(By.XPATH, "//ul[contains(@class,'XQXOT')]/div/li")
        for c in comment_elements:
            try:
                username_el = c.find_element(By.XPATH, ".//h3//a")
                message_el = c.find_element(By.XPATH, ".//span")
                time_el = c.find_element(By.TAG_NAME, "time")
                
                comments_data.append({
                    "Username": username_el.text,
                    "Message": polish_message(message_el.text),
                    "Time": pd.to_datetime(time_el.get_attribute("datetime"))
                })
            except:
                continue

        # Break if reached max_comments
        if len(comments_data) >= max_comments:
            break

    driver.quit()
    return pd.DataFrame(comments_data[:max_comments])


def get_reddit_comments(post_url):
    #Check if URL have .json at the end
    if not post_url.endswith(".json"):
        if post_url[-1] == '/':
            post_url = post_url + ".json"
        else:
            post_url = post_url + "/.json"
    
    headers = {
        "User-Agent": "CommentScraperBot/0.1"
    }

    response = requests.get(post_url, headers=headers)
    data = response.json()

    comments = []

    def extract_comments(children):
        for c in children:
            kind = c.get("kind")
            if kind != "t1":
                continue
            comment_data = c["data"]
            comments.append({
                "Name": comment_data.get("author"),
                "Date": pd.to_datetime(comment_data.get("created_utc"), unit='s'),
                "Message": polish_message(comment_data.get("body"))
            })
            # Recursively get replies
            if comment_data.get("replies"):
                extract_comments(comment_data["replies"]["data"]["children"])
    
    extract_comments(data[1]["data"]["children"])
    return pd.DataFrame(comments)

# --- Main Program ---
def scrape_comments(link):
    if "youtube.com" in link or "youtu.be" in link:
        print("🎥 Detected YouTube link")
        method = input("Choose method - (1) API (2) Web Scraping [1/2]: ")
        if method == "2":
            df = get_youtube_comments(link)
            df.to_csv("youtube_comments.csv", index=False)
            print("✅ Saved YouTube comments to youtube_comments.csv")
        else:
            video_id = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", link).group(1)
            api_key = youtube_api_key
            df = get_youtube_comments_api(video_id, api_key)
            df.to_csv(f"youtube_comments.csv", index=False)
            print("✅ Saved YouTube comments to CSV")

    elif "instagram.com" in link:
        print("📸 Detected Instagram link")
        # extract shortcode from link
        username = input("Enter Instagram username: ")
        password = input("Enter Instagram password: ")
        df = get_instagram_comments(link, username, password)
        df.to_csv("instagram_comments.csv", index=False)
        print("✅ Saved Instagram comments to instagram_comments.csv")

    elif "reddit.com" in link:
        print("👽 Detected Reddit link")
        df = get_reddit_comments(link)
        df.to_csv("reddit_comments.csv", index=False)
        print("✅ Saved Reddit comments to reddit_comments.csv")    

    else:
        print("❌ Unsupported link")


# --- Run ---
if __name__ == "__main__":
    link = input("Enter Post link [Instagram/YouTube/Reddit]: ")
    scrape_comments(link)
