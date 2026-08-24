import { Footer } from "@/components/landing/footer";
import { Card, CardContent } from "@/components/ui/card";
import HeaderImg from "@/assets/headers.png";
import Navbar from "@/nav-bar";
import type { ReactNode } from "react";

const headerSteps = [
    "Open music.youtube.com and sign in to your Google account.",
    "Open your browser's developer tools, go to the Network tab, filter for /browse, and find a successful POST request with a 200 status.",
    "In Firefox, right-click the request and choose Copy > Copy Request Headers. In Chrome or Edge, open the request, select Headers, and copy everything from accept: */* to the end of Request Headers.",
    "Paste the copied request headers into backend/browser.json and save the file. Paste them into the file instead of the web-hosted form.",
];

export default function Selfhost() {
    return (
        <main className="flex w-screen flex-col items-center">
            <div className="w-full max-w-[960px] px-4">
                <Navbar />

                <div className="mt-20 md:mt-28 lg:mt-32">
                    <div className="max-w-2xl">
                        <p className="text-sm font-medium uppercase tracking-wide text-primary">
                            Self-hosting guide
                        </p>
                        <h1 className="mt-4 text-3xl font-bold tracking-tight text-foreground sm:text-4xl md:text-5xl">
                            Run SpotTransfer on your computer
                        </h1>
                        <p className="mt-5 text-base leading-relaxed text-muted-foreground sm:text-lg">
                            The transfer needs to be self-hosted. Follow these
                            steps to authenticate with YouTube Music, choose a
                            Spotify playlist, and run the local script.
                        </p>
                    </div>

                    <div className="mt-12 space-y-8">
                        <GuideSection number="01" title="Install the backend">
                            <p>
                                You need Python 3.8 or newer. Clone the
                                repository, enter the backend directory, and
                                install its dependencies:
                            </p>
                            <CodeBlock>{`git clone https://github.com/Pushan2005/SpotTransfer.git
cd SpotTransfer/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt`}</CodeBlock>
                            <p>
                                On Windows, activate the environment with{" "}
                                <InlineCode>venv\Scripts\activate</InlineCode>.
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

                        <GuideSection number="03" title="Set the playlist">
                            <p>
                                Open <InlineCode>backend/setup.py</InlineCode>{" "}
                                and paste your Spotify playlist link into the
                                variable:
                            </p>
                            <CodeBlock>{`spotify_playlist_link = "https://open.spotify.com/playlist/your-playlist-id"`}</CodeBlock>
                        </GuideSection>

                        <GuideSection number="04" title="Run the transfer">
                            <p>
                                From the <InlineCode>backend</InlineCode>{" "}
                                directory, run:
                            </p>
                            <CodeBlock>{`python3 selfhost.py`}</CodeBlock>
                            <p>
                                For a new playlist, change the playlist link
                                in <InlineCode>setup.py</InlineCode> and run{" "}
                                <InlineCode>python3 selfhost.py</InlineCode>{" "}
                                again. Repeat this for each playlist.
                            </p>
                        </GuideSection>

                        <Card className="border-amber-500/30 bg-amber-500/5">
                            <CardContent className="p-6">
                                <h2 className="font-semibold text-foreground">
                                    Authentication issue?
                                </h2>
                                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                                    Delete the contents of{" "}
                                    <InlineCode>browser.json</InlineCode>, get
                                    a fresh set of headers from YouTube Music,
                                    paste them into the file, save it, and run
                                    the script again. This usually happens when
                                    the headers expire.
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
