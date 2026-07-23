import { Card, CardContent } from "@/components/ui/card";
import HeaderImg from "@/assets/headers.png";
import Navbar from "@/nav-bar";

type StepProps = {
    title: string;
    description: string | JSX.Element;
};

export default function GetHeaders() {
    const steps: StepProps[] = [
        {
            title: "Open DevTools and go to the Network tab",
            description:
                "Right-click anywhere on the page and select 'Inspect', or press Ctrl+Shift+I. Then navigate to the Network tab.",
        },
        {
            title: "Sign into YouTube Music",
            description: (
                <>
                    Go to{" "}
                    <a
                        href="https://music.youtube.com"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:underline"
                    >
                        music.youtube.com
                    </a>{" "}
                    and make sure you're signed in with your Google account.
                </>
            ),
        },
        {
            title: "Find an authenticated POST request",
            description: (
                <>
                    <p>
                        Filter by <code className="font-mono text-xs bg-muted px-1.5 py-0.5 rounded">/browse</code> in the search bar of
                        the Network tab. Find a POST request with a status of
                        200.
                    </p>
                    <p className="mt-2 font-medium text-foreground">Firefox (recommended):</p>
                    <ul className="list-disc list-inside mb-2 ml-4 text-muted-foreground">
                        <li>
                            Verify: <span className="font-medium text-foreground">Status:</span> 200,{" "}
                            <span className="font-medium text-foreground">Method:</span> POST,{" "}
                            <span className="font-medium text-foreground">File:</span> browse?...
                        </li>
                        <li>
                            Right-click the request &gt; Copy &gt; Copy Request Headers
                        </li>
                    </ul>

                    <p className="mb-2 font-medium text-foreground">Chrome / Edge:</p>
                    <ul className="list-disc list-inside mb-2 ml-4 text-muted-foreground">
                        <li>
                            Verify: <span className="font-medium text-foreground">Status:</span> 200,{" "}
                            <span className="font-medium text-foreground">Name:</span> browse?...
                        </li>
                        <li>
                            Click the request name, go to the Headers tab, and copy everything from "accept: */*" to the end of Request Headers
                        </li>
                    </ul>
                </>
            ),
        },
        {
            title: "Paste the headers below",
            description:
                "These headers authenticate the requests used to create the playlist on your YouTube Music account.",
        },
    ];

    return (
        <>
            <div className="w-[1000px]">
                <Navbar />
            </div>
            <div className="w-[1000px] mx-auto my-8">
                <Card className="overflow-hidden">
                    <div className="flex flex-col lg:flex-row">
                        <CardContent className="flex-1 p-6 lg:p-8">
                            <div className="space-y-6">
                                <h2 className="text-xl lg:text-2xl font-semibold tracking-tight text-foreground">
                                    How to get auth headers
                                </h2>
                                <div className="space-y-5">
                                    {steps.map((step, index) => (
                                        <Step
                                            key={index}
                                            index={index}
                                            title={step.title}
                                            description={step.description}
                                        />
                                    ))}
                                </div>
                            </div>
                        </CardContent>
                        <div className="flex-1 bg-muted min-h-[300px] lg:min-h-0 hidden lg:block">
                            <img
                                src={HeaderImg}
                                alt="How to get headers - network tab example"
                                className="h-full w-full object-cover object-left-top"
                            />
                        </div>
                    </div>
                </Card>
            </div>
        </>
    );
}

function Step({ title, description, index }: StepProps & { index: number }) {
    return (
        <div className="flex items-start gap-3">
            <span className="font-mono text-xs text-primary shrink-0 mt-1 w-5 text-right">
                {String(index + 1).padStart(2, "0")}
            </span>
            <div>
                <h3 className="font-medium text-foreground text-sm">{title}</h3>
                <div className="mt-1 text-sm text-muted-foreground leading-relaxed">
                    {description}
                </div>
            </div>
        </div>
    );
}
