import Hero from "@/components/landing/hero.tsx";
import HowToUse from "@/components/landing/how-to-use.tsx";
import { Footer } from "@/components/landing/footer.tsx";
import { Link } from "react-router-dom";

export default function App() {
    return (
        <main className="flex w-screen flex-col items-center">
            <div className="w-full bg-primary/10 border-b border-primary/20 px-4 py-2.5">
                <p className="text-center text-xs sm:text-sm text-foreground/80">
                    SpotTransfer may shut down soon.{" "}
                    <Link
                        to="/announcements"
                        className="font-medium text-primary hover:underline"
                    >
                        Read the announcement
                    </Link>
                </p>
            </div>
            <Hero />
            <HowToUse />
            <Footer />
        </main>
    );
}
