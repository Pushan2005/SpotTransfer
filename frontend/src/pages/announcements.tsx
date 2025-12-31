import { Footer } from "@/components/landing/footer";
import Navbar from "@/nav-bar.tsx";

interface Announcement {
    id: string;
    date: string;
    title: string;
    content: string;
    type: "info" | "warning" | "success" | "error";
}

const announcements: Announcement[] = [
    {
        id: "1",
        date: "December 24, 2024",
        title: "SpotTransfer Launch",
        content: `SpotTransfer is now live! 🎉`,
        type: "success",
    },
    {
        id: "2",
        date: "December 28, 2024",
        title: "Server Improvements and Bug Fixes",
        content: `Several improvements to server stability:

• Extended timeout to 10 minutes (from previous shorter timeouts)
• Better error handling for empty search results
• Improved logging for debugging

Despite these improvements, self-hosting remains the best option for large playlists and guaranteed reliability.`,
        type: "info",
    },
    {
        id: "3",
        date: "January 4, 2025",
        title: "Timeout Extended to 15 Minutes",
        content: `The server timeout has been extended from 10 minutes to 15 minutes to accommodate larger playlists. However, timeout issues may still occur for very large playlists.

        • Improved error handling for clone errors, server errors and connection errors.
        • Extended timeout to 15 minutes (from previous shorter timeouts)

For the most reliable experience, especially with playlists over 100 songs, I recommend self-hosting SpotTransfer.`,
        type: "warning",
    },
    {
        id: "4",
        date: "January 12, 2025",
        title: "New Feature: Missed Tracks Report",
        content: `Added a new feature that shows you which tracks couldn't be found on YouTube Music during the transfer process. This helps you identify:

• Songs that might have different names
• Tracks not available on YouTube Music
• Regional availability issues

You'll now get a detailed report after each playlist transfer.`,
        type: "success",
    },
    {
        id: "5",
        date: "January 13, 2025",
        title: "Self-Hosting Made Easier",
        content: `There have been significant improvements to make self-hosting SpotTransfer much easier:

• Simplified installation process
• Better documentation
• Automated setup scripts
• Reduced configuration complexity

If you're experiencing timeout issues with the hosted version, self-hosting is now more accessible than ever!`,
        type: "success",
    },
    {
        id: "6",
        date: "July 9, 2025",
        title: "Improved Self-Hosting Guide",
        content: `We've significantly improved the self-hosting guide based on user feedback. The new guide includes:

• Step-by-step installation instructions
• Environment variable configuration
• Common troubleshooting solutions

Self-hosting remains the best way to avoid timeout issues and get reliable playlist transfers.`,
        type: "success",
    },
    {
        id: "7",
        date: "July 10, 2025",
        title: "Self-Hosting Guide Updated",
        content: `Updated README.md with enhanced self-hosting instructions to help users set up SpotTransfer locally for better reliability and no timeout issues.

Recent improvements include:
• Clearer setup steps
• Better environment configuration
• Troubleshooting guide

Self-hosting provides unlimited transfers without server timeout restrictions.`,
        type: "info",
    },
    {
        id: "8",
        date: "December 31, 2025",
        title: "Improved Header Parsing for Chrome Users",
        content: `Improved header parsing logic to make it easier for Chrome users. Courtesy of @LifeRIP's contribution.
`,
        type: "success",
    },
];

function getTypeIcon(type: Announcement["type"]) {
    switch (type) {
        case "warning":
            return "⚠️";
        case "error":
            return "❌";
        case "success":
            return "✅";
        default:
            return "ℹ️";
    }
}

export default function Announcements() {
    return (
        <main className="flex w-screen flex-col items-center justify-center">
            <div className="w-full max-w-[1000px] px-4">
                <Navbar />
                <div className="flex flex-col justify-center items-center mt-20 md:mt-30 lg:mt-40">
                    <div className="text-center mb-12">
                        <h1 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold max-w-3xl mx-auto text-center mt-4 relative z-20 py-4 bg-clip-text text-transparent bg-gradient-to-b from-neutral-800 via-neutral-700 to-neutral-700 dark:from-neutral-800 dark:via-white dark:to-white">
                            Announcements
                        </h1>
                        <p className="text-center text-base sm:text-lg md:text-xl pb-4 transition-colors first:mt-0 bg-clip-text text-transparent bg-gradient-to-r from-black to-zinc-950 dark:from-gray-400 dark:to-gray-300">
                            Latest updates and important information about
                            SpotTransfer
                        </p>
                    </div>

                    <div className="w-full max-w-4xl">
                        {announcements
                            .slice()
                            .reverse()
                            .map((announcement, index) => (
                                <div key={announcement.id}>
                                    <section
                                        id={`announcement-${announcement.id}`}
                                        className="py-6"
                                    >
                                        <div className="flex items-start gap-3">
                                            <span className="text-lg mt-1 flex-shrink-0">
                                                {getTypeIcon(announcement.type)}
                                            </span>
                                            <div className="flex-1">
                                                <div className="flex items-center gap-3 mb-2">
                                                    <h2 className="text-lg font-semibold text-neutral-800 dark:text-white">
                                                        {announcement.title}
                                                    </h2>
                                                    <span className="text-xs text-gray-500 dark:text-gray-400">
                                                        {announcement.date}
                                                    </span>
                                                </div>
                                                <div className="text-sm text-neutral-700 dark:text-neutral-300 whitespace-pre-line leading-relaxed">
                                                    {announcement.content}
                                                </div>
                                                {announcement.id === "7" && (
                                                    <div className="mt-3">
                                                        <a
                                                            href="https://github.com/Pushan2005/SpotTransfer"
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                            className="inline-flex items-center gap-2 px-3 py-1.5 bg-neutral-800 dark:bg-white text-white dark:text-black text-sm rounded-lg hover:bg-neutral-700 dark:hover:bg-gray-100 transition-colors"
                                                        >
                                                            <span>📚</span>
                                                            View Self-Hosting
                                                            Guide
                                                        </a>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </section>
                                    {index < announcements.length - 1 && (
                                        <div className="border-t-2 border-white dark:border-gray-600"></div>
                                    )}
                                </div>
                            ))}
                    </div>
                </div>
                <Footer />
            </div>
        </main>
    );
}
