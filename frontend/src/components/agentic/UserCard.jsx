import React, { useState } from 'react';
import { User, Copy, Check } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeHighlight from 'rehype-highlight';
import rehypeKatex from 'rehype-katex';
import clsx from 'clsx';
import { copyToClipboard } from '../../utils/clipboard';
import './OrchestratorCards.css';

/**
 * UserCard - Displays user messages in orchestrator style
 *
 * Uses standardized header structure:
 * - User avatar icon
 * - User name (from settings or default "You")
 * - Copy button on the right
 */
export default function UserCard({
    content = '',
    showMarkdown = true,
    userName = 'You'
}) {
    const [copied, setCopied] = useState(false);

    const handleCopy = async () => {
        await copyToClipboard(content);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="orchestrator-card user-card fade-in">
            {/* Standardized Header */}
            <div className="orchestrator-header">
                <div className="orchestrator-header-icon icon-purple">
                    <User size={16} />
                </div>
                <div className="orchestrator-header-info">
                    <div className="orchestrator-header-primary">
                        <span className="orchestrator-header-agent">{userName}</span>
                    </div>
                </div>
                <div className="orchestrator-header-actions">
                    <button
                        onClick={handleCopy}
                        className={clsx(
                            "orchestrator-copy-btn",
                            copied ? "copied text-green-400" : "text-white/40 hover:text-white"
                        )}
                        title={copied ? "Copied!" : "Copy Message"}
                    >
                        {copied ? <Check size={14} /> : <Copy size={14} />}
                    </button>
                </div>
            </div>

            {/* Content */}
            <div className="user-card-content">
                {showMarkdown ? (
                    <div className="markdown-content">
                        <ReactMarkdown
                            remarkPlugins={[remarkGfm, remarkMath]}
                            rehypePlugins={[rehypeHighlight, rehypeKatex]}
                        >
                            {content}
                        </ReactMarkdown>
                    </div>
                ) : (
                    <div className="plain-content">{content}</div>
                )}
            </div>
        </div>
    );
}
