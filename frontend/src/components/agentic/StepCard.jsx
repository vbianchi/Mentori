import React, { useState, useEffect } from 'react';
import SmoothText from '../primitives/SmoothText';
import { CheckCircle2, Loader2, AlertCircle, ChevronRight, ArrowUpRight, ArrowDownLeft, AlertTriangle, Copy, Check } from 'lucide-react';
import clsx from 'clsx';
import { copyToClipboard } from '../../utils/clipboard';
import './OrchestratorCards.css';

/**
 * Agent badge configuration
 */
const AGENT_COLORS = {
    handyman: { bg: 'rgba(59, 130, 246, 0.2)', color: '#93c5fd' },
    coder: { bg: 'rgba(168, 85, 247, 0.2)', color: '#d8b4fe' },
    vision: { bg: 'rgba(16, 185, 129, 0.2)', color: '#6ee7b7' },
    editor: { bg: 'rgba(245, 158, 11, 0.2)', color: '#fcd34d' },
    lead_researcher: { bg: 'rgba(139, 92, 246, 0.2)', color: '#c4b5fd' },
    supervisor: { bg: 'rgba(236, 72, 153, 0.2)', color: '#f9a8d4' },  // Pink for Supervisor
    default: { bg: 'rgba(156, 163, 175, 0.2)', color: '#d1d5db' }
};

const AGENT_LABELS = {
    handyman: 'Handyman',
    coder: 'Coder',
    vision: 'Vision',
    editor: 'Editor',
    lead_researcher: 'Lead Researcher',
    supervisor: 'Supervisor',
    default: 'Agent'
};

/**
 * StepCard - Displays a single orchestrator step execution
 *
 * Shows:
 * - Header with status icon, step description, agent badge
 * - Tool call section (name + arguments)
 * - Tool result section (content or loading)
 * - Error section (inline, if failed)
 * - LR evaluation section (collapsible thinking)
 */
export default function StepCard({
    stepId,
    description,
    agentRole = 'default',
    agentName = 'Agent',
    agentModel = 'Model',
    thinkingLevel = null,
    status = 'pending', // 'pending' | 'running' | 'completed' | 'failed'
    toolName,
    toolInput,
    toolOutput,
    toolProgress = [],
    error = null,
    evaluation = '',
    evaluationSummary = '',
    isStreaming = false,
    thinkingOpen = true,
    onToggleThinking
}) {
    const [evalOpen, setEvalOpen] = useState(thinkingOpen);
    const [copied, setCopied] = useState(false);

    // Sync with global toggle
    useEffect(() => {
        setEvalOpen(thinkingOpen);
    }, [thinkingOpen]);

    const handleToggleEval = () => {
        const newState = !evalOpen;
        setEvalOpen(newState);
        if (onToggleThinking) {
            onToggleThinking(newState);
        }
    };

    const handleCopy = async () => {
        let text = `Step: ${description}\nTool: ${toolName}`;

        // Include full tool input
        if (toolInput) {
            try {
                const parsed = JSON.parse(toolInput);
                text += `\n\nInput:\n${JSON.stringify(parsed, null, 2)}`;
            } catch {
                text += `\n\nInput:\n${toolInput}`;
            }
        }

        // Include full tool output
        if (toolOutput) {
            text += `\n\nOutput:\n${toolOutput}`;
        }

        // Include error if present
        if (error) {
            text += `\n\nError:\n${error}`;
        }

        await copyToClipboard(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const agentColors = AGENT_COLORS[agentRole] || AGENT_COLORS.default;
    // const agentLabel = AGENT_LABELS[agentRole] || AGENT_LABELS.default; // Unused if we use agentName

    // Status icon and styling
    const getStatusIcon = () => {
        switch (status) {
            case 'completed':
                return <CheckCircle2 size={18} className="text-white" />;
            case 'running':
                return <Loader2 size={18} className="text-white animate-spin" />;
            case 'failed':
                return <AlertCircle size={18} className="text-white" />;
            default:
                return <div className="w-4 h-4 rounded-full bg-gray-600" />;
        }
    };

    // Format tool input for display
    const formatToolInput = (input) => {
        if (!input) return '(No arguments)';
        if (typeof input === 'string') {
            try {
                return JSON.stringify(JSON.parse(input), null, 2);
            } catch {
                return input;
            }
        }
        return JSON.stringify(input, null, 2);
    };

    // Thinking level display
    // Map status to badge style
    const statusBadgeStyle = {
        completed: 'badge-green',
        running: 'badge-blue',
        failed: 'badge-orange',
        pending: 'badge-muted'
    }[status] || 'badge-muted';

    const statusLabel = {
        completed: 'Done',
        running: 'Running',
        failed: 'Failed',
        pending: 'Pending'
    }[status] || 'Pending';

    return (
        <div className={clsx('orchestrator-card step-card fade-in', {
            'step-success': status === 'completed',
            'step-running': status === 'running',
            'step-failed': status === 'failed'
        })}>
            {/* Standardized Header */}
            <div className="orchestrator-header">
                <div className={clsx('step-status-icon', status)}>
                    {getStatusIcon()}
                </div>
                <div className="orchestrator-header-info">
                    <div className="orchestrator-header-primary">
                        <span className="orchestrator-header-agent" style={{ color: agentColors.color }}>
                            {agentName}
                        </span>
                        <span className="orchestrator-header-separator">•</span>
                        <span className="orchestrator-header-model">{agentModel}</span>
                        {thinkingLevel && (
                            <span className="orchestrator-header-thinking">
                                Thinking{typeof thinkingLevel === 'string' ? `: ${thinkingLevel}` : ''}
                            </span>
                        )}
                    </div>
                    <div className="orchestrator-header-secondary">{description}</div>
                </div>
                <div className="orchestrator-header-actions">
                    <span className={clsx('orchestrator-phase-badge', statusBadgeStyle)}>{statusLabel}</span>
                    <span className="orchestrator-header-model">{stepId}</span>
                    <button
                        onClick={handleCopy}
                        className={clsx(
                            "orchestrator-copy-btn",
                            copied ? "copied text-green-400" : "text-white/40 hover:text-white"
                        )}
                        title={copied ? "Copied!" : "Copy Step Info"}
                    >
                        {copied ? <Check size={14} /> : <Copy size={14} />}
                    </button>
                </div>
            </div>

            {/* Body */}
            <div className="step-card-body">
                {/* Tool Call Section */}
                {toolName && (
                    <div className="tool-section">
                        <div className="tool-section-header">
                            <ArrowUpRight size={12} />
                            <span>Tool Call</span>
                        </div>
                        <div className="tool-call-box">
                            <div className="tool-name-display">{toolName}</div>
                            <div className="tool-args-display">
                                {formatToolInput(toolInput)}
                            </div>
                        </div>
                    </div>
                )}

                {/* Error Section (Inline) */}
                {error && (
                    <div className="error-section">
                        <div className="error-header">
                            <AlertTriangle size={14} />
                            <span>Tool Error</span>
                        </div>
                        <div className="error-message">{error}</div>
                    </div>
                )}

                {/* Tool Result Section */}
                {(toolOutput || status === 'running') && !error && (
                    <div className="tool-section">
                        <div className="tool-section-header">
                            <ArrowDownLeft size={12} />
                            <span>Tool Result</span>
                        </div>
                        <div className={clsx('tool-result-box', { 'result-loading': status === 'running' && !toolOutput })}>
                            {status === 'running' && !toolOutput ? (
                                toolProgress && toolProgress.length > 0 ? (
                                    <div className="tool-progress-log">
                                        {toolProgress.map((p, i) => {
                                            const isLatest = i === toolProgress.length - 1;
                                            const progressLabel = p.totalSteps > 0
                                                ? ` (${p.step}/${p.totalSteps})`
                                                : '';
                                            return (
                                                <div key={i} className={clsx('progress-line', { latest: isLatest })}>
                                                    {isLatest
                                                        ? <Loader2 size={12} className="progress-icon animate-spin" />
                                                        : <CheckCircle2 size={12} className="progress-icon done" />
                                                    }
                                                    <span className="progress-message">
                                                        {p.message}{progressLabel}
                                                    </span>
                                                </div>
                                            );
                                        })}
                                    </div>
                                ) : (
                                    <span className="loading-text">
                                        Running...
                                        <span className="streaming-cursor">|</span>
                                    </span>
                                )
                            ) : (
                                <KernelResultRenderer content={toolOutput} />
                            )}
                        </div>
                    </div>
                )}

                {/* Supervisor Evaluation Section */}
                {(evaluation || evaluationSummary) && (
                    <div className="evaluation-section">
                        <div className="evaluation-header" onClick={handleToggleEval}>
                            <span className={clsx('evaluation-toggle-icon', { open: evalOpen })}>
                                <ChevronRight size={14} />
                            </span>
                            <span className="evaluation-title">Supervisor Evaluation</span>
                        </div>
                        {evaluation && (
                            <div className={clsx('evaluation-body', { collapsed: !evalOpen })}>
                                <SmoothText text={evaluation} speed={5} />
                                {isStreaming && <span className="streaming-cursor">|</span>}
                            </div>
                        )}
                        {evaluationSummary && (
                            <div className={clsx('evaluation-summary', {
                                'summary-success': status === 'completed',
                                'summary-error': status === 'failed'
                            })}>
                                {status === 'completed' ? (
                                    <><CheckCircle2 size={12} /> {evaluationSummary}</>
                                ) : status === 'failed' ? (
                                    <><AlertCircle size={12} /> {evaluationSummary}</>
                                ) : (
                                    evaluationSummary
                                )}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

// Helper component to extract and render rich media from backend output
// Format: Text... <!--RENDER_IMAGE mime="image/png" base64="..."--> ...
function KernelResultRenderer({ content }) {
    if (!content) return null;

    // Split content by our special tags
    // Regex to match <!--RENDER_IMAGE ...--> or <!--RENDER_HTML ...-->
    const parts = [];
    let lastIndex = 0;

    // Generic regex for robust parsing
    const tagRegex = /<!--RENDER_(IMAGE|HTML)\s+([^>]+)-->/g;

    let match;
    while ((match = tagRegex.exec(content)) !== null) {
        // Text before match
        if (match.index > lastIndex) {
            parts.push({ type: 'text', value: content.substring(lastIndex, match.index) });
        }

        const type = match[1];
        const attrsStr = match[2];

        if (type === 'IMAGE') {
            const mimeMatch = attrsStr.match(/mime="([^"]+)"/);
            const b64Match = attrsStr.match(/base64="([^"]+)"/);
            if (mimeMatch && b64Match) {
                parts.push({ type: 'image', mime: mimeMatch[1], src: b64Match[1] });
            }
        } else if (type === 'HTML') {
            const b64Match = attrsStr.match(/base64="([^"]+)"/);
            if (b64Match) {
                try {
                    const html = atob(b64Match[1]);
                    parts.push({ type: 'html', html: html });
                } catch (e) {
                    console.error("Failed to decode HTML", e);
                }
            }
        }

        lastIndex = match.index + match[0].length;
    }

    // Remaining text
    if (lastIndex < content.length) {
        parts.push({ type: 'text', value: content.substring(lastIndex) });
    }

    return (
        <div className="kernel-result-container">
            {parts.map((part, index) => {
                if (part.type === 'image') {
                    return (
                        <div key={index} className="kernel-image-output my-2">
                            <img
                                src={`data:${part.mime};base64,${part.src}`}
                                alt="Plot Output"
                                className="max-w-full rounded border border-gray-700 shadow-sm"
                            />
                        </div>
                    );
                } else if (part.type === 'html') {
                    return (
                        <div key={index} className="kernel-html-output my-2 overflow-x-auto"
                            dangerouslySetInnerHTML={{ __html: part.html }} />
                    );
                } else {
                    return <div key={index} className="whitespace-pre-wrap font-mono text-xs">{part.value}</div>;
                }
            })}
        </div>
    );
}
