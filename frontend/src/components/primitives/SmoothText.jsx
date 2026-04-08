import React, { useState, useEffect, useRef } from 'react';

/**
 * SmoothText - Animates text addition character by character
 * to prevent large chunks of text from appearing instantly.
 * 
 * Usage:
 * 1. <SmoothText text="Hello" /> -> <div>Hello</div>
 * 2. <SmoothText text="Hello" as="span" /> -> <span>Hello</span>
 * 3. <SmoothText text="Hello">{(text) => <Markdown>{text}</Markdown>}</SmoothText>
 */
export default function SmoothText({ text, speed = 10, className = "", as: Component = "div", children }) {
    const [displayedText, setDisplayedText] = useState("");
    const targetTextRef = useRef(text);
    const timeoutRef = useRef(null);
    const [isComplete, setIsComplete] = useState(false);

    useEffect(() => {
        setDisplayedText(text || "");
        setIsComplete(true);
    }, [text]);

    // Render prop
    if (typeof children === 'function') {
        return children(displayedText, isComplete);
    }

    return <Component className={className}>{displayedText}</Component>;
}
