import Hero from "@/components/landing/hero.tsx";
import HowToUse from "@/components/landing/how-to-use.tsx";
import { Footer } from "@/components/landing/footer.tsx";
import { Link } from "react-router-dom";

import { Analytics } from "@vercel/analytics/react";

export default function App() {
    return (
        <main className="flex w-screen flex-col items-center">
            <div className="w-full bg-primary/10 border-b border-primary/20 px-4 py-2.5">
                <p className="text-center text-xs sm:text-sm text-foreground/80">
                    SpotTransfer can now be self-hosted.{" "}
                    <Link
                        to="/selfhost"
                        className="font-medium text-primary hover:underline"
                    >
                        View the setup guide
                    </Link>
                    {" · "}
                    <Link
                        to="/announcements"
                        className="font-medium text-primary hover:underline"
                    >
                        Read announcements
                    </Link>
                </p>
            </div>
            <Hero />
            <HowToUse />
            <Footer />
            <Analytics />
        </main>
    );
}
