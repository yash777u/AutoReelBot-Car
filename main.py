import os
import random
from dotenv import load_dotenv
from PIL import Image

# Instagram Login
from login import login_user

# --- CONFIGURATION ---
load_dotenv()

# Folders
OUTPUT_DIR = "output"

# Constant Caption
FIXED_CAPTION = """#lamborghini #carsofinstagram #huracan #lambo #lamborghinihuracan
#porsche #carsofinstagram #gt3rs #992gt3rs #porsche911 #bmw #bmwm3 #bmws1000rr #bmwnation
#bmw #bmws1000rr #bmwm #bmwperformance

#bmw #bmws1000rr #bmwnation #bmwm3
#bmw #bmwm3 #f80m3 #snow #carsofinstagram

#bmw #carsofinstagram #bmwfans #bmwm3"""


def ensure_folders():
    """Ensures output folder exists but DOES NOT delete contents."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("📂 Directories verified.")


def generate_simple_thumbnail(video_path):
    """Generate a simple thumbnail using ffmpeg (fast and reliable)."""
    import subprocess

    try:
        print("📸 Generating thumbnail...")
        thumbnail_path = os.path.join(OUTPUT_DIR, "thumbnail.jpg")

        # Use ffmpeg to extract middle frame (fast and doesn't lock file)
        cmd = [
            "ffmpeg",
            "-i",
            video_path,
            "-ss",
            "00:00:01",  # Extract frame at 1 second
            "-vframes",
            "1",  # Only 1 frame
            "-vf",
            "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
            "-q:v",
            "2",  # High quality
            "-y",  # Overwrite
            thumbnail_path,
        ]

        # Run ffmpeg silently
        result = subprocess.run(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10
        )

        if result.returncode == 0 and os.path.exists(thumbnail_path):
            print(f"✅ Thumbnail saved: {thumbnail_path}")
            return thumbnail_path
        else:
            print("⚠️ ffmpeg failed, trying fallback method...")
            return generate_thumbnail_fallback(video_path)

    except FileNotFoundError:
        print("⚠️ ffmpeg not found, using fallback method...")
        return generate_thumbnail_fallback(video_path)
    except Exception as e:
        print(f"⚠️ Thumbnail generation failed: {e}")
        return generate_thumbnail_fallback(video_path)


def generate_thumbnail_fallback(video_path):
    """Fallback: Use moviepy but with proper cleanup."""
    try:
        from moviepy.editor import VideoFileClip
        import gc

        print("📸 Using fallback thumbnail generator...")
        thumbnail_path = os.path.join(OUTPUT_DIR, "thumbnail.jpg")

        # Open video
        video = VideoFileClip(video_path)

        # Get frame at 1 second (or middle if video is shorter)
        frame_time = min(1.0, video.duration / 2)
        frame = video.get_frame(frame_time)

        # Close video IMMEDIATELY to release file
        video.close()
        del video
        gc.collect()

        # Save thumbnail
        img = Image.fromarray(frame)
        img = img.resize((1080, 1920), Image.LANCZOS)
        img.save(thumbnail_path, "JPEG", quality=95)

        print(f"✅ Thumbnail saved (fallback): {thumbnail_path}")
        return thumbnail_path

    except Exception as e:
        print(f"⚠️ Fallback thumbnail failed: {e}")
        print("💡 Uploading without custom thumbnail (Instagram will generate one)")
        return None


def upload_reel(video_path, caption):
    """Upload reel to Instagram."""
    print("🚀 Connecting to Instagram...")
    cl = login_user()
    if not cl:
        print("❌ Login failed. Video skipped.")
        return False

    # Verify we're actually logged in
    try:
        user = cl.account_info()
        print(f"✅ Logged in as: @{user.username}")
    except Exception as e:
        print(f"❌ Not actually logged in! Error: {e}")
        print("💡 Get fresh INSTA_SESSIONID from browser cookies")
        return False

    print(f"📤 Uploading reel: {os.path.basename(video_path)}")

    # Generate thumbnail
    thumbnail_path = generate_simple_thumbnail(video_path)

    try:
        media = cl.clip_upload(video_path, caption=caption, thumbnail=thumbnail_path)

        # Success
        if media and hasattr(media, "code"):
            print(f"\n🎉 SUCCESS! REEL POSTED!")
            print(f"📱 Code: {media.code}")
            print(f"🔗 URL: https://www.instagram.com/reel/{media.code}/")
            print(f"👀 Profile: https://www.instagram.com/{user.username}/")
            return True
        else:
            print("⚠️ Upload returned but no media code")
            return False

    except Exception as e:
        error_str = str(e)

        # Sometimes instagrapi throws pydantic errors even when upload succeeds
        if "pydantic" in error_str.lower() or "validation" in error_str.lower():
            print("\n✅ Upload likely SUCCEEDED (pydantic parsing error)")
            print(f"👀 Check your profile: https://www.instagram.com/{user.username}/")
            return True  # Treat as success to delete the file

        # Real errors
        print(f"\n❌ UPLOAD FAILED: {error_str}")

        if "login_required" in error_str.lower():
            print("\n💡 FIX: Session expired! Get fresh sessionid from browser")
        elif "challenge" in error_str.lower():
            print("\n💡 FIX: Complete verification in Instagram app")
        elif "spam" in error_str.lower() or "limit" in error_str.lower():
            print("\n💡 FIX: Wait 1-2 hours (posting too fast)")

        return False


def get_video_files():
    """Returns a list of video files in the output directory."""
    if not os.path.exists(OUTPUT_DIR):
        return []

    video_extensions = (".mp4", ".mov", ".mkv", ".avi")
    files = [
        os.path.join(OUTPUT_DIR, f)
        for f in os.listdir(OUTPUT_DIR)
        if f.lower().endswith(video_extensions)
    ]
    return files


# --- MAIN LOOP ---
if __name__ == "__main__":
    try:
        ensure_folders()

        videos = get_video_files()

        if not videos:
            print(f"⚠️ No videos found in '{OUTPUT_DIR}' folder.")
            print("   Please add video files (.mp4, .mov) to the output folder.")
            exit(0)

        print(f"📹 Found {len(videos)} videos in queue.")

        # Pick one random video
        selected_video = random.choice(videos)
        print(f"👉 Selected video: {os.path.basename(selected_video)}")

        # Upload
        success = upload_reel(selected_video, FIXED_CAPTION)

        # Delete if successful
        if success:
            try:
                os.remove(selected_video)
                print(f"🗑️ Deleted uploaded video: {os.path.basename(selected_video)}")
                print("\n✅ UPLOAD COMPLETE - PROGRAM FINISHED")
            except Exception as del_err:
                print(f"⚠️ Failed to delete video: {del_err}")
        else:
            print("⚠️ Video NOT deleted because upload failed.")

        # Exit program after one upload attempt
        print("\n👋 Exiting program...")
        exit(0)

    except KeyboardInterrupt:
        print("\n\n⚠️ Program interrupted by user")
        exit(0)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        exit(1)
