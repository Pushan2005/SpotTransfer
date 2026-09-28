import { createContext, useContext, useState, ReactNode } from "react";

type PlaylistContextType = {
    playlistUrl: string;
    setPlaylistUrl: (url: string) => void;
};

const PlaylistContext = createContext<PlaylistContextType | undefined>(
    undefined
);

export function PlaylistProvider({ children }: { children: ReactNode }) {
    const [playlistUrl, setPlaylistUrl] = useState("");

    return (
        <PlaylistContext.Provider value={{ playlistUrl, setPlaylistUrl }}>
            {children}
        </PlaylistContext.Provider>
    );
}

export function usePlaylist() {
    const context = useContext(PlaylistContext);
    if (context === undefined) {
        throw new Error("usePlaylist must be used within a PlaylistProvider");
    }
    return context;
}
