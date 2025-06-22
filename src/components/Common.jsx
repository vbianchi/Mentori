import { h } from 'preact';
import { useState } from 'preact/hooks';
import { ClipboardIcon, ClipboardCheckIcon, ChevronsRightIcon, ChevronsLeftIcon } from './Icons';

export const CopyButton = ({ textToCopy, className = '' }) => {
    const [copied, setCopied] = useState(false);
    const handleCopy = (e) => {
        e.stopPropagation();
        const textArea = document.createElement("textarea");
        textArea.value = textToCopy;
        textArea.style.position = "fixed"; document.body.appendChild(textArea);
        textArea.focus(); textArea.select();
        try { document.execCommand('copy'); setCopied(true); setTimeout(() => setCopied(false), 2000); }
        catch (err) { console.error('Failed to copy text: ', err); }
        document.body.removeChild(textArea);
    };
    return (
        <button onClick={handleCopy} class={`p-1.5 rounded-md hover:bg-secondary ${className}`}>
            {copied ? <ClipboardCheckIcon class="h-4 w-4 text-green-400" /> : <ClipboardIcon class="h-4 w-4 text-muted-foreground" />}
        </button>
    );
};

// --- MODIFIED: The component is simplified and will be positioned by its parent ---
export const ToggleButton = ({ onToggle, side }) => {
    return (
        <button onClick={onToggle} class="bg-card/50 hover:bg-secondary text-muted-foreground hover:text-foreground p-2 rounded-md border border-border">
            {side === 'left' ? <ChevronsRightIcon class="h-5 w-5" /> : <ChevronsLeftIcon class="h-5 w-5" />}
        </button>
    );
};
