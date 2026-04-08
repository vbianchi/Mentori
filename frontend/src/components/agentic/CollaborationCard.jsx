import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, ThumbsUp, ThumbsDown, AlertTriangle, Send, Check, X, Edit2, RefreshCw, SkipForward } from 'lucide-react';
import clsx from 'clsx';
import SmoothText from '../primitives/SmoothText';
import PlanCardV2 from './PlanCardV2';
import './OrchestratorCards.css';
import config from '../../config';

/**
 * CollaborationCard - Handles Human-in-the-Loop interactions
 * 
 * Supports:
 * - ask_user: User answers a question
 * - present_plan: User approves/rejects/modifies a plan
 * - share_progress: User gives feedback on progress
 * - report_failure: User decides next action on failure
 */
export default function CollaborationCard({
    type, // 'question' | 'approval' | 'update' | 'failure'
    data,
    taskId,
    onResponse, // Callback when user submits response
    // Props for reconstructed state (from page refresh)
    submitted: initialSubmitted = false,
    userResponse: initialUserResponse = null,
}) {
    const [response, setResponse] = useState(initialUserResponse || '');
    const [submitting, setSubmitting] = useState(false);
    const [submitted, setSubmitted] = useState(initialSubmitted);
    const [submittedAction, setSubmittedAction] = useState(initialSubmitted ? 'reply' : null);
    const [selectedOption, setSelectedOption] = useState(null);
    const [mode, setMode] = useState('view'); // 'view' | 'edit' (for plans)
    const textareaRef = useRef(null);

    // Auto-resize textarea based on content
    useEffect(() => {
        const textarea = textareaRef.current;
        if (textarea) {
            // Reset height to auto to get the correct scrollHeight
            textarea.style.height = 'auto';
            // Set to scrollHeight (content height) with a minimum
            const minHeight = 120;
            const maxHeight = 400;
            const newHeight = Math.min(Math.max(textarea.scrollHeight, minHeight), maxHeight);
            textarea.style.height = `${newHeight}px`;
        }
    }, [response]);

    const handleSubmit = async (payload) => {
        setSubmitting(true);
        try {
            // Determine tool name based on type if not present in data
            let toolName = data.tool;
            if (type === 'approval' && !toolName) {
                toolName = 'present_plan';
            }
            if (type === 'intervention' && !toolName) {
                toolName = 'report_failure';
            }
            if (type === 'question' && !toolName) {
                toolName = 'ask_user';
            }

            // Get auth token from localStorage
            const token = localStorage.getItem("mentori_token");

            const res = await fetch(`${config.API_BASE_URL}/tasks/${taskId}/collaborate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    task_id: taskId,
                    tool_name: toolName,
                    ...payload
                })
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || `HTTP ${res.status}`);
            }

            setSubmitted(true);
            setSubmittedAction(payload.action || 'reply');
            if (onResponse) onResponse(payload);
        } catch (error) {
            console.error('Failed to submit response:', error);
            setSubmitting(false);
        }
    };

    // --- Renderers for specific types ---

    const renderQuestion = () => {
        const { question, context, options, allow_freeform } = data.payload || {};

        if (submitted) {
            return (
                <>
                    {/* Standardized Header - Matching Mentori style */}
                    <div className="orchestrator-header">
                        <div className="orchestrator-header-icon icon-purple">
                            <MessageSquare size={16} />
                        </div>
                        <div className="orchestrator-header-info">
                            <div className="orchestrator-header-primary">
                                <span className="orchestrator-header-agent">Lead Researcher</span>
                                <span className="orchestrator-header-separator">•</span>
                                <span className="orchestrator-header-model">Question Answered</span>
                            </div>
                        </div>
                        <div className="orchestrator-header-actions">
                            <span className="orchestrator-phase-badge badge-green">Answered</span>
                        </div>
                    </div>
                    <div className="orchestrator-card-body">
                        <p className="text-base text-white/60 mb-3">{question}</p>
                        <div className="p-3 bg-accent-primary/10 rounded-lg border border-accent-primary/20 flex items-center gap-2 text-accent-primary">
                            <Check size={16} />
                            <span className="text-sm">Your answer: &quot;{response || selectedOption}&quot;</span>
                        </div>
                    </div>
                </>
            );
        }

        return (
            <>
                {/* Standardized Header - Matching Mentori style */}
                <div className="orchestrator-header">
                    <div className="orchestrator-header-icon icon-purple">
                        <MessageSquare size={16} />
                    </div>
                    <div className="orchestrator-header-info">
                        <div className="orchestrator-header-primary">
                            <span className="orchestrator-header-agent">Lead Researcher</span>
                            <span className="orchestrator-header-separator">•</span>
                            <span className="orchestrator-header-model">Needs Clarification</span>
                        </div>
                    </div>
                    <div className="orchestrator-header-actions">
                        <span className="orchestrator-phase-badge badge-purple">Question</span>
                    </div>
                </div>

                <div className="orchestrator-card-body space-y-4">
                    <p className="text-lg font-medium text-white leading-relaxed">{question}</p>

                    {context && (
                        <div className="bg-white/5 p-3 rounded-lg text-sm text-gray-300 border border-white/10">
                            <span className="text-gray-400 text-xs uppercase tracking-wide font-medium block mb-1">Context</span>
                            {context}
                        </div>
                    )}

                    {options && options.length > 0 && (
                        <div className="space-y-2">
                            <span className="text-gray-400 text-xs uppercase tracking-wide font-medium">Quick options</span>
                            <div className="flex flex-wrap gap-2">
                                {options.map((opt) => (
                                    <button
                                        key={opt}
                                        onClick={() => {
                                            setSelectedOption(opt);
                                            setResponse(opt);
                                        }}
                                        className={clsx(
                                            "px-4 py-2 rounded-lg border transition-all text-sm",
                                            response === opt
                                                ? "bg-accent-primary border-accent-primary text-black font-medium"
                                                : "bg-white/5 border-white/10 text-gray-300 hover:bg-white/10"
                                        )}
                                    >
                                        {opt}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {(allow_freeform !== false) && (
                        <textarea
                            ref={textareaRef}
                            value={response}
                            onChange={(e) => {
                                setResponse(e.target.value);
                                if (options?.includes(e.target.value)) setSelectedOption(e.target.value);
                                else setSelectedOption(null);
                            }}
                            placeholder="Type your answer here..."
                            className="w-full bg-[#0d0d12] border border-white/10 rounded-lg p-4 text-white text-base leading-relaxed focus:ring-2 focus:ring-accent-primary focus:border-accent-primary outline-none min-h-[120px] resize-none placeholder:text-gray-500 transition-all"
                            style={{ overflow: 'hidden' }}
                            autoFocus
                        />
                    )}

                    <button
                        onClick={() => handleSubmit({ response: response, action: 'reply' })}
                        disabled={!response.trim() || submitting}
                        className="btn-success w-full flex items-center justify-center gap-2 py-2.5 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {submitting ? 'Sending...' : <><Send size={16} /> Send Answer</>}
                    </button>
                </div>
            </>
        );
    };

    const renderPlanApproval = () => {
        const { plan, reasoning } = data;

        if (submitted) {
            return (
                <>
                    <div className="orchestrator-header">
                        <div className="orchestrator-header-icon icon-amber">
                            <AlertTriangle size={16} />
                        </div>
                        <div className="orchestrator-header-info">
                            <div className="orchestrator-header-primary">
                                <span className="orchestrator-header-agent">Lead Researcher</span>
                                <span className="orchestrator-header-separator">•</span>
                                <span className="orchestrator-header-model">Plan Review</span>
                            </div>
                        </div>
                        <div className="orchestrator-header-actions">
                            <span className={clsx("orchestrator-phase-badge", submittedAction === 'approve' ? "badge-green" : "badge-red")}>
                                {submittedAction === 'approve' ? 'Approved' : 'Rejected'}
                            </span>
                        </div>
                    </div>
                    <div className="orchestrator-card-body">
                        <div className="mb-4 opacity-50 pointer-events-none">
                            <PlanCardV2 plan={plan} thinking={reasoning} thinkingOpen={false} />
                        </div>
                        <div className={clsx(
                            "p-3 rounded-lg border flex items-center gap-2 font-medium justify-center text-sm",
                            submittedAction === 'approve'
                                ? 'bg-green-500/10 border-green-500/20 text-green-400'
                                : 'bg-red-500/10 border-red-500/20 text-red-400'
                        )}>
                            {submittedAction === 'approve' ? <Check size={16} /> : <X size={16} />}
                            <span>Plan {submittedAction === 'approve' ? 'Approved' : 'Rejected'}</span>
                        </div>
                    </div>
                </>
            );
        }

        return (
            <>
                <div className="orchestrator-header">
                    <div className="orchestrator-header-icon icon-amber">
                        <AlertTriangle size={16} />
                    </div>
                    <div className="orchestrator-header-info">
                        <div className="orchestrator-header-primary">
                            <span className="orchestrator-header-agent">Lead Researcher</span>
                            <span className="orchestrator-header-separator">•</span>
                            <span className="orchestrator-header-model">Awaiting Approval</span>
                        </div>
                    </div>
                    <div className="orchestrator-header-actions">
                        <span className="orchestrator-phase-badge badge-amber">Approval</span>
                    </div>
                </div>

                <div className="orchestrator-card-body space-y-4">
                    <p className="text-gray-300 text-sm">
                        Review the proposed execution plan before proceeding.
                    </p>

                    {/* Embed PlanCardV2 for preview */}
                    <div className="rounded-lg overflow-hidden border border-white/10">
                        <PlanCardV2 plan={plan} thinking={reasoning} thinkingOpen={false} />
                    </div>

                    <div className="flex gap-3">
                        <button
                            onClick={() => handleSubmit({ action: 'approve', response: 'Approved' })}
                            disabled={submitting}
                            className="btn-success flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-medium disabled:opacity-50"
                        >
                            <Check size={16} /> Approve
                        </button>

                        <button
                            onClick={() => {
                                // TODO: Implement modify mode
                                alert("Modification not implemented in this MVP yet.");
                            }}
                            disabled={submitting}
                            className="btn-secondary flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-medium disabled:opacity-50"
                        >
                            <Edit2 size={16} /> Modify
                        </button>

                        <button
                            onClick={() => handleSubmit({ action: 'reject', response: 'Rejected' })}
                            disabled={submitting}
                            className="btn-danger flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-medium disabled:opacity-50"
                        >
                            <X size={16} /> Reject
                        </button>
                    </div>
                </div>
            </>
        );
    };

    const renderIntervention = () => {
        const { step_description, reason, issues, attempts } = data;

        if (submitted) {
            const labels = { retry: 'Retrying', skip: 'Skipped', abort: 'Aborted' };
            const colors = { retry: 'badge-amber', skip: 'badge-green', abort: 'badge-red' };
            return (
                <>
                    <div className="orchestrator-header">
                        <div className="orchestrator-header-icon icon-red">
                            <AlertTriangle size={16} />
                        </div>
                        <div className="orchestrator-header-info">
                            <div className="orchestrator-header-primary">
                                <span className="orchestrator-header-agent">Supervisor</span>
                                <span className="orchestrator-header-separator">•</span>
                                <span className="orchestrator-header-model">Step Failed</span>
                            </div>
                        </div>
                        <div className="orchestrator-header-actions">
                            <span className={`orchestrator-phase-badge ${colors[submittedAction] || 'badge-amber'}`}>
                                {labels[submittedAction] || submittedAction}
                            </span>
                        </div>
                    </div>
                    <div className="orchestrator-card-body">
                        <p className="text-sm text-white/60">{step_description}</p>
                    </div>
                </>
            );
        }

        return (
            <>
                <div className="orchestrator-header">
                    <div className="orchestrator-header-icon icon-red">
                        <AlertTriangle size={16} />
                    </div>
                    <div className="orchestrator-header-info">
                        <div className="orchestrator-header-primary">
                            <span className="orchestrator-header-agent">Supervisor</span>
                            <span className="orchestrator-header-separator">•</span>
                            <span className="orchestrator-header-model">Step Failed — Your Decision</span>
                        </div>
                    </div>
                    <div className="orchestrator-header-actions">
                        <span className="orchestrator-phase-badge badge-red">Intervention</span>
                    </div>
                </div>

                <div className="orchestrator-card-body space-y-4">
                    <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 space-y-2">
                        <p className="text-sm font-medium text-red-300">{reason}</p>
                        {step_description && (
                            <p className="text-xs text-white/50">Step: {step_description}</p>
                        )}
                        {issues && issues.length > 0 && (
                            <ul className="text-xs text-white/60 space-y-1 list-disc list-inside">
                                {issues.map((issue, i) => <li key={i}>{issue}</li>)}
                            </ul>
                        )}
                    </div>

                    <p className="text-xs text-gray-400">
                        This step failed after {attempts} attempt{attempts !== 1 ? 's' : ''}. Choose how to proceed:
                    </p>

                    <div className="flex gap-3">
                        <button
                            onClick={() => handleSubmit({ action: 'retry', response: 'Retry this step' })}
                            disabled={submitting}
                            className="btn-secondary flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-medium disabled:opacity-50"
                        >
                            <RefreshCw size={15} /> Retry
                        </button>

                        <button
                            onClick={() => handleSubmit({ action: 'skip', response: 'Skip this step' })}
                            disabled={submitting}
                            className="btn-secondary flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-medium disabled:opacity-50"
                        >
                            <SkipForward size={15} /> Skip
                        </button>

                        <button
                            onClick={() => handleSubmit({ action: 'abort', response: 'Abort task' })}
                            disabled={submitting}
                            className="btn-danger flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-medium disabled:opacity-50"
                        >
                            <X size={15} /> Abort
                        </button>
                    </div>
                </div>
            </>
        );
    };

    return (
        <div className="orchestrator-card collaboration-card fade-in">
            {type === 'question' && renderQuestion()}
            {type === 'approval' && renderPlanApproval()}
            {type === 'intervention' && renderIntervention()}
        </div>
    );
}
