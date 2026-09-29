import { Footer } from "@/components/landing/footer";
import { Card, CardContent } from "@/components/ui/card";
import HeaderImg from "@/assets/headers.png";
import Navbar from "@/nav-bar";
import type { ReactNode } from "react";

const headerSteps = [
    "Open music.youtube.com and sign in to your Google account.",
    "Open your browser's developer tools, go to the Network tab, filter for /browse, and find a successful POST request with a 200 status.",
    "In Firefox, right-click the request and choose Copy > Copy Request Headers. In Chrome or Edge, open the request, select Headers, and copy everything from accept: */* to the end of Request Headers.",
    "Paste the copied request headers into the desktop app's headers box. If you use the terminal script instead, paste them into apps/desktop/browser.json and save the file.",
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
                        <GuideSection number="01" title="Get the desktop app">
                            <p>
                                You need Python 3.8 or newer. On Debian/Ubuntu
                                you may also need{" "}
                                <InlineCode>sudo apt install python3-tk</InlineCode>.
                                Clone the repository and start the app:
                            </p>
                            <CodeBlock>{`git clone https://github.com/Pushan2005/SpotTransfer.git
cd SpotTransfer/apps/desktop
python main.py`}</CodeBlock>
                            <p>
                                The first run creates{" "}
                                <InlineCode>apps/desktop/.venv</InlineCode>{" "}
                                automatically, installs the dependencies into
                                it, and restarts itself — no manual pip step.
                            </p>
                        </GuideSection>

                        <GuideSection number="02" title="Copy your request headers">
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
                                Paste your public Spotify playlist link and the
                                request headers into the app's input fields and
                                press <strong>Start Transfer</strong>. Progress
                                is saved to{" "}
                                <InlineCode>
                                    apps/desktop/transfer_progress.json
                                </InlineCode>{" "}
                                after every track, so stopping early never loses
                                completed work — press Start again to resume.
                            </p>
                        </GuideSection>

                        <GuideSection number="04" title="Prefer the terminal?">
                            <p>
                                Open{" "}
                                <InlineCode>apps/desktop/setup.py</InlineCode>{" "}
                                and paste your Spotify playlist link into the
                                variable:
                            </p>
                            <CodeBlock>{`spotify_playlist_link = "https://open.spotify.com/playlist/your-playlist-id"`}</CodeBlock>
                            <p>
                                Paste your headers into{" "}
                                <InlineCode>apps/desktop/browser.json</InlineCode>,
                                then run the script with the desktop venv
                                interpreter from the{" "}
                                <InlineCode>apps/desktop</InlineCode> directory:
                            </p>
                            <CodeBlock>{`.venv/Scripts/python selfhost.py   # Windows
.venv/bin/python selfhost.py       # macOS/Linux`}</CodeBlock>
                            <p>
                                For a new playlist, change the playlist link
                                in <InlineCode>setup.py</InlineCode> and run{" "}
                                <InlineCode>selfhost.py</InlineCode> again.
                                Repeat this for each playlist.
                            </p>
                        </GuideSection>

                        <Card className="border-amber-500/30 bg-amber-500/5">
                            <CardContent className="p-6">
                                <h2 className="font-semibold text-foreground">
                                    Authentication issue?
                                </h2>
                                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                                    The script pauses the transfer and saves
                                    its progress when the headers expire. Get a
                                    fresh set of headers from YouTube Music,
                                    paste them into the app (or into{" "}
                                    <InlineCode>browser.json</InlineCode> for
                                    the terminal script), and run the transfer
                                    again — it resumes from where it stopped
                                    instead of starting over.
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
    return (
        <pre className="overflow-x-auto rounded-lg bg-muted p-4 font-mono text-xs leading-relaxed text-foreground">
            <code>{children}</code>
        </pre>
    );
}

function InlineCode({ children }: { children: ReactNode }) {
    return (
        <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs text-foreground">
            {children}
        </code>
    );
}
