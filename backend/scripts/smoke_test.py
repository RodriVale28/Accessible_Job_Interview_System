
# Smoke test for the staging deployment of Interview Studio.
import os
import sys
import time
import urllib.error
import urllib.request

BASE_URL = (
    sys.argv[1]
    if len(sys.argv) > 1
    else os.environ.get("STAGING_URL", "")
).rstrip("/")

ATTEMPTS = 6
WAIT_SECONDS = 15
REQUEST_TIMEOUT_SECONDS = 30


def app_is_up():
    """Check that the application responds at its root URL."""
    for attempt in range(1, ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(
                BASE_URL + "/", timeout=REQUEST_TIMEOUT_SECONDS
            ) as response:
                print(f"Step 1 OK: app responded with HTTP {response.status}")
                return True
        except urllib.error.HTTPError as error:
            if error.code < 500:
                print(f"Step 1 OK: app responded with HTTP {error.code}")
                return True
            print(f"Attempt {attempt}: HTTP {error.code}")
        except Exception as error:
            print(f"Attempt {attempt}: {type(error).__name__}: {error}")

        if attempt < ATTEMPTS:
            time.sleep(WAIT_SECONDS)

    return False


def database_is_healthy():
    """Check database connectivity through the application's API."""
    for attempt in range(1, ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(
                BASE_URL + "/health/db",
                timeout=REQUEST_TIMEOUT_SECONDS,
            ) as response:
                if response.status == 200:
                    print("Step 2 OK: database health check passed")
                    return True
                print(f"Attempt {attempt}: HTTP {response.status}")
        except urllib.error.HTTPError as error:
            print(f"Attempt {attempt}: /health/db returned HTTP {error.code}")
        except Exception as error:
            print(f"Attempt {attempt}: {type(error).__name__}: {error}")

        if attempt < ATTEMPTS:
            time.sleep(WAIT_SECONDS)

    return False


if __name__ == "__main__":
    if not BASE_URL:
        sys.exit("Give the staging URL as an argument or set STAGING_URL.")

    app_ok = app_is_up()
    db_ok = database_is_healthy() if app_ok else False

    success = app_ok and db_ok
    print("PASS" if success else "FAIL")
    sys.exit(0 if success else 1)
