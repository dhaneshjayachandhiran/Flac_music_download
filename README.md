# Spotify Playlist to FLAC Downloader 🎵

A Python script that automatically downloads all songs from a Spotify playlist in high-quality FLAC format.

This script automates downloads from the [**us.qobuz.squid.wtf**](https://us.qobuz.squid.wtf/) website. While you can visit the site to download single songs manually, this tool is designed to save you hours of work by automatically downloading entire Spotify playlists. It reads your playlist, finds each song on the website, and downloads it for you, making it perfect for bulk downloading.

---
## Features ✨

* **Full Playlist Support**: Fetches every song from any public Spotify playlist, even those with hundreds of tracks.
* **High-Quality Downloads**: Saves songs in the FLAC format for the best audio quality.
* **Smart Duplicate Skipping**: Automatically checks your music folder and skips songs you've already downloaded to save time.
* **Failure Logging**: If any song fails to download, it's automatically recorded in a `download_log.csv` file.
* **Headless Mode**: Can run completely in the background without a visible browser window.

---
## Requirements 📋

Before you begin, you need two things installed on your computer:

1.  **Python 3**: The programming language the script is written in.
2.  **Google Chrome**: The web browser the script will automate.

---
## ⚙️ Setup and Installation Guide

Follow these steps carefully to get the script running on your own computer.

### Step 1: Download the Code

* On this GitHub page, click the green **`< > Code`** button.
* Select **"Download ZIP"**.
* Unzip the downloaded file to a location you can easily find, like your Desktop.

### Step 2: Open a Command Window (Terminal)

You need to open a command window to install the required tools.
* **On Windows**: Click the Start menu and type `cmd` or `powershell`, then press Enter.
* **On macOS**: Open Launchpad and search for `Terminal`.
* **On Linux (Pop!_OS)**: Press the Super key (Windows key) and type `Terminal`, then press Enter.

### Step 3: Navigate to the Project Folder

In the terminal you just opened, you need to move into the folder you unzipped. Use the `cd` (change directory) command. For example, if the folder is on your Desktop, you would type:

```bash
cd Desktop/project-folder-name
```
*(Replace `project-folder-name` with the actual name of the unzipped folder).*

### Step 4: Install Required Libraries

This script depends on a few helper tools. You can install all of them with one simple command. Make sure you are in the project folder in your terminal and type:

```bash
pip install -r requirements.txt
```
*(This command reads the `requirements.txt` file and automatically installs all the listed libraries).*

---
## 🚀 Configuration and Running the Script

You need to edit one file to tell the script where to save music and which playlist to use.

### Step 1: Get Your Spotify API Keys

To allow the script to read your playlist, you need special "keys" from Spotify.

1.  Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications) and log in.
2.  Click "**Create App**".
3.  Give your app any **Name** and **Description** (e.g., "My Music Downloader") and check the boxes to agree to the terms.
4.  Once created, you will see your **Client ID** and a button to "**Show client secret**". You will need both of these.

### Step 2: Edit the Python Script

Open the main Python script file (e.g., `downloader.py`) in a text editor. You need to change the following lines at the top:

```python
# Here u have to choose the download Directory
DOWNLOAD_FOLDER = "/home/your_user_name/Music/Flac_songs"

# Here past your Playlist link
SPOTIFY_PLAYLIST_URL = "[https://open.spotify.com/playlist/YOUR_PLAYLIST_ID_HERE](https://open.spotify.com/playlist/YOUR_PLAYLIST_ID_HERE)"

# --- Spotify Auth ---
# Copy your keys from the Spotify Developer Dashboard here
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id='YOUR_CLIENT_ID_HERE',
    client_secret='YOUR_CLIENT_SECRET_HERE'
))
```

* Update `DOWNLOAD_FOLDER` to the path where you want your music saved.
* Update `SPOTIFY_PLAYLIST_URL` with the link to your playlist.
* Replace `YOUR_CLIENT_ID_HERE` and `YOUR_CLIENT_SECRET_HERE` with the keys you got from Spotify.

### Step 3: Run the Script!

Go back to your terminal (making sure you are still in the project folder) and run the script with this command:

```bash
python your_script_name.py
```
*(Replace `your_script_name.py` with the actual name of the Python file).*

The script will now start working. You'll see status updates directly in your terminal.

---
### Optional: Running in Headless Mode

If you don't want the Chrome browser window to pop up, you can run the script invisibly. Open the Python script and find this line in the `setup_browser` function:

```python
# To run invisibly in the background, uncomment the next line
#options.add_argument("--headless=new")
```
Simply remove the `#` from the beginning of the second line to enable it.

---

Happy Listening! 😊❤️🎶
