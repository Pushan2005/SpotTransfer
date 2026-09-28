import { FaGithub } from "react-icons/fa";

export function Footer() {
    return (
        <footer className="w-full border-t border-border mt-20">
            <div className="max-w-[960px] mx-auto px-4 py-10 flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="flex items-center gap-1.5">
                    <span className="inline-block w-2 h-2 rounded-full bg-primary" />
                    <span className="text-sm font-semibold text-foreground">
                        SpotTransfer
                    </span>
                </div>
                <p className="text-xs text-muted-foreground">
                    Built by{" "}
                    <a
                        href="https://github.com/pushan2005"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-foreground hover:text-primary transition-colors inline-flex items-center gap-1"
                    >
                        @pushan2005
                        <FaGithub className="w-3.5 h-3.5" />
                    </a>
                </p>
            </div>
        </footer>
    );
}
