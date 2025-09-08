import re
import pandas as pd

# --- YouTube ---
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

    else:
        print("❌ Unsupported link")


# --- Run ---
if __name__ == "__main__":
    link = input("Enter YouTube or Instagram link: ")
    scrape_comments(link)
