import React, { useState, useEffect, useMemo } from 'react';
import SmoothText from '../primitives/SmoothText';
import { Bot, ChevronRight, Copy, Check } from 'lucide-react';
import clsx from 'clsx';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeHighlight from 'rehype-highlight';
import rehypeKatex from 'rehype-katex';
import { copyToClipboard } from '../../utils/clipboard';
import { remarkCitations } from '../../utils/remarkCitations';
import { parseSources } from '../../utils/parseSources';
import { CitationTooltip } from '../ui/CitationTooltip';
import './OrchestratorCards.css';

/**
 * SynthesisCard - Displays the final answer synthesis phase
 *
 * Shows:
 * - Header with Lead Researcher avatar and model badge
 * - Thinking section (collapsible)
 * - Final answer content (streaming markdown)
 */
export default function SynthesisCard({
    thinking = '',
    content = '',
    model = '',
    agentName = 'Lead Researcher',
    thinkingLevel = null,
    isStreaming = false,
    thinkingOpen = true,
    onToggleThinking,
    showMarkdown = true
}) {
    const [localOpen, setLocalOpen] = useState(thinkingOpen);
    const [copied, setCopied] = useState(false);

    // Sync with global toggle
    useEffect(() => {
        setLocalOpen(thinkingOpen);
    }, [thinkingOpen]);

    const handleToggle = () => {
        const newState = !localOpen;
        setLocalOpen(newState);
        if (onToggleThinking) {
            onToggleThinking(newState);
        }
    };

    const handleCopy = async () => {
        const text = `Synthesis (${model}):\nThinking: ${thinking}\nAnswer: ${content}`;
        await copyToClipboard(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    // Parse model name and thinking efficiency
    const getModelInfo = (modelStr) => {
        if (!modelStr) return { display: 'Model', thinking: null };

        // Extract thinking level if present in string and not provided as prop
        let level = thinkingLevel;
        const thinkMatch = modelStr.match(/\[think(?::(\w+))?\]/);
        if (thinkMatch && !level) {
            level = thinkMatch[1] || 'enabled';
        }

        let cleaned = modelStr.split('::').pop();
        cleaned = cleaned.replace(/\[think(?::\w+)?\]$/, '');

        return { display: cleaned, thinking: level };
    };

    const { display: displayModel, thinking: displayThinking } = getModelInfo(model);

    const sources = useMemo(() => parseSources(content), [content]);

    return (
        <div className="orchestrator-card synthesis-card fade-in">
            {/* Standardized Header */}
            <div className="orchestrator-header">
                <div className="orchestrator-header-icon icon-purple">
                    <Bot size={18} />
                </div>
                <div className="orchestrator-header-info">
                    <div className="orchestrator-header-primary">
                        <span className="orchestrator-header-agent">{agentName}</span>
                        <span className="orchestrator-header-separator">•</span>
                        <span className="orchestrator-header-model">{displayModel}</span>
                        {displayThinking && (
                            <span className="orchestrator-header-thinking">
                                Thinking{typeof displayThinking === 'string' && displayThinking !== 'enabled' ? `: ${displayThinking}` : ''}
                            </span>
                        )}
                    </div>
                </div>
                <div className="orchestrator-header-actions">
                    <span className="orchestrator-phase-badge badge-purple">Synthesis</span>
                    <button
                        onClick={handleCopy}
                        className={clsx(
                            "orchestrator-copy-btn",
                            copied ? "copied text-green-400" : "text-white/40 hover:text-white"
                        )}
                        title={copied ? "Copied!" : "Copy Answer"}
                    >
                        {copied ? <Check size={14} /> : <Copy size={14} />}
                    </button>
                </div>
            </div>

            {/* Body */}
            <div className="synthesis-card-body">
                {/* Thinking Section */}
                {thinking && (
                    <div className="thinking-section">
                        <div className="thinking-header" onClick={handleToggle}>
                            <span className={clsx('thinking-toggle-icon', { open: localOpen })}>
                                <ChevronRight size={14} />
                            </span>
                            <span className="thinking-title">Thinking</span>
                        </div>
                        <div className={clsx('thinking-body', { collapsed: !localOpen })}>
                            <SmoothText text={thinking} speed={5} />
                            {isStreaming && !content && <span className="streaming-cursor">|</span>}
                        </div>
                    </div>
                )}

                {/* Final Answer */}
                {content && (
                    <div className="final-answer">
                        <SmoothText text={content} speed={3}>
                            {(smoothedText) => (
                                showMarkdown ? (
                                    <div className="markdown-content">
                                        <ReactMarkdown
                                            remarkPlugins={[remarkGfm, remarkMath, remarkCitations]}
                                            rehypePlugins={[rehypeHighlight, rehypeKatex]}
                                            components={{
                                                citation: ({ node, number, children }) => (
                                                    <CitationTooltip number={number} sources={sources} />
                                                ),
                                            }}
                                        >
                                            {smoothedText}
                                        </ReactMarkdown>
                                        {isStreaming && <span className="streaming-cursor">|</span>}
                                    </div>
                                ) : (
                                    <div className="plain-content">
                                        {smoothedText}
                                        {isStreaming && <span className="streaming-cursor">|</span>}
                                    </div>
                                )
                            )}
                        </SmoothText>
                    </div>
                )}
            </div>
        </div>
    );
}
