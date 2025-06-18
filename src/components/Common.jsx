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
        <button onClick={handleCopy} class={`p-1.5 rounded-md hover:bg-gray-700 ${className}`}>
            {copied ? <ClipboardCheckIcon class="h-4 w-4 text-green-400" /> : <ClipboardIcon class="h-4 w-4 text-gray-400" />}
        </button>
    );
};

export const ToggleButton = ({ isVisible, onToggle, side }) => {
    if (isVisible) return null;
    const positionClass = side === 'left' ? 'left-4' : 'right-4';
    return (
        <div class={`fixed top-4 z-20 ${positionClass}`}>
            <button onClick={onToggle} class="bg-gray-800 hover:bg-gray-700 text-white p-2 rounded-md border border-gray-600">
                {side === 'left' ? <ChevronsRightIcon class="h-5 w-5" /> : <ChevronsLeftIcon class="h-5 w-5" />}
            </button>
        </div>
    );
};
