# SpotTransfer

SpotTransfer is a free, open-source tool for moving Spotify playlists to YouTube Music.

[![](https://star-history.dera.page/svg?repos=Pushan2005/SpotTransfer&type=date&legend=top-left)](https://star-history.dera.page/#Pushan2005/SpotTransfer&type=date&legend=top-left)

This repo holds the self-hosted desktop client (`apps/desktop`, plain Python)
and the web frontend (`apps/web`).

### Quick start

You need Git and Python 3.8+ installed (on Debian/Ubuntu you may also need
`sudo apt install python3-tk`).

1.  (a) Copy and Paste this into your terminal and run:

    ```bash
    git clone https://github.com/Pushan2005/SpotTransfer.git
    cd SpotTransfer/apps/desktop
    python main.py
    ```

1.  (b) If you don't have Git, download the ZIP and run the commands below in the
    extracted folder instead:

        ```bash
        cd apps/desktop
        python main.py
        ```

1.  Open [music.youtube.com](https://music.youtube.com) and sign in to your Google account.
1.  Open your browser's developer tools and go to the **Network** tab.
1.  Filter the requests for `/browse` and find a successful `POST` request with a `200` status.
    - In Firefox, right-click the request and choose **Copy > Copy Request Headers**.
    - In Chrome or Edge, open the request, go to **Headers**, and copy everything from `accept: */*` to the end of **Request Headers**.
1.  Paste the copied request headers into the app's headers box.
1.  Paste your Spotify playlist link and click on `Clone Playlist`

### Authentication issues

The YouTube Music request headers expire periodically, which is most noticeable on large playlists. When that happens the script pauses the transfer, saves its progress to `apps/desktop/transfer_progress.json`, and tells you what to do:

1. Get a fresh set of request headers from YouTube Music.
2. Paste the fresh headers into the headers box.
3. Click "Clone Playlist" again. The app resumes from where it left off.

**Starting a transfer for a different playlist automatically discards any saved progress of the previous one.**

### Reporting errors

If the desktop app fails, send `apps/desktop/logs/spottransfer.log`. If numbered backup logs are present, send the entire `apps/desktop/logs` folder.

# Acknowledgements

[Aran404](https://github.com/Aran404/) for SpotAPI

# Legal Notice

> **Disclaimer**: This repository and any associated code are provided "as is" without warranty of any kind, either expressed or implied. The author of this repository does not accept any responsibility for the use or misuse of this repository or its contents. The author does not endorse any actions or consequences arising from the use of this repository. Any copies, forks, or re-uploads made by other users are not the responsibility of the author. The repository is solely intended as a Proof Of Concept for educational purposes regarding the use of a service's private API. By using this repository, you acknowledge that the author makes no claims about the accuracy, legality, or safety of the code and accepts no liability for any issues that may arise. More information can be found [HERE](./LEGAL_NOTICE.md).
