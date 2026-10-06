import { Footer } from "@/components/landing/footer";
import { Card, CardContent } from "@/components/ui/card";
import HeaderImg from "@/assets/headers.png";
import AppImg from "@/assets/app.png";
import Navbar from "@/nav-bar";
import { useState } from "react";
import type { ReactNode } from "react";

const headerSteps = [
    "Open music.youtube.com and sign in to your Google account.",
    "Open your browser's developer tools, go to the Network tab, filter for /browse, and find a successful POST request with a 200 status.",
    "In Firefox, right-click the request and choose Copy > Copy Request Headers. In Chrome or Edge, open the request, select Headers, and copy everything from accept: */* to the end of Request Headers.",
    "Paste the copied request headers into the app's headers box.",
];

export default function Guide() {
    return (
        <main className="flex w-screen flex-col items-center">
            <div className="w-full max-w-[960px] px-4">
                <Navbar />

                <div className="mt-20 md:mt-28 lg:mt-32">
                    <div className="max-w-2xl">
                        <p className="text-sm font-medium uppercase tracking-wide text-primary">
                            Guide
                        </p>
                        <h1 className="mt-4 text-3xl font-bold tracking-tight text-foreground sm:text-4xl md:text-5xl">
                            Run SpotTransfer on your computer
                        </h1>
                        <p className="mt-5 text-base leading-relaxed text-muted-foreground sm:text-lg">
                            SpotTransfer is self-hosted: the transfer runs on
                            your machine, not on a server. Use the desktop app
                            below, or the terminal script if you prefer it.
                        </p>
                    </div>

                    <div className="mt-12 space-y-8">
                        <GuideSection number="01" title="Get the app">
                            <p>
                                You need Git and Python 3.8 or newer. On
                                Debian/Ubuntu you may also need{" "}
                                <InlineCode>
                                    sudo apt install python3-tk
                                </InlineCode>
                                .
                                <br />
                                Copy and paste this into your terminal and run:
                            </p>
                            <CodeBlock>{`git clone https://github.com/Pushan2005/SpotTransfer.git
cd SpotTransfer/apps/desktop
python main.py`}</CodeBlock>
                            <p>
                                Already have SpotTransfer? Update to the latest
                                version by running{" "}
                                <InlineCode>git pull</InlineCode> from the
                                project directory:
                            </p>
                            <CodeBlock>{`cd SpotTransfer
git pull`}</CodeBlock>
                            <p>
                                No Git? Download the ZIP from{" "}
                                <a
                                    href="https://github.com/Pushan2005/SpotTransfer"
                                    target="_blank"
                                    rel="noreferrer"
                                    className="text-blue-600 underline underline-offset-2"
                                >
                                    GitHub
                                </a>
                                , then run the commands below in the extracted
                                folder instead:
                            </p>
                            <CodeBlock>{`cd apps/desktop
python main.py`}</CodeBlock>
                        </GuideSection>

                        <GuideSection
                            number="02"
                            title="Copy your request headers"
                        >
                            <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_280px] lg:items-start">
                                <ol className="list-decimal space-y-3 pl-5">
                                    {headerSteps.map((step) => (
                                        <li key={step}>{step}</li>
                                    ))}
                                </ol>
                                <div className="overflow-hidden rounded-lg border border-border bg-muted">
                                    <img
                                        src={HeaderImg}
                                        alt="YouTube Music Network tab showing a filtered /browse POST request"
                                        className="h-full w-full object-cover object-left-top"
                                    />
                                </div>
                            </div>
                        </GuideSection>

                        <GuideSection number="03" title="Run the transfer">
                            <p>
                                Paste your Spotify playlist link and the request
                                headers into the app and click{" "}
                                <strong>Clone Playlist</strong>.
                            </p>
                            <p>
                                Found SpotTransfer helpful? Please star the
                                project on{" "}
                                <a
                                    href="https://github.com/Pushan2005/SpotTransfer"
                                    target="_blank"
                                    rel="noreferrer"
                                    className="text-blue-600 underline underline-offset-2"
                                >
                                    GitHub
                                </a>
                                , it is free and it helps a lot!
                            </p>
                            <p className="text-xs text-muted-foreground">
                                This is a{" "}
                                <strong className="underline underline-offset-2">
                                    screenshot of the app
                                </strong>
                                , not the app itself — follow step 01 above to
                                run it on your computer.
                            </p>
                            <div className="overflow-hidden rounded-lg border border-border bg-muted">
                                <img
                                    src={AppImg}
                                    alt="SpotTransfer desktop app with headers box, playlist URL field, and Clone Playlist button"
                                    draggable={false}
                                    className="h-full w-full select-none object-cover object-left-top pointer-events-none"
                                />
                            </div>
                        </GuideSection>

                        <Card className="border-amber-500/30 bg-amber-500/5">
                            <CardContent className="p-6">
                                <h2 className="font-semibold text-foreground">
                                    Authentication issue?
                                </h2>
                                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                                    The request headers expire periodically,
                                    which is most noticeable on large playlists.
                                    When that happens the app pauses the
                                    transfer and saves its progress to{" "}
                                    <InlineCode>
                                        apps/desktop/transfer_progress.json
                                    </InlineCode>
                                    . Get a fresh set of headers from YouTube
                                    Music, paste them into the headers box, and
                                    click Clone Playlist again — the app resumes
                                    from where it left off.
                                </p>
                                <p className="mt-2 text-sm font-medium leading-relaxed text-foreground">
                                    Starting a transfer for a different playlist
                                    automatically discards any saved progress of
                                    the previous one.
                                </p>
                            </CardContent>
                        </Card>

                        <Card className="border-red-500/30 bg-red-500/5">
                            <CardContent className="p-6">
                                <h2 className="font-semibold text-foreground">
                                    Still stuck?
                                </h2>
                                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                                    Keep your log file handy — it records what
                                    happened during each transfer and makes
                                    debugging much faster. You can find it at{" "}
                                    <InlineCode>
                                        apps/desktop/logs/spottransfer.log
                                    </InlineCode>
                                    . If you report an issue, attach it so I can
                                    take a look and get back to you.
                                </p>
                            </CardContent>
                        </Card>
                    </div>
                </div>

                <Footer />
            </div>
        </main>
    );
}

function GuideSection({
    number,
    title,
    children,
}: {
    number: string;
    title: string;
    children: ReactNode;
}) {
    return (
        <section className="border-t border-border pt-6">
            <div className="flex items-start gap-4">
                <span className="font-mono text-xs text-primary">{number}</span>
                <div className="min-w-0 flex-1">
                    <h2 className="font-semibold text-foreground">{title}</h2>
                    <div className="mt-3 space-y-3 text-sm leading-relaxed text-muted-foreground">
                        {children}
                    </div>
                </div>
            </div>
        </section>
    );
}

function CodeBlock({ children }: { children: string }) {
    const [copied, setCopied] = useState(false);

    async function copy() {
        try {
            await navigator.clipboard.writeText(children);
        } catch {
            // Clipboard API needs a secure context — fall back to execCommand.
            const area = document.createElement("textarea");
            area.value = children;
            document.body.appendChild(area);
            area.select();
            document.execCommand("copy");
            document.body.removeChild(area);
        }
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
    }

    return (
        <div className="relative overflow-hidden rounded-lg bg-muted">
            <button
                type="button"
                onClick={copy}
                aria-label="Copy code to clipboard"
                className="absolute right-2 top-2 rounded-md border border-border bg-background/80 px-2 py-1 font-mono text-[11px] text-muted-foreground transition-colors hover:text-foreground"
            >
                {copied ? "Copied" : "Copy"}
            </button>
            <pre className="overflow-x-auto p-4 pr-16 font-mono text-xs leading-relaxed text-foreground">
                <code>{children}</code>
            </pre>
        </div>
    );
}

function InlineCode({ children }: { children: ReactNode }) {
    return (
        <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs text-foreground">
            {children}
        </code>
    );
}
