import os
from dotenv import load_dotenv
from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired,
    ChallengeRequired,
    TwoFactorRequired,
    BadPassword,
)

load_dotenv()
USERNAME = os.getenv("INSTA_USERNAME")
PASSWORD = os.getenv("INSTA_PASSWORD")
MANUAL_SESSION_ID = os.getenv("INSTA_SESSIONID")  # Add this to your .env


def login_user():
    cl = Client()
    session_file = "session.json"

    # 1. Try Loading Session File
    if os.path.exists(session_file):
        try:
            cl.load_settings(session_file)
            cl.login(USERNAME, PASSWORD)
            print(f"✅ Session Valid! Logged in as: {cl.account_info().username}")
            return cl
        except Exception as e:
            print(f"⚠️ Session invalid: {e}. Re-authenticating...")
            # Clear corrupted session file
            try:
                os.remove(session_file)
                print("🗑️ Cleared corrupted session file.")
            except:
                pass

    # 2. Try Manual Session ID (Bypasses Password Block)
    if MANUAL_SESSION_ID:
        print("🍪 Using Session ID from .env...")
        try:
            cl.login_by_sessionid(MANUAL_SESSION_ID)
            cl.dump_settings(session_file)
            print("✅ Logged in via Session ID!")
            return cl
        except Exception as e:
            print(f"❌ Session ID failed: {e}")
            print("💡 Get a fresh session ID from Instagram cookies in browser.")

    # 3. Fallback to Password
    print(f"🔐 Logging in with password...")
    try:
        cl.login(USERNAME, PASSWORD)
        # VERIFY login actually worked
        try:
            user_info = cl.account_info()
            print(f"✅ Password login successful! User: {user_info.username}")
            cl.dump_settings(session_file)
            return cl
        except Exception as verify_error:
            print(f"❌ Login succeeded but account access failed: {verify_error}")
            return None
    except TwoFactorRequired:
        print("📱 2FA Required!")
        code = input("Enter 2FA Code: ")
        cl.two_factor_login(code)
        cl.dump_settings(session_file)
        print("✅ 2FA login successful!")
        return cl
    except Exception as e:
        print(f"❌ Login Error: {e}")
        print("💡 Try these fixes:")
        print("   1. Get fresh session ID from Instagram cookies (Chrome DevTools)")
        print("   2. Check if password is correct")
        print("   3. Instagram might be blocking automation - wait 1 hour")
        return None


if __name__ == "__main__":
    login_user()
