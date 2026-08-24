# SpotTransfer

SpotTransfer is a free, open-source tool for moving Spotify playlists to YouTube Music.

[![](https://star-history.dera.page/svg?repos=Pushan2005/SpotTransfer&type=date&legend=top-left)](https://star-history.dera.page/#Pushan2005/SpotTransfer&type=date&legend=top-left)

### Prerequisites
- Python 3.8+

Clone the repository and install the backend dependencies:

```bash
git clone https://github.com/Pushan2005/SpotTransfer.git
cd SpotTransfer/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

On Windows, activate the virtual environment with `venv\Scripts\activate` instead.

### Get your YouTube Music request headers

1. Open [music.youtube.com](https://music.youtube.com) and sign in to your Google account.
2. Open your browser's developer tools and go to the **Network** tab.
3. Filter the requests for `/browse` and find a successful `POST` request with a `200` status.
    - In Firefox, right-click the request and choose **Copy > Copy Request Headers**.
    - In Chrome or Edge, open the request, go to **Headers**, and copy everything from `accept: */*` to the end of **Request Headers**.
4. Paste the copied request headers into `backend/browser.json` and save the file. Paste them into the file instead of the web-hosted form.

### Run a transfer

1. Open `backend/setup.py` and paste your Spotify playlist link into the variable:

    ```python
    spotify_playlist_link = "https://open.spotify.com/playlist/your-playlist-id"
    ```

2. From the `backend` directory, run:

    ```bash
    python3 selfhost.py
    ```

For a new playlist, change `spotify_playlist_link` in `setup.py` and run `python3 selfhost.py` again. Repeat this for each playlist you want to transfer.

### Authentication issues

If you get an authentication error, delete the contents of `browser.json`, get a fresh set of request headers from YouTube Music, paste them into the file, save it, and run `python3 selfhost.py` again. This usually happens when the browser headers expire.

# Acknowledgements

[Aran404](https://github.com/Aran404/) for SpotAPI

# Legal Notice

> **Disclaimer**: This repository and any associated code are provided "as is" without warranty of any kind, either expressed or implied. The author of this repository does not accept any responsibility for the use or misuse of this repository or its contents. The author does not endorse any actions or consequences arising from the use of this repository. Any copies, forks, or re-uploads made by other users are not the responsibility of the author. The repository is solely intended as a Proof Of Concept for educational purposes regarding the use of a service's private API. By using this repository, you acknowledge that the author makes no claims about the accuracy, legality, or safety of the code and accepts no liability for any issues that may arise. More information can be found [HERE](./LEGAL_NOTICE.md).
