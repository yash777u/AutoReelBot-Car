import time
import random
from instagrapi import Client
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Supported file extensions
VIDEO_EXTENSIONS = (".mp4", ".mov", ".avi", ".mkv")

SESSION_FILE = "session.json"


def get_current_directory():
    return os.getcwd()


def login(username, password):
    cl = Client()

    # Try to reuse existing session
    if os.path.exists(SESSION_FILE):
        try:
            cl.load_settings(SESSION_FILE)
            cl.login(username, password)
            cl.get_timeline_feed()  # session validation
            print("✅ Session loaded and valid")
            return cl
        except Exception:
            print("⚠️ Session invalid. Re-authenticating...")
            os.remove(SESSION_FILE)

    try:
        cl.login(username, password)
        cl.dump_settings(SESSION_FILE)
        print("🆕 New session created and saved")
        return cl
    except Exception as e:
        print("❌ Login failed:", e)
        return None


def upload_one_random_video_and_exit(client):
    base_path = get_current_directory()
    videos_folder = os.path.join(base_path, "videos")

    if not os.path.exists(videos_folder):
        print("📂 Videos folder not found")
        return

    video_files = [
        f for f in os.listdir(videos_folder) if f.lower().endswith(VIDEO_EXTENSIONS)
    ]

    if not video_files:
        print("📭 No videos available to upload")
        return

    # Cool-off delay AFTER login
    pre_delay = random.randint(20, 40)
    print(f"⏳ Pre-upload cool-off: waiting {pre_delay}s")
    time.sleep(pre_delay)

    video = random.choice(video_files)
    video_path = os.path.join(videos_folder, video)

    try:
        client.video_upload(
            video_path,
            caption="Tags 🏷: #animeedit #animevibes #anime",
        )
        print(f"🎬 Uploaded video: {video}")

        post_delay = random.randint(30, 40)
        print(f"⏳ Post-upload cool-down: {post_delay}s")
        time.sleep(post_delay)

        os.remove(video_path)
        print(f"🗑️ Deleted uploaded video: {video}")

    except Exception as e:
        print(f"❌ Failed to upload video {video}:", e)


def main():
    username = os.getenv("IG_USERNAME")
    password = os.getenv("IG_PASSWORD")

    if not username or not password:
        print("❌ Missing IG_USERNAME or IG_PASSWORD in .env file")
        return

    client = login(username, password)
    if not client:
        return

    upload_one_random_video_and_exit(client)
    print("👋 Task complete. Exiting program.")


if __name__ == "__main__":
    main()
