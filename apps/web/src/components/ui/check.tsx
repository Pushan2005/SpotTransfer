"use client";

import { useEffect } from "react";
import type { Variants } from "motion/react";
import { motion, useAnimation } from "motion/react";

const pathVariants: Variants = {
    initial: {
        opacity: 0,
        pathLength: 0,
        scale: 0,
    },
    animate: {
        opacity: 1,
        pathLength: 1,
        scale: 1,
        transition: {
            duration: 0.6,
            ease: "easeOut",
            opacity: { duration: 0.2 },
        },
    },
};

const CheckIcon = () => {
    const controls = useAnimation();

    useEffect(() => {
        setTimeout(() => {
            controls.start("animate");
        }, 250);
    }, [controls]);

    return (
        <div className="p-2 flex items-center justify-center">
            <svg
                xmlns="http://www.w3.org/2000/svg"
                width="28"
                height="28"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
            >
                <motion.path
                    variants={pathVariants}
                    initial="initial"
                    animate={controls}
                    d="M4 12 9 17L20 6"
                />
            </svg>
        </div>
    );
};

export { CheckIcon };
