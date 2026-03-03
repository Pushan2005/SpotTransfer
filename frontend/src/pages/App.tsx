import Hero from "@/components/landing/hero.tsx";
import HowToUse from "@/components/landing/how-to-use.tsx";
import { Footer } from "@/components/landing/footer.tsx";
import { Link } from "react-router-dom";

export default function App() {
    return (
        <main className="flex w-screen flex-col items-center justify-center">
            <div className="w-full bg-yellow-100 border-b-2 border-yellow-300 px-4 py-3">
                <p className="text-center text-sm md:text-base text-yellow-900">
                    Possibility of SpotTransfer shutting down, check{" "}
                    <Link
                        to="/announcements"
                        className="font-semibold underline hover:text-yellow-700 transition-colors"
                    >
                        announcements
                    </Link>{" "}
                    for more details
                </p>
            </div>
            <div className="mb-10">
                <Hero />
            </div>
            <h2 className="mt-20 text-center mb-3 text-2xl font-bold mx-auto relative z-20 py-4 bg-clip-text text-transparent bg-gradient-to-b from-neutral-800 via-neutral-700 to-neutral-700 dark:from-neutral-800 dark:via-white dark:to-white w-full">
                How to use
            </h2>
            <HowToUse />
            <Footer />
        </main>
    );
}
