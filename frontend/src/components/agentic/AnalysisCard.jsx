import React, { useState, useEffect } from 'react';
import { Search, ChevronRight, CheckCircle2, Copy, Check } from 'lucide-react';
import clsx from 'clsx';
import SmoothText from '../primitives/SmoothText';
import { copyToClipboard } from '../../utils/clipboard';
import './OrchestratorCards.css';

/**
 * AnalysisCard - Displays the Lead Researcher analyzing phase
 *
 * Shows:
 * - Header with "LEAD RESEARCHER" and phase badge
 * - Streaming thinking content (collapsible)
 * - Decision indicator (needs plan / direct answer)
 */
export default function AnalysisCard({
    thinking = '',
    decision = null, // 'plan' | 'direct' | null
    decisionReason = '',
    agentName = "Lead Researcher",
    agentModel = "System",
    thinkingLevel = null,
    isStreaming = false,
    thinkingOpen = true,
    onToggleThinking
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
        const text = `analysis: ${thinking}\ndecision: ${decision} (${decisionReason})`;
        await copyToClipboard(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="orchestrator-card analysis-card fade-in">
            {/* Standardized Header */}
            <div className="orchestrator-header">
                <div className="orchestrator-header-icon icon-purple">
                    <Search size={16} />
                </div>
                <div className="orchestrator-header-info">
                    <div className="orchestrator-header-primary">
                        <span className="orchestrator-header-agent">{agentName}</span>
                        <span className="orchestrator-header-separator">•</span>
                        <span className="orchestrator-header-model">{agentModel}</span>
                        {thinkingLevel && (
                            <span className="orchestrator-header-thinking">
                                Thinking{typeof thinkingLevel === 'string' && thinkingLevel !== 'enabled' ? `: ${thinkingLevel}` : ''}
                            </span>
                        )}
                    </div>
                </div>
                <div className="orchestrator-header-actions">
                    <span className="orchestrator-phase-badge badge-purple">Analyzing</span>
                    <button
                        onClick={handleCopy}
                        className={clsx(
                            "orchestrator-copy-btn",
                            copied ? "copied text-green-400" : "text-white/40 hover:text-white"
                        )}
                        title={copied ? "Copied!" : "Copy Analysis"}
                    >
                        {copied ? <Check size={14} /> : <Copy size={14} />}
                    </button>
                </div>
            </div>

            <div className="orchestrator-card-body">
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
                            {isStreaming && <span className="streaming-cursor">|</span>}
                        </div>
                    </div>
                )}

                {/* Decision Indicator */}
                {decision && (
                    <div className={clsx('analysis-decision', {
                        'decision-plan': decision === 'plan',
                        'decision-direct': decision === 'direct'
                    })}>
                        <CheckCircle2 size={14} />
                        <span>
                            {decision === 'plan'
                                ? `Decision: Creating execution plan${decisionReason ? ` (${decisionReason})` : ''}`
                                : `Decision: Direct answer${decisionReason ? ` (${decisionReason})` : ''}`
                            }
                        </span>
                    </div>
                )}
            </div>
        </div>
    );
}
