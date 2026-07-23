import { Footer } from "@/components/landing/footer";
import GetHeaders from "@/components/create-playlist/get-headers";
import InputFields from "@/components/create-playlist/input-fields";

export default function CreatePlaylist() {
    return (
        <>
            {/* Mobile View */}
            <main className="lg:hidden flex w-screen h-screen flex-col items-center justify-center p-6">
                <h2 className="text-xl font-semibold text-center text-foreground">
                    Open this on a desktop
                </h2>
                <p className="mt-2 text-sm text-muted-foreground">
                    SpotTransfer works best on a laptop or desktop browser.
                </p>
            </main>

            {/* Desktop View */}
            <main className="hidden lg:flex w-screen flex-col items-center">
                <GetHeaders />
                <div className="w-full max-w-[1000px] mx-auto px-4 mt-8">
                    <h2 className="text-sm font-medium text-primary mb-6 tracking-wide uppercase">
                        Transfer
                    </h2>
                </div>
                <InputFields />
                <Footer />
            </main>
        </>
    );
}
