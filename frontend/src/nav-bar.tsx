import { FaGithub } from "react-icons/fa";
import { Link } from "react-router-dom";

export default function Navbar() {
    return (
        <nav className="flex w-full justify-between items-center px-4 sm:px-10 py-5">
            <Link
                to="/"
                className="flex items-center gap-1.5 text-foreground"
            >
                <span className="inline-block w-2 h-2 rounded-full bg-primary" />
                <span className="text-lg font-semibold tracking-tight">
                    SpotTransfer
                </span>
            </Link>
            <div className="flex items-center gap-6">
                <Link
                    to="/announcements"
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                    Announcements
                </Link>
                <a
                    href="https://github.com/Pushan2005/SpotTransfer"
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1.5"
                >
                    <FaGithub className="w-4 h-4" />
                    <span className="hidden sm:inline">GitHub</span>
                </a>
            </div>
        </nav>
    );
}
