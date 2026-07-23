import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import Navbar from "@/nav-bar.tsx";
import { Link } from "react-router-dom";
import { usePlaylist } from "@/context/playlist-context";
import { FaGithub } from "react-icons/fa";

export default function Hero() {
    const { playlistUrl, setPlaylistUrl } = usePlaylist();

    return (
        <main className="flex justify-center items-center">
            <div className="w-full max-w-[960px] px-4">
                <Navbar />
                <div className="flex flex-col items-center mt-24 md:mt-32 lg:mt-40">
                    <div className="text-center max-w-2xl mx-auto">
                        <a
                            href="https://github.com/Pushan2005/SpotTransfer"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 px-5 py-2 rounded-full bg-gradient-to-r from-primary/20 via-primary to-primary/20 text-primary-foreground text-sm font-medium hover:brightness-110 transition-all"
                        >
                            <FaGithub className="w-4 h-4" />
                            Star this on GitHub ⭐
                        </a>

                        <h1 className="mt-8 text-3xl sm:text-4xl md:text-5xl lg:text-[3.25rem] font-bold tracking-tight leading-[1.1] text-foreground">
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
                    </div>
                </div>
            </div>
        </main>
    );
}
