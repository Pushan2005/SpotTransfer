import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ThemeProvider } from "@/components/theme-provider";

import "./index.css";
import App from "./pages/App.tsx";
import Announcements from "./pages/announcements.tsx";
import Guide from "./pages/guide.tsx";

createRoot(document.getElementById("root")!).render(
    <StrictMode>
        <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
            <BrowserRouter>
                <Routes>
                    <Route path="/" element={<App />} />
                    <Route
                        path="/announcements"
                        element={<Announcements />}
                    />
                    <Route path="/guide" element={<Guide />} />
                    <Route
                        path="/selfhost"
                        element={<Navigate to="/guide" replace />}
                    />
                    <Route
                        path="/create-playlist"
                        element={<Navigate to="/" replace />}
                    />
                </Routes>
            </BrowserRouter>
        </ThemeProvider>
    </StrictMode>,
);
