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

    const handleUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const url = e.target.value;
        setPlaylistUrl(url);
        setIsValidUrl(validateUrl(url) || url === "");
    };

    async function clonePlaylist() {
        const body = {
            playlist_link: playlistUrl,
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
                if (data.missed_tracks.count > 0) {
                    setMissedTracks(data.missed_tracks);
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
                            className="text-primary hover:underline"
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
                            className="text-primary hover:underline"
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
                        className="text-primary hover:underline"
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
            <div className="w-full max-w-[1000px] mx-auto px-4 flex flex-col lg:flex-row items-start justify-center gap-10 lg:gap-16 pb-12">
                {/* Left: Headers textarea */}
                <div className="flex-1 w-full space-y-3">
                    <label className="text-sm font-medium text-foreground">
                        Paste headers here
                    </label>
                    <Textarea
                        placeholder="Paste your headers here"
                        value={authHeaders}
                        onChange={(e) => setAuthHeaders(e.target.value)}
                        id="auth-headers"
                        className="w-full min-h-[300px] lg:min-h-[400px] font-mono text-xs"
                    />
                </div>

                {/* Right: Controls */}
                <div className="flex-1 w-full space-y-8">
                    {/* Connection section */}
                    <div className="space-y-3">
                        <div>
                            <h3 className="text-sm font-medium text-foreground">
                                Connect to server
                            </h3>
                            {serverOnline && (
                                <p className="text-xs text-primary mt-1">
                                    Connected
                                </p>
                            )}
                        </div>
                        <AlertDialog
                            open={connectionDialogOpen}
                            onOpenChange={setConnectionDialogOpen}
                        >
                            <AlertDialogTrigger asChild>
                                <Button
                                    variant={serverOnline ? "secondary" : "default"}
                                    className="w-full"
                                    onClick={testConnection}
                                >
                                    {serverOnline ? "Reconnect" : "Connect"}
                                </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                                <AlertDialogHeader>
                                    <AlertDialogTitle>
                                        Connecting...
                                    </AlertDialogTitle>
                                    <AlertDialogDescription>
                                        Please wait while the server comes
                                        online. This may take up to a minute.
                                    </AlertDialogDescription>
                                </AlertDialogHeader>
                            </AlertDialogContent>
                        </AlertDialog>
                    </div>

                    {/* Playlist URL section */}
                    <div className="space-y-3">
                        <div>
                            <h3 className="text-sm font-medium text-foreground">
                                Spotify playlist URL
                            </h3>
                            <div className="flex items-center gap-1.5 mt-1.5">
                                <FaExclamationCircle className="text-muted-foreground w-3 h-3" />
                                <p className="text-xs text-muted-foreground">
                                    The playlist must be public
                                </p>
                            </div>
                            <div className="flex items-center gap-1.5 mt-1">
                                <FaExclamationCircle className="text-amber-500 w-3 h-3" />
                                <p className="text-xs text-muted-foreground">
                                    Timeout issues are common due to server
                                    limitations.{" "}
                                    <a
                                        href="https://github.com/Pushan2005/SpotTransfer/?tab=readme-ov-file#-quick-start"
                                        className="text-primary hover:underline"
                                    >
                                        Self-host
                                    </a>{" "}
                                    for better reliability.
                                </p>
                            </div>
                        </div>
                        <Input
                            placeholder="open.spotify.com/playlist/..."
                            value={playlistUrl}
                            onChange={handleUrlChange}
                            id="playlist-name"
                            className={`w-full ${
                                !isValidUrl ? "border-destructive" : ""
                            }`}
                        />
                        {!isValidUrl && (
                            <p className="text-destructive text-xs">
                                Please enter a valid Spotify playlist URL
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
                                        Fetching playlist...
                                    </AlertDialogTitle>
                                    <AlertDialogDescription>
                                        This may take a few minutes.
                                    </AlertDialogDescription>
                                </AlertDialogHeader>
                            </AlertDialogContent>
                        </AlertDialog>
                    </div>
                </div>
            </div>

            {/* Success dialog */}
            <AlertDialog open={starPrompt} onOpenChange={setStarPrompt}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>
                            <div className="flex items-center gap-2">
                                <CheckIcon />
                                Playlist cloned
                            </div>
                        </AlertDialogTitle>
                        <AlertDialogDescription>
                            <p className="mt-1">
                                Please consider starring the project on GitHub.
                                It's free and helps a lot.
                            </p>
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <div className="flex items-center justify-between w-full">
                            <Button variant="outline" size="sm">
                                <a
                                    className="flex items-center gap-1.5"
                                    href="https://github.com/Pushan2005/SpotTransfer"
                                >
                                    Star on GitHub
                                    <FaGithub className="w-4 h-4" />
                                </a>
                            </Button>
                            <AlertDialogAction>
                                Clone Another
                            </AlertDialogAction>
                        </div>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>

            {/* Connection error dialog */}
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

            {/* Clone error dialog */}
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

            {/* Missed tracks dialog */}
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
