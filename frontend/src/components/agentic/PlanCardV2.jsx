import React, { useState, useEffect } from 'react';
import { ClipboardList, ChevronRight, CheckCircle2, Loader2, AlertCircle, RefreshCw, Wrench, Copy, Check } from 'lucide-react';
import clsx from 'clsx';
import SmoothText from '../primitives/SmoothText';
import { copyToClipboard } from '../../utils/clipboard';
import './OrchestratorCards.css';

/**
 * Agent badge color configuration
 */
const AGENT_COLORS = {
    handyman: { bg: 'rgba(59, 130, 246, 0.2)', color: '#93c5fd' },
    coder: { bg: 'rgba(168, 85, 247, 0.2)', color: '#d8b4fe' },
    vision: { bg: 'rgba(16, 185, 129, 0.2)', color: '#6ee7b7' },
    editor: { bg: 'rgba(245, 158, 11, 0.2)', color: '#fcd34d' },
    lead_researcher: { bg: 'rgba(139, 92, 246, 0.2)', color: '#c4b5fd' },
    default: { bg: 'rgba(156, 163, 175, 0.2)', color: '#d1d5db' }
};

const AGENT_LABELS = {
    handyman: 'Handyman',
    coder: 'Coder',
    vision: 'Vision',
    editor: 'Editor',
    lead_researcher: 'Lead Researcher',
    default: 'Agent'
};

/**
 * AgentBadge - Displays agent role badge
 */
const AgentBadge = ({ agentRole }) => {
    const colors = AGENT_COLORS[agentRole] || AGENT_COLORS.default;
    const label = AGENT_LABELS[agentRole] || AGENT_LABELS.default;

    return (
        <span
            className="orchestrator-agent-badge"
            style={{ background: colors.bg, color: colors.color }}
        >
            {label}
        </span>
    );
};

/**
 * PlanCardV2 - Displays orchestrator execution plan
 *
 * Shows:
 * - Header with goal and version badge
 * - List of steps with status indicators
 * - Agent and tool badges for each step
 * - Supports dimmed state for superseded plans
 */
export default function PlanCardV2({
    plan,
    thinking = '',
    stepStatuses = {},
    version = 1,
    isSuperseded = false,
    isUpdated = false,
    thinkingOpen = true,
    onToggleThinking
}) {
    const [expanded, setExpanded] = useState(true);
    const [localOpen, setLocalOpen] = useState(thinkingOpen);
    const [copied, setCopied] = useState(false);

    // Sync with global toggle
    useEffect(() => {
        setLocalOpen(thinkingOpen);
    }, [thinkingOpen]);

    const handleToggle = (e) => {
        e.stopPropagation(); // Prevent card collapse
        const newState = !localOpen;
        setLocalOpen(newState);
        if (onToggleThinking) {
            onToggleThinking(newState);
        }
    };

    const handleCopy = async (e) => {
        e.stopPropagation(); // Prevent card collapse
        const stepsText = plan.steps?.map((step, idx) =>
            `${idx + 1}. ${step.description} (${step.agent_role} → ${step.tool_name})`
        ).join('\n') || '';
        const text = `Execution Plan v${version}\nGoal: ${plan.goal}\n\nSteps:\n${stepsText}`;
        await copyToClipboard(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    if (!plan) return null;

    const getStepStatus = (stepId) => {
        return stepStatuses[stepId] || 'pending';
    };

    const renderStepNumber = (idx, status) => {
        if (status === 'completed') {
            return <CheckCircle2 size={14} className="text-white" />;
        }
        if (status === 'running') {
            return <Loader2 size={14} className="text-white animate-spin" />;
        }
        if (status === 'failed') {
            return <AlertCircle size={14} className="text-white" />;
        }
        if (status === 'skipped') {
            return <span className="text-gray-500">-</span>;
        }
        return idx + 1;
    };

    return (
        <div className={clsx('orchestrator-card plan-card-v2 fade-in', {
            'plan-superseded': isSuperseded,
            'plan-updated': isUpdated
        })}>
            {/* Standardized Header */}
            <div className="orchestrator-header" onClick={() => setExpanded(!expanded)}>
                <div className={clsx('orchestrator-header-icon', isUpdated ? 'icon-orange' : 'icon-purple')}>
                    {isUpdated ? <RefreshCw size={16} /> : <ClipboardList size={16} />}
                </div>
                <div className="orchestrator-header-info">
                    <div className="orchestrator-header-primary">
                        <span className={clsx('orchestrator-header-agent', { 'text-amber-400': isUpdated })}>
                            {isUpdated ? 'Execution Plan (Updated)' : 'Execution Plan'}
                        </span>
                    </div>
                    <div className="orchestrator-header-secondary">{plan.goal}</div>
                </div>
                <div className="orchestrator-header-actions">
                    <span className={clsx('plan-version-badge', { 'version-superseded': isSuperseded })}>
                        v{version}{isSuperseded ? ' (superseded)' : ''}
                    </span>
                    <button
                        onClick={handleCopy}
                        className={clsx(
                            "orchestrator-copy-btn",
                            copied ? "copied text-green-400" : "text-white/40 hover:text-white"
                        )}
                        title={copied ? "Copied!" : "Copy Plan"}
                    >
                        {copied ? <Check size={14} /> : <Copy size={14} />}
                    </button>
                    <ChevronRight
                        size={16}
                        className={clsx('orchestrator-chevron', { 'expanded': expanded })}
                    />
                </div>
            </div>

            {expanded && (
                <>
                    {/* Thinking Section if present */}
                    {thinking && (
                        <div className="plan-thinking-wrapper" style={{ padding: '16px 16px 12px 16px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                            <div className="thinking-section">
                                <div className="thinking-header" onClick={handleToggle}>
                                    <span className={clsx('thinking-toggle-icon', { open: localOpen })}>
                                        <ChevronRight size={14} />
                                    </span>
                                    <span className="thinking-title">Planning Logic</span>
                                </div>
                                <div className={clsx('thinking-body', { collapsed: !localOpen })}>
                                    <SmoothText text={thinking} speed={5} />
                                </div>
                            </div>
                        </div>
                    )}

                    <div className="plan-steps-container">
                        {plan.steps?.map((step, idx) => {
                            const status = getStepStatus(step.step_id);
                            return (
                                <div
                                    key={step.step_id}
                                    className={clsx('plan-step-row', status, {
                                        'step-skipped': status === 'skipped' || isSuperseded
                                    })}
                                >
                                    <div className={clsx('plan-step-number', status)}>
                                        {renderStepNumber(idx, status)}
                                    </div>
                                    <div className="plan-step-content">
                                        <div className={clsx('plan-step-description', {
                                            'description-skipped': status === 'skipped' || isSuperseded
                                        })}>
                                            {step.description}
                                        </div>
                                        <div className="plan-step-meta">
                                            <AgentBadge agentRole={step.agent_role} />
                                            <span className="plan-tool-badge">
                                                <Wrench size={10} />
                                                {step.tool_name}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </>
            )}
        </div>
    );
}
