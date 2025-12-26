import { usePlaylist } from "@/context/playlist-context";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Textarea } from "../ui/textarea";
import { FaExclamationCircle } from "react-icons/fa";
import { useState } from "react";

import {
    AlertDialog,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogTrigger,
    AlertDialogFooter,
    AlertDialogAction,
} from "@/components/ui/alert-dialog";
import { FaGithub } from "react-icons/fa";
import { CheckIcon } from "@/components/ui/check.tsx";

export default function InputFields() {
    const [authHeaders, setAuthHeaders] = useState("");
    const [serverOnline, setServerOnline] = useState(false);

    const [isValidUrl, setIsValidUrl] = useState(true);
    const [dialogOpen, setdialogOpen] = useState(false);
    const [connectionDialogOpen, setConnectionDialogOpen] = useState(false);
    const [starPrompt, setStarPrompt] = useState(false);
    const [connectionError, setConnectionError] = useState(false);
    const [errorMessage, setErrorMessage] = useState<React.ReactNode>("");
    const [cloneError, setCloneError] = useState(false);
    const [cloneErrorMessage, setCloneErrorMessage] =
        useState<React.ReactNode>("");
    const [missedTracksDialog, setMissedTracksDialog] = useState(false);
    const [missedTracks, setMissedTracks] = useState<{
        count: number;
        tracks: string[];
    }>({
        count: 0,
        tracks: [],
    });

    const { playlistUrl, setPlaylistUrl } = usePlaylist();

    const validateUrl = (url: string) => {
        const pattern = /^(?:https?:\/\/)?open\.spotify\.com\/playlist\/.+/;
        return pattern.test(url);
    };

    const validateUrls = (urls: string) => {
        if (!urls.trim()) return true;
        const urlList = urls.split('\n').filter(u => u.trim());
        return urlList.every(url => validateUrl(url.trim()));
    };

    const handleUrlChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        const urls = e.target.value;
        setPlaylistUrl(urls);
        setIsValidUrl(validateUrls(urls));
    };

    async function clonePlaylist() {
        const urlList = playlistUrl.split('\n').filter(u => u.trim()).map(u => u.trim());

        const body = {
            playlist_links: urlList,
            auth_headers: authHeaders,
        };

        try {
            setdialogOpen(true);
            const res = await fetch(`${import.meta.env.VITE_API_URL}/create`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(body),
            });
            const data = await res.json();

            if (res.ok) {
                // Collect all missed tracks from all playlists
                let totalMissed = 0;
                let allMissedTracks: string[] = [];

                data.results?.forEach((result: any) => {
                    if (result.status === "success" && result.missed_tracks?.count > 0) {
                        totalMissed += result.missed_tracks.count;
                        allMissedTracks = allMissedTracks.concat(
                            result.missed_tracks.tracks.map(
                                (track: string) => `[${result.playlist_name}] ${track}`
                            )
                        );
                    }
                });

                if (totalMissed > 0) {
                    setMissedTracks({
                        count: totalMissed,
                        tracks: allMissedTracks,
                    });
                    setMissedTracksDialog(true);
                }

                setStarPrompt(true);
            } else if (res.status === 500) {
                setCloneError(true);
                setCloneErrorMessage(
                    <>
                        Server timeout while cloning playlist. Please try again
                        or{" "}
                        <a
                            href="https://github.com/Pushan2005/SpotTransfer/issues/new/choose"
                            className="text-blue-500 hover:underline"
                        >
                            report this issue
                        </a>
                    </>
                );
            } else {
                setCloneError(true);
                setCloneErrorMessage(
                    data.message || "Failed to clone playlist"
                );
            }
        } catch {
            setCloneError(true);
            setCloneErrorMessage("Network error while cloning playlist");
        } finally {
            setdialogOpen(false);
        }
    }

    async function testConnection() {
        setConnectionDialogOpen(true);
        setConnectionError(false);
        setServerOnline(false);

        try {
            const res = await fetch(`${import.meta.env.VITE_API_URL}/`, {
                method: "GET",
                headers: {
                    "Content-Type": "application/json",
                },
            });
            const data = await res.json();
            if (res.ok) {
                setServerOnline(true);
                console.log(data);
            } else if (res.status === 500) {
                setConnectionError(true);
                setErrorMessage(
                    <>
                        Server Error (500). The server likely hit a timeout.
                        Please try again later or{" "}
                        <a
                            href="https://github.com/Pushan2005/SpotTransfer/issues/new/choose"
                            className="text-blue-500 hover:underline"
                        >
                            report this issue on GitHub
                        </a>
                        .
                    </>
                );
            }
        } catch {
            setConnectionError(true);
            setErrorMessage(
                <>
                    Unable to connect to server. If this issue persists, please
                    contact me or{" "}
                    <a
                        href="https://github.com/Pushan2005/SpotTransfer/issues/new/choose"
                        className="text-blue-500 hover:underline"
                    >
                        open an issue on GitHub
                    </a>
                </>
            );
        } finally {
            setConnectionDialogOpen(false);
        }
    }

    return (
        <>
            <div className="w-full flex items-center justify-around">
                <div className="flex flex-col gap-3 items-center justify-center">
                    <div className="space-y-1">
                        <h1 className="text-lg font-semibold">
                            Paste headers here
                        </h1>
                        <p className="text-sm text-gray-500"></p>
                    </div>
                    <Textarea
                        placeholder="Paste your headers here"
                        value={authHeaders}
                        onChange={(e) => setAuthHeaders(e.target.value)}
                        id="auth-headers"
                        className="w-[40vw] h-[50vh]"
                    />
                </div>

                <div className="flex flex-col gap-12 items-start justify-center">
                    <div className="flex flex-col w-full gap-3 items-center justify-center">
                        <div className="space-y-1 w-full">
                            <h1 className="text-lg font-semibold w-full">
                                You need to be connected to the server
                            </h1>
                            {serverOnline && (
                                <p className="text-green-500 text-sm">
                                    Connection Successful
                                </p>
                            )}
                        </div>
                        <AlertDialog
                            open={connectionDialogOpen}
                            onOpenChange={setConnectionDialogOpen}
                        >
                            <AlertDialogTrigger asChild>
                                <Button
                                    className="w-full"
                                    onClick={testConnection}
                                >
                                    Connect
                                </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                                <AlertDialogHeader>
                                    <AlertDialogTitle>
                                        Requesting connection...
                                    </AlertDialogTitle>
                                    <AlertDialogDescription>
                                        Please wait till the server comes
                                        online. This may take upto a minute.
                                    </AlertDialogDescription>
                                </AlertDialogHeader>
                            </AlertDialogContent>
                        </AlertDialog>
                    </div>

                    <div className="flex flex-col gap-3 items-start justify-center">
                        <div className="space-y-1">
                            <h1 className="text-lg font-semibold">
                                Paste Spotify playlist URL(s) here
                            </h1>
                            <div className="flex items-center gap-2">
                                <FaExclamationCircle />
                                <p className="text-sm text-gray-500">
                                    Make sure the playlist(s) are public
                                </p>
                            </div>
                            <div className="flex items-center gap-2">
                                <FaExclamationCircle className="text-blue-500" />
                                <p className="text-sm text-gray-500">
                                    You can paste multiple URLs (one per line)
                                </p>
                            </div>
                            <div className="flex items-center gap-2 mt-2">
                                <FaExclamationCircle className="text-orange-500" />
                                <p className="text-sm text-gray-500">
                                    Timeout issues are common due to server
                                    limitations.
                                    <br />
                                    If you experience them, consider{" "}
                                    <a
                                        href="https://github.com/Pushan2005/SpotTransfer/?tab=readme-ov-file#-quick-start"
                                        className="text-blue-500 hover:underline"
                                    >
                                        self-hosting
                                    </a>{" "}
                                    for better reliability.
                                </p>
                            </div>
                        </div>
                        <Textarea
                            placeholder="Paste your playlist URL(s) here (one per line)"
                            value={playlistUrl}
                            onChange={handleUrlChange}
                            id="playlist-urls"
                            className={`w-full min-h-[100px] ${
                                !isValidUrl ? "border-red-500" : ""
                            }`}
                        />
                        {!isValidUrl && (
                            <p className="text-red-500 text-sm">
                                Please enter valid Spotify playlist URL(s)
                            </p>
                        )}
                        <AlertDialog
                            open={dialogOpen}
                            onOpenChange={setdialogOpen}
                        >
                            <AlertDialogTrigger asChild>
                                <Button
                                    disabled={
                                        !isValidUrl ||
                                        !authHeaders ||
                                        playlistUrl.trim() === "" ||
                                        !serverOnline
                                    }
                                    className="w-full"
                                    onClick={clonePlaylist}
                                >
                                    Clone Playlist
                                </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                                <AlertDialogHeader>
                                    <AlertDialogTitle>
                                        Cloning playlist(s)...
                                    </AlertDialogTitle>
                                    <AlertDialogDescription>
                                        This may take a few minutes. Check the server console for progress updates.
                                    </AlertDialogDescription>
                                </AlertDialogHeader>
                            </AlertDialogContent>
                        </AlertDialog>

                        <AlertDialog
                            open={starPrompt}
                            onOpenChange={setStarPrompt}
                        >
                            <AlertDialogContent>
                                <AlertDialogHeader>
                                    <AlertDialogTitle>
                                        <div className="flex items-center">
                                            <CheckIcon />
                                            Your Playlist(s) have been cloned!
                                        </div>
                                    </AlertDialogTitle>
                                    <AlertDialogDescription>
                                        <div className="ml-12 mb-2">
                                            <p>
                                                Please consider starring the
                                                project on GitHub.
                                            </p>
                                            <p>It's free and helps me a lot!</p>
                                        </div>
                                    </AlertDialogDescription>
                                </AlertDialogHeader>
                                <AlertDialogFooter>
                                    <div className="flex items-center justify-between w-full">
                                        <Button>
                                            <a
                                                className="w-full flex items-center gap-2"
                                                href="https://github.com/Pushan2005/SpotTransfer"
                                            >
                                                ⭐ on GitHub
                                                <FaGithub className="w-6 h-6" />
                                            </a>
                                        </Button>
                                        <AlertDialogAction>
                                            Clone Another Playlist
                                        </AlertDialogAction>
                                    </div>
                                </AlertDialogFooter>
                            </AlertDialogContent>
                        </AlertDialog>
                    </div>
                </div>
            </div>
            <AlertDialog
                open={connectionError}
                onOpenChange={setConnectionError}
            >
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Connection Error</AlertDialogTitle>
                        <AlertDialogDescription>
                            {errorMessage}
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogAction
                            onClick={() => setConnectionError(false)}
                        >
                            Try Again
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
            <AlertDialog open={cloneError} onOpenChange={setCloneError}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Clone Error</AlertDialogTitle>
                        <AlertDialogDescription>
                            {cloneErrorMessage}
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogAction onClick={() => setCloneError(false)}>
                            Try Again
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
            <AlertDialog
                open={missedTracksDialog}
                onOpenChange={setMissedTracksDialog}
            >
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>
                            Some songs couldn't be found
                        </AlertDialogTitle>
                        <AlertDialogDescription>
                            <div className="mt-2">
                                <p className="mb-2">
                                    {missedTracks.count} songs couldn't be found
                                    on YouTube Music:
                                </p>
                                <div className="max-h-[200px] overflow-y-auto">
                                    <ul className="list-disc list-inside">
                                        {missedTracks.tracks.map(
                                            (track, index) => (
                                                <li
                                                    key={index}
                                                    className="text-sm"
                                                >
                                                    {track}
                                                </li>
                                            )
                                        )}
                                    </ul>
                                </div>
                            </div>
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogAction
                            onClick={() => setMissedTracksDialog(false)}
                        >
                            Close
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </>
    );
}
