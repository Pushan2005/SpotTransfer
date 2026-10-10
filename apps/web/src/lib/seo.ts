import { useEffect } from "react";

const SITE_URL = "https://spottransfer.pages.dev";

interface SeoOptions {
    title: string;
    description: string;
    path: string;
}

export function useSeo({ title, description, path }: SeoOptions) {
    useEffect(() => {
        const canonicalUrl = `${SITE_URL}${path}`;

        document.title = title;

        const setMeta = (selector: string, content: string) => {
            let el = document.head.querySelector<HTMLMetaElement>(selector);
            if (!el) {
                el = document.createElement("meta");
                // selector is like meta[name="description"] or meta[property="og:title"]
                const match = selector.match(/meta\[(name|property)="(.+)"\]/);
                if (match) el.setAttribute(match[1], match[2]);
                document.head.appendChild(el);
            }
            el.setAttribute("content", content);
        };

        setMeta('meta[name="description"]', description);
        setMeta('meta[property="og:title"]', title);
        setMeta('meta[property="og:description"]', description);
        setMeta('meta[property="og:url"]', canonicalUrl);
        setMeta('meta[name="twitter:title"]', title);
        setMeta('meta[name="twitter:description"]', description);

        let canonical = document.head.querySelector<HTMLLinkElement>(
            'link[rel="canonical"]',
        );
        if (!canonical) {
            canonical = document.createElement("link");
            canonical.setAttribute("rel", "canonical");
            document.head.appendChild(canonical);
        }
        canonical.setAttribute("href", canonicalUrl);
    }, [title, description, path]);
}

export { SITE_URL };
