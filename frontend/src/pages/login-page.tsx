import { useEffect, useState } from "react";
import {
    clientId,
    redirectUri,
    generateRandomString,
    sha256,
    base64encode,
} from "../utils/spotiyAuth";

interface TokenResponse {
    access_token: string;
    token_type: string;
    expires_in: number;
    refresh_token?: string;
    scope: string;
}

export default function LoginPage() {
    const [token, setToken] = useState<string | null>(null);

    useEffect(() => {
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get("code");

        if (code) {
            exchangeToken(code);
        }
    }, []);

    const handleLogin = async (): Promise<void> => {
        const codeVerifier = generateRandomString(64);
        const hashed = await sha256(codeVerifier);
        const codeChallenge = base64encode(hashed);

        window.localStorage.setItem("code_verifier", codeVerifier);

        const scope = "playlist-read-private playlist-read-collaborative";

        const authUrl = new URL("https://accounts.spotify.com/authorize");

        const params: Record<string, string> = {
            response_type: "code",
            client_id: clientId,
            scope,
            code_challenge_method: "S256",
            code_challenge: codeChallenge,
            redirect_uri: redirectUri,
        };

        authUrl.search = new URLSearchParams(params).toString();
        window.location.href = authUrl.toString();
    };

    const exchangeToken = async (code: string): Promise<void> => {
        const codeVerifier = localStorage.getItem("code_verifier");

        if (!codeVerifier) {
            console.error("Code verifier not found in local storage.");
            return;
        }

        const payload: RequestInit = {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body: new URLSearchParams({
                client_id: clientId,
                grant_type: "authorization_code",
                code: code,
                redirect_uri: redirectUri,
                code_verifier: codeVerifier,
            }),
        };

        try {
            // Use the official Spotify token endpoint
            const body = await fetch(
                "https://accounts.spotify.com/api/token",
                payload,
            );
            const response: TokenResponse = await body.json();

            if (response.access_token) {
                setToken(response.access_token);
                // Clean up the URL
                window.history.replaceState({}, document.title, "/");
            }
        } catch (error) {
            console.error("Error exchanging token:", error);
        }
    };

    return (
        <div style={{ textAlign: "center", marginTop: "50px" }}>
            <h1>Spotify React OAuth (TS + PKCE)</h1>

            {!token ? (
                <button
                    onClick={handleLogin}
                    style={{
                        padding: "10px 20px",
                        fontSize: "16px",
                        cursor: "pointer",
                    }}
                >
                    Log in with Spotify
                </button>
            ) : (
                <div>
                    <h2 style={{ color: "green" }}>Successfully Logged In!</h2>
                    <p>Your Access Token:</p>
                    <textarea
                        readOnly
                        value={token}
                        rows={4}
                        cols={50}
                        style={{ width: "80%", maxWidth: "500px" }}
                    />
                    <br />
                    <button
                        onClick={() => setToken(null)}
                        style={{
                            marginTop: "15px",
                            padding: "5px 15px",
                            cursor: "pointer",
                        }}
                    >
                        Log Out
                    </button>
                </div>
            )}
        </div>
    );
}
