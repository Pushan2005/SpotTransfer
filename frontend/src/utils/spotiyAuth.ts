export const clientId: string = import.meta.env.VITE_SPOTIPY_CLIENT_ID!;
export const redirectUri: string = import.meta.env.DEV
    ? "http://localhost:5173/callback"
    : import.meta.env.VITE_REDIRECT_URI;

export const generateRandomString = (length: number): string => {
    const possible =
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    const values = crypto.getRandomValues(new Uint8Array(length));
    return values.reduce((acc, x) => acc + possible[x % possible.length], "");
};

export const sha256 = async (plain: string): Promise<ArrayBuffer> => {
    const encoder = new TextEncoder();
    const data = encoder.encode(plain);
    return window.crypto.subtle.digest("SHA-256", data);
};

export const base64encode = (input: ArrayBuffer): string => {
    return btoa(String.fromCharCode(...new Uint8Array(input)))
        .replace(/=/g, "")
        .replace(/\+/g, "-")
        .replace(/\//g, "_");
};
