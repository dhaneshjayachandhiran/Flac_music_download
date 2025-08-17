import os
import time
import sys
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import re

# Configuration
# Here u have to choose the download Directory
DOWNLOAD_FOLDER = "/home/dhanesh/Music/Flac_songs"
CSV_LOG = "data/download_log.csv"

# Here past your Playlist link
SPOTIFY_PLAYLIST_URL = "PAST_YOUR_PLAYLIST_HERE"
DOWNLOAD_TIMEOUT = 300
ELEMENT_WAIT_TIMEOUT = 30

# Spotify Auth
'''Here change the client_id and client_secret with your spotify account 
your can get the client_id,key on here "https://developer.spotify.com/dashboard" '''

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id='YOUR_CLIENT_ID_HERE',
    client_secret='YOUR_CLIENT_SECRET_HERE'
))


def normalize_track_name(track_name):
    """Improved normalization that handles more cases"""
    # Remove anything in parentheses/brackets
    track_name = re.sub(r'[\(\[].*?[\)\]]', '', track_name)
    # Remove common prefixes/suffixes
    track_name = re.sub(r'\b(from|feat|ft|vs|remix|mix|version)\b.*', '', track_name, flags=re.IGNORECASE)
    # Remove special characters and extra spaces
    track_name = re.sub(r'[^\w\s]', ' ', track_name)
    track_name = re.sub(r'\s+', ' ', track_name).strip().lower()
    return track_name


def wait_for_download_completion_with_name(directory, timeout, expected_title):
    """
    Improved verification with more flexible matching:
    1. Only requires 2 matching words (or 50% match ratio)
    2. Gives more weight to the main track name words
    3. Better handles common variations
    """
    initial_files = set(os.listdir(directory))
    start_time = time.time()
    normalized_title = normalize_track_name(expected_title)

    # Split into words and identify the most important words (first 2 words)
    title_words = normalized_title.split()
    main_words = title_words[:2] if len(title_words) > 1 else title_words
    valid_extensions = ('.flac', '.mp3', '.m4a', '.wav')

    while time.time() - start_time < timeout:
        current_files = set(os.listdir(directory))
        new_files = current_files - initial_files

        for filename in new_files:
            # Skip temp files and incomplete downloads
            if filename.startswith(('.com.google.Chrome.', '~$')) or filename.endswith(('.crdownload', '.tmp')):
                continue

            if filename.lower().endswith(valid_extensions):
                normalized_file = normalize_track_name(filename)
                file_words = normalized_file.split()

                # Count matches of important words
                main_matches = sum(1 for word in main_words if word in file_words)

                # Special case: if we match at least 2 important words
                if main_matches >= 2:
                    return True

                # Normal case: match at least 50% of words or 2+ words
                total_matches = sum(1 for word in title_words if word in file_words)
                match_ratio = total_matches / len(title_words)

                if total_matches >= 2 or match_ratio >= 0.5:
                    return True
                else:
                    try:
                        os.remove(os.path.join(directory, filename))
                    except Exception as e:
                        pass
                    return False

        time.sleep(1)

    return False


def get_tracks_from_playlist(playlist_url):
    """Fetch tracks from Spotify playlist"""
    try:
        playlist_id = playlist_url.split("/")[-1].split("?")[0]
        results = sp.playlist_tracks(playlist_id)
        tracks = [(item['track']['name'], item['track']['artists'][0]['name'])
                  for item in results['items'] if item.get('track')]

        while results['next']:
            results = sp.next(results)
            tracks.extend([(item['track']['name'], item['track']['artists'][0]['name'])
                           for item in results['items'] if item.get('track')])

        print(f"Found {len(tracks)} tracks in the playlist.")
        return tracks
    except Exception as e:
        print(f"Error fetching tracks: {e}")
        return []


def find_chrome_executable():
    """Find Chrome executable path"""
    candidates = [
        '/usr/bin/google-chrome-stable', '/usr/bin/google-chrome',
        '/opt/google/chrome/google-chrome',
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        'C:/Program Files/Google/Chrome/Application/chrome.exe',
        'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def setup_browser():
    """Setup undetected Chrome browser"""
    chrome_executable_path = find_chrome_executable()
    if not chrome_executable_path:
        print("=" * 50)
        print("[CRITICAL ERROR] Could not find Google Chrome executable.")
        print("Please ensure Google Chrome is installed and in your system PATH.")
        print("=" * 50)
        sys.exit(1)

    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--headless")  # Remove or comment this line if you want to see the browser window
    prefs = {
        "download.default_directory": DOWNLOAD_FOLDER,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True
    }
    options.add_experimental_option("prefs", prefs)

    driver = uc.Chrome(
        browser_executable_path=chrome_executable_path,
        options=options,
        use_subprocess=True
    )
    driver.set_page_load_timeout(60)
    return driver


def download_song(driver, title, artist):
    """Download a single song with improved reliability"""
    search_query = f"{title} {artist}"
    try:
        driver.get("https://us.qobuz.squid.wtf/")
        wait = WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT)
        time.sleep(1)

        # Set filter to Tracks
        filter_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(., 'Albums') or contains(., 'albums')]")
        ))
        filter_button.click()
        time.sleep(0.05)

        tracks_option = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[contains(@role, 'menuitemradio') and contains(., 'Tracks')]")
        ))
        tracks_option.click()
        time.sleep(0.5)

        # Perform search
        search_box = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "input[placeholder*='Search']")
        ))
        search_box.clear()
        search_box.send_keys(search_query[:100])  # Limit to 100 chars
        search_box.send_keys(Keys.RETURN)
        time.sleep(0.5)

        # Check if search results are found
        try:
            track_card = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.group")
            ))
        except:
            return "Failed (Song not found)"

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", track_card)
        time.sleep(1)

        ActionChains(driver).move_to_element(track_card).perform()
        time.sleep(0.7)

        download_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[.//*[contains(@class, 'lucide-download')]]")
        ))
        download_button.click()
        time.sleep(0.5)

        # Verify download
        if wait_for_download_completion_with_name(DOWNLOAD_FOLDER, DOWNLOAD_TIMEOUT, title):
            return "Success"
        return "Failed (Mismatch)"

    except Exception as e:
        return "Failed (Song not found)"


def main():
    """Main execution function"""
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    os.makedirs(os.path.dirname(CSV_LOG), exist_ok=True)

    driver = None
    try:
        print("Checking for existing songs...")
        existing_files = os.listdir(DOWNLOAD_FOLDER)

        driver = setup_browser()
        tracks = get_tracks_from_playlist(SPOTIFY_PLAYLIST_URL)

        if not tracks:
            print("No tracks found. Exiting.")
            return

        failed_songs = []
        total_tracks = len(tracks)
        print("\n--- Starting Downloads ---")

        for i, (title, artist) in enumerate(tracks, 1):
            normalized_title = normalize_track_name(title)
            is_downloaded = any(normalized_title in normalize_track_name(f) for f in existing_files)

            if is_downloaded:
                print(f"⏩ [{i}/{total_tracks}] Skipped: {title[:30]}...")
                continue

            status = download_song(driver, title, artist)

            if status == "Success":
                print(f"✅ [{i}/{total_tracks}] Downloaded: {title[:30]}...")
                existing_files = os.listdir(DOWNLOAD_FOLDER)
            elif status == "Failed (Song not found)":
                print(f"❌ [{i}/{total_tracks}] Song not found: {title[:30]}...")
                failed_songs.append({
                    "title": title,
                    "artist": artist,
                    "status": status,
                    "timestamp": pd.Timestamp.now()
                })
            else:
                print(f"❌ [{i}/{total_tracks}] Failed (Mismatch): {title[:30]}...")
                failed_songs.append({
                    "title": title,
                    "artist": artist,
                    "status": status,
                    "timestamp": pd.Timestamp.now()
                })

        print("\n--- Download Complete ---")
        if failed_songs:
            pd.DataFrame(failed_songs).to_csv(CSV_LOG, index=False)
            print(f"{len(failed_songs)} failures logged to {CSV_LOG}")
        else:
            print("All downloads completed successfully!")

    except Exception as e:
        print(f"\nFatal error: {e}")
    finally:
        if driver:
            driver.quit()
            print("Browser closed")


if __name__ == "__main__":
    main()
