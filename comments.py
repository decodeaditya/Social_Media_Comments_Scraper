import re
import pandas as pd

# --- YouTube ---
import requests
from youtube_comment_downloader import YoutubeCommentDownloader

# --- Instagram ---
import instaloader


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


# --- Scrape Instagram Comments (using session file) ---
def get_instagram_comments(post_shortcode):
    L = instaloader.Instaloader()

    try:
        # load saved session (avoids login problems + 2FA)
        L.load_session_from_file("your_username")
    except:
        # fallback: ask for login once
        username = input("Instagram Username: ")
        password = input("Instagram Password: ")
        L.login(username, password)
        L.save_session_to_file()  # save for next time

    post = instaloader.Post.from_shortcode(L.context, post_shortcode)
    comments = []

    for c in post.get_comments():
        comments.append({
            "Name": c.owner.username,
            "Date": c.created_at_utc,
            "Message": polish_message(c.text)
        })

    return pd.DataFrame(comments)


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
        df = get_youtube_comments(link)
        df.to_csv("youtube_comments.csv", index=False)
        print("✅ Saved YouTube comments to youtube_comments.csv")

    elif "instagram.com" in link:
        print("📸 Detected Instagram link")
        # extract shortcode from link
        shortcode = link.rstrip("/").split("/")[-1]
        df = get_instagram_comments(shortcode)
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
