# Smoke test for the staging deployment of Interview Studio.
import os
import sys
import time
import urllib.error
import urllib.request


BASE_URL = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("STAGING_URL", "")).rstrip("/") # Staging URL for the app
DATABASE_URL = os.environ.get("DATABASE_URL", "") # Database connection string


# Checks if no URL or database connection string was provided
if not BASE_URL:
    sys.exit("Give the staging URL as an argument or set STAGING_URL.")
if not DATABASE_URL:
    sys.exit("Set DATABASE_URL in your shell (do not write it into this file).")



ATTEMPTS = 6
WAIT_SECONDS = 15

"""Checks if website is up. If the app answers it passes, 
if there is no answer or a 5xx error it fails. 
It retries a few times before giving up."""
def app_is_up():
    for attempt in range(1, ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(BASE_URL + "/", timeout=60) as resp:
                print(f"Step 1 OK: app responded with HTTP {resp.status}")
                return True
        except urllib.error.HTTPError as e:
            if e.code < 500:  # e.g. 404 still means the app is running
                print(f"Step 1 OK: app responded with HTTP {e.code}")
                return True
            print(f"Attempt {attempt}: HTTP {e.code}")
        except Exception as e:
            print(f"Attempt {attempt}: {e}")
        if attempt < ATTEMPTS:
            time.sleep(WAIT_SECONDS)
    return False

"""Checks if the app can read one question from the Supabase database. 
It passes if it can connect to the database and retrieve at least one question. 
It fails if it cannot connect or if the questions table is empty."""
def can_read_one_question():
    try:
        import psycopg2
    except ImportError:
        print("Run: pip install psycopg2-binary")
        return False
    try:
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
        cur = conn.cursor()
        cur.execute("SELECT id FROM questions LIMIT 1")
        row = cur.fetchone()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Step 2 failed: {type(e).__name__}")
        return False
    if row is None:
        print("Step 2 failed: questions table is empty")
        return False
    print("Step 2 OK: read one question from Supabase")
    return True


if __name__ == "__main__":
    ok = app_is_up() and can_read_one_question()
    print("PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)