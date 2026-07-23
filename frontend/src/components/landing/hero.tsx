import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import Navbar from "@/nav-bar.tsx";
import { Link } from "react-router-dom";
import { usePlaylist } from "@/context/playlist-context";

export default function Hero() {
    const { playlistUrl, setPlaylistUrl } = usePlaylist();

    return (
        <main className="flex justify-center items-center">
            <div className="w-full max-w-[960px] px-4">
                <Navbar />
                <div className="flex flex-col items-center mt-24 md:mt-32 lg:mt-40">
                    <div className="text-center max-w-2xl mx-auto">
                        <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-[3.25rem] font-bold tracking-tight leading-[1.1] text-foreground">
                            Transfer your Spotify
                            <br />
                            playlist to{" "}
                            <span className="text-primary">YouTube Music</span>
                        </h1>
                        <p className="mt-5 text-muted-foreground text-base sm:text-lg leading-relaxed max-w-lg mx-auto">
                            A free, open-source tool to move your playlists
                            across platforms in a few steps.
                        </p>

                        <div className="mt-10 flex flex-col sm:flex-row items-center gap-3 w-full max-w-xl mx-auto">
                            <Input
                                placeholder="open.spotify.com/playlist/..."
                                value={playlistUrl}
                                onChange={(e) => setPlaylistUrl(e.target.value)}
                                className="flex-1 h-11 text-sm"
                            />
                            <Link to="/create-playlist" className="shrink-0">
                                <Button className="h-11 px-6 text-sm font-medium">
                                    Get Started
                                </Button>
                            </Link>
                        </div>

                        <a
                            href="https://github.com/Pushan2005/SpotTransfer"
                            className="inline-flex items-center gap-1.5 mt-6 text-xs text-muted-foreground hover:text-foreground transition-colors"
                        >
                            <span className="inline-block w-1.5 h-1.5 rounded-full bg-primary" />
                            View source on GitHub
                        </a>
                    </div>
                </div>
            </div>
        </main>
    );
}
