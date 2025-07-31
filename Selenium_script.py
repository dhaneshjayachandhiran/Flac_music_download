import os
import csv
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

# Here u have to choose the download Directory
DOWNLOAD_FOLDER = "/home/dhanesh/Music/Flac_songs"

CSV_LOG = "data/download_log.csv"

# Here past your Playlist link
SPOTIFY_PLAYLIST_URL = "https://open.spotify.com/playlist/1av9d5kKNZ1mXSL0aysxZu?si=bQJAErHpSQyEzGc6Kxtnag"

# --- TIMEOUTS TO ENSURE WAITING --- #
DOWNLOAD_TIMEOUT = 300
ELEMENT_WAIT_TIMEOUT = 30

# Spotify Auth

'''Here change the client_id and client_secret with your spotify account 
your can get the client_id,key on here "https://developer.spotify.com/dashboard" '''
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id='3ebac30f04b7473ab11da8e3550710ff',
    client_secret='48232116171e44f991d2b66b791a5471'
))


#
## ---------------------------------------------------------------- ##
## Modified Function to Fetch All Songs                             ##
## ---------------------------------------------------------------- ##
#

def get_tracks_from_playlist(playlist_url):
    """Fetch ALL track titles and artists from a Spotify playlist, handling pagination."""
    try:
        playlist_id = playlist_url.split("/")[-1].split("?")[0]

        # 1. Get the first page of tracks
        results = sp.playlist_tracks(playlist_id)
        all_items = results['items']

        # 2. Keep fetching the next page until there are no more pages
        while results['next']:
            results = sp.next(results)
            all_items.extend(results['items'])

        # 3. Process the complete list of tracks
        tracks = []
        for item in all_items:
            track = item.get('track')
            # Ensure track and artists are not None before processing
            if track and track.get('artists'):
                title = track['name']
                artist = track['artists'][0]['name']
                tracks.append((title, artist))

        print(f"Found {len(tracks)} tracks in the Spotify playlist.")
        return tracks
    except Exception as e:
        print(f"Error fetching Spotify playlist tracks: {e}")
        return []


def find_chrome_executable():
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
    chrome_executable_path = find_chrome_executable()

    if not chrome_executable_path:
        print("=" * 50)
        print("[CRITICAL ERROR] Could not find Google Chrome executable.")
        print("Please install Google Chrome or specify the path manually.")
        print("=" * 50)
        sys.exit(1)

    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # To run invisibly in the background, uncomment the next line
    #options.add_argument("--headless=new")

    prefs = {"download.default_directory": DOWNLOAD_FOLDER}
    options.add_experimental_option("prefs", prefs)

    print("Setting up undetected-chromedriver...")
    driver = uc.Chrome(
        browser_executable_path=chrome_executable_path,
        options=options,
        use_subprocess=True
    )
    driver.set_page_load_timeout(60)
    return driver


def wait_for_download_completion(directory, timeout):
    initial_files = set(os.listdir(directory))
    start_time = time.time()
    while time.time() - start_time < timeout:
        current_files = set(os.listdir(directory))
        new_files = current_files - initial_files
        if new_files:
            downloaded_file = new_files.pop()
            if not downloaded_file.endswith(('.crdownload', '.tmp')):
                return True
        time.sleep(0.5)
    return False


def download_song(driver, title, artist):
    """This function uses longer wait times to prevent premature refreshing."""
    search_query = f"{title}, {artist}"
    try:
        driver.get("https://us.qobuz.squid.wtf/")
        wait = WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT)
        time.sleep(0.5)

        filter_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH,
             "//button[./span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'albums')]] | //div[./span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'albums')]]")
        ))
        filter_button.click()
        time.sleep(0.5)

        tracks_option = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@role='menuitemradio' and contains(., 'Tracks')]")
        ))
        if "data-state=\"checked\"" not in tracks_option.get_attribute("outerHTML"):
            tracks_option.click()
            time.sleep(0.05)

        search_box = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[placeholder='Search for anything...']")
        ))
        search_box.clear()
        search_box.send_keys(search_query)
        search_box.send_keys(Keys.RETURN)

        track_card = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div.group")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", track_card)
        time.sleep(0.5)
        ActionChains(driver).move_to_element(track_card).perform()
        time.sleep(0.5)

        download_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[.//*[contains(@class, 'lucide-download')]]")
        ))
        driver.execute_script("arguments[0].click();", download_button)

        if wait_for_download_completion(DOWNLOAD_FOLDER, DOWNLOAD_TIMEOUT):
            return "Success"
        else:
            return "Failed (Timeout)"

    except Exception:
        return "Failed (Error)"


def main():
    """Main execution function with duplicate check and failure-only logging."""
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    if not os.path.exists(os.path.dirname(CSV_LOG)):
        os.makedirs(os.path.dirname(CSV_LOG))

    driver = None
    try:
        print("Checking for already downloaded songs...")
        existing_files = os.listdir(DOWNLOAD_FOLDER)

        driver = setup_browser()
        tracks = get_tracks_from_playlist(SPOTIFY_PLAYLIST_URL)

        if not tracks:
            print("No tracks found or could not fetch playlist. Exiting.")
            return

        failed_songs = []
        total_tracks = len(tracks)
        print("\n--- Starting Downloads ---")

        for i, (title, artist) in enumerate(tracks, 1):

            # --- CORRECTED DUPLICATE CHECK LOGIC ---
            # Create a simpler "core" title for more reliable matching.
            # This handles cases where filenames are cleaned up (e.g., text in parentheses is removed).
            core_title = title
            if ' (' in core_title:
                core_title = core_title.split(' (')[0]
            if ' - ' in core_title:
                core_title = core_title.split(' - ')[0]
            core_title = core_title.strip()

            is_downloaded = False
            for filename in existing_files:
                # Check using the simplified core_title and artist.
                if core_title.lower() in filename.lower() and artist.lower() in filename.lower():
                    is_downloaded = True
                    break

            if is_downloaded:
                final_message = f"⏩ [{i}/{total_tracks}] Skipping '{title}' (Already exists)"
                print(final_message + " " * 10)
                continue
            # ----------------------------------------------------

            processing_message = f"[{i}/{total_tracks}] Processing: {title}..."
            print(processing_message, end='\r')
            status = download_song(driver, title, artist)

            if status == "Success":
                final_message = f"✅ [{i}/{total_tracks}] {title} - {artist}"
                # --- ADD the new file to the list so we don't re-download it in the same session ---
                existing_files.append(f"{title} - {artist}")
            else:
                final_message = f"❌ [{i}/{total_tracks}] {title} - {artist} ({status})"

            print(final_message + " " * 20)

            if status != "Success":
                failed_songs.append({
                    "title": title,
                    "artist": artist,
                    "status": status,
                    "timestamp": pd.Timestamp.now()
                })

        print("-" * 28)

        if failed_songs:
            pd.DataFrame(failed_songs).to_csv(CSV_LOG, index=False)
            print(f"Download Process Complete! Some songs failed.")
            print(f"Log of FAILED downloads saved to: {CSV_LOG}")
        else:
            print("Download Process Complete! All songs were successful or already existed.")

    except Exception as e:
        print(f"\n[CRITICAL SCRIPT ERROR] An unexpected error occurred: {e}")
    finally:
        if driver:
            driver.quit()
            print("Browser closed.")


if __name__ == "__main__":
    main()
