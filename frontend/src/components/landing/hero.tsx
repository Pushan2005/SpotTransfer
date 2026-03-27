import { Button } from "@/components/ui/button";
import Navbar from "@/nav-bar.tsx";
import { Link } from "react-router-dom";

export default function Hero() {
    return (
        <main className="flex justify-center items-center mt-5">
            <div className="w-full max-w-[1000px] px-4">
                <Navbar />
                <div className="flex flex-col justify-center items-center mt-20 md:mt-30 lg:mt-40">
                    <div className="text-center">
                        <div className="flex justify-center items-center mb-6">
                            <a href="https://github.com/Pushan2005/SpotTransfer">
                                <Button
                                    variant="outline"
                                    className="dark:bg-gradient-to-r dark:from-gray-900 dark:to-black text-black dark:text-white flex justify-center items-center rounded-full px-6 py-3 text-lg border dark:border-gray-800"
                                >
                                    Star this on Github ⭐
                                </Button>
                            </a>
                        </div>
                        <h1 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold max-w-3xl mx-auto text-center mt-4 relative z-20 py-4 bg-clip-text text-transparent bg-gradient-to-b from-neutral-800 via-neutral-700 to-neutral-700 dark:from-neutral-800 dark:via-white dark:to-white">
                            Sync your Spotify Library to YouTube Music
                        </h1>
                        <p className="text-center text-sm sm:text-base md:text-lg pb-4 transition-colors first:mt-0 bg-clip-text text-transparent bg-gradient-to-r from-black to-zinc-950 dark:from-gray-400 dark:to-gray-300 max-w-2xl mx-auto">
                            SpotTransfer is a free service that allows you to
                            sync your Spotify library to YouTube Music in a few
                            simple steps.
                        </p>
                        <form className="flex flex-col items-center justify-center gap-4 sm:flex-row sm:gap-3 mt-8"></form>
                        <div className="flex flex-col items-center gap-2 mt-8">
                            <div className="bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-800 rounded-lg p-4 mb-4 max-w-md">
                                <p className="text-amber-900 dark:text-amber-100 font-semibold text-sm">
                                    ⚠️ Important Notice
                                </p>
                                <p className="text-amber-800 dark:text-amber-200 text-sm mt-2">
                                    Due to recent changes in Spotify's API
                                    policies, users will have to login to their
                                    Spotify account to be able to pull their
                                    playlists.
                                </p>
                            </div>
                            <p className="text-sm text-muted-foreground">
                                Login to Spotify to get started
                            </p>
                            <Link to="/login">
                                <Button className="px-6 py-2 text-md flex items-center gap-2">
                                    <img
                                        src="/Spotify_Primary_Logo_RGB_Green.png"
                                        alt="Spotify"
                                        className="w-[25px] h-[25px]"
                                    />
                                    Login to Spotify
                                </Button>
                            </Link>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    );
}
