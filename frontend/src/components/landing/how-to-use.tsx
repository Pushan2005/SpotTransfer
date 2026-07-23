const steps = [
    {
        number: "01",
        title: "Sign in to YouTube Music",
        description: (
            <>
                Open{" "}
                <a
                    href="https://music.youtube.com"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                >
                    music.youtube.com
                </a>{" "}
                and make sure you're logged in with your Google account.
            </>
        ),
    },
    {
        number: "02",
        title: "Grab your request headers",
        description:
            "Open DevTools, filter the Network tab for /browse, and copy the request headers from a successful POST request.",
    },
    {
        number: "03",
        title: "Paste and go",
        description:
            "Paste your headers and Spotify playlist URL, hit clone, and your playlist will appear on YouTube Music.",
    },
];

export default function HowToUse() {
    return (
        <div className="w-full max-w-[960px] mx-auto px-4 pb-20">
            <h2 className="text-sm font-medium text-primary mb-8 tracking-wide uppercase">
                How it works
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-12">
                {steps.map((step) => (
                    <div key={step.number} className="flex flex-col gap-3">
                        <span className="font-mono text-xs text-muted-foreground">
                            {step.number}
                        </span>
                        <h3 className="font-semibold text-foreground text-base">
                            {step.title}
                        </h3>
                        <p className="text-sm text-muted-foreground leading-relaxed">
                            {step.description}
                        </p>
                    </div>
                ))}
            </div>
        </div>
    );
}
