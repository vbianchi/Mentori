import React, { useState } from 'react';
import { Code2, Brain, Play, RefreshCw, CheckCircle2, AlertCircle, ChevronRight, FileText, ExternalLink, Loader2, Target, Clock, Layers } from 'lucide-react';
import clsx from 'clsx';
import './OrchestratorCards.css';

/**
 * CoderCardV2 - Display for the Coder V2 orchestrator-style agent
 *
 * Shows:
 * - Algorithm plan with numbered steps
 * - Step-by-step execution progress with scores
 * - Evaluation feedback and retry attempts
 * - Documentation export links
 * - Summary on completion
 */
export default function CoderCardV2({
    phase = 'algorithm', // 'algorithm' | 'executing' | 'complete'
    algorithm = {},
    algorithmCellId = null,
    steps = [],
    stepProgress = {},
    currentStep = null,
    exports = {},
    summary = null,
}) {
    const [algorithmOpen, setAlgorithmOpen] = useState(true);
    const [stepsOpen, setStepsOpen] = useState(true);

    // Derive status from phase
    const getStatus = () => {
        if (phase === 'complete') return 'completed';
        if (Object.values(stepProgress).some(s => s.status === 'failed')) return 'failed';
        return 'running';
    };

    const status = getStatus();

    // Count step statuses
    const completedSteps = Object.values(stepProgress).filter(s => s.status === 'completed').length;
    const totalSteps = steps.length;

    // Get score badge color
    const getScoreBadgeClass = (score) => {
        if (score >= 70) return 'badge-green';
        if (score >= 50) return 'badge-yellow';
        return 'badge-orange';
    };

    // Get step status icon
    const getStepIcon = (stepNum) => {
        const progress = stepProgress[stepNum];
        if (!progress) return <span className="step-number-badge pending">{stepNum}</span>;

        switch (progress.status) {
            case 'completed':
                return <CheckCircle2 size={16} className="text-green-400" />;
            case 'running':
                return <Loader2 size={16} className="animate-spin text-blue-400" />;
            case 'retrying':
                return <RefreshCw size={16} className="animate-spin text-yellow-400" />;
            case 'failed':
                return <AlertCircle size={16} className="text-red-400" />;
            default:
                return <span className="step-number-badge pending">{stepNum}</span>;
        }
    };

    return (
        <div className={clsx('orchestrator-card coder-card coder-v2-card fade-in', {
            'step-success': status === 'completed',
            'step-running': status === 'running',
            'step-failed': status === 'failed'
        })}>
            {/* Header */}
            <div className="orchestrator-header">
                <div className={clsx('step-status-icon', status)}>
                    {status === 'completed' && <CheckCircle2 size={18} className="text-white" />}
                    {status === 'running' && <Loader2 size={18} className="text-white animate-spin" />}
                    {status === 'failed' && <AlertCircle size={18} className="text-white" />}
                </div>
                <div className="orchestrator-header-info">
                    <div className="orchestrator-header-primary">
                        <span className="orchestrator-header-agent" style={{ color: '#c4b5fd' }}>
                            Notebook Coder V2
                        </span>
                        <span className="orchestrator-header-separator">•</span>
                        <span className="orchestrator-header-model">Orchestrator</span>
                    </div>
                    <div className="orchestrator-header-secondary">
                        {algorithm.goal || 'Executing notebook task'}
                    </div>
                </div>
                <div className="orchestrator-header-actions">
                    <span className={clsx('orchestrator-phase-badge', {
                        'badge-blue': phase === 'algorithm',
                        'badge-purple': phase === 'executing',
                        'badge-green': phase === 'complete',
                    })}>
                        {phase === 'algorithm' ? 'Planning' :
                         phase === 'executing' ? `${completedSteps}/${totalSteps}` :
                         'Complete'}
                    </span>
                </div>
            </div>

            {/* Body */}
            <div className="coder-card-body">
                {/* Algorithm Section */}
                {steps.length > 0 && (
                    <div className="coder-phase-section">
                        <div
                            className="coder-phase-header"
                            onClick={() => setAlgorithmOpen(!algorithmOpen)}
                        >
                            <span className={clsx('coder-phase-toggle', { open: algorithmOpen })}>
                                <ChevronRight size={14} />
                            </span>
                            <Brain size={14} />
                            <span>Algorithm ({steps.length} steps)</span>
                            {completedSteps === totalSteps && totalSteps > 0 && (
                                <CheckCircle2 size={12} className="text-green-400 ml-auto" />
                            )}
                        </div>
                        <div className={clsx('coder-phase-content coder-v2-algorithm', { collapsed: !algorithmOpen })}>
                            {steps.map((step, idx) => {
                                const stepNum = step.step_number || idx + 1;
                                return (
                                    <div key={stepNum} className="coder-v2-algorithm-step">
                                        <span className="step-number">{stepNum}.</span>
                                        <span className="step-description">{step.description || step}</span>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}

                {/* Step Progress Section */}
                {Object.keys(stepProgress).length > 0 && (
                    <div className="coder-phase-section">
                        <div
                            className="coder-phase-header"
                            onClick={() => setStepsOpen(!stepsOpen)}
                        >
                            <span className={clsx('coder-phase-toggle', { open: stepsOpen })}>
                                <ChevronRight size={14} />
                            </span>
                            <Play size={14} />
                            <span>Execution Progress</span>
                        </div>
                        <div className={clsx('coder-phase-content coder-v2-progress', { collapsed: !stepsOpen })}>
                            {Object.entries(stepProgress)
                                .sort(([a], [b]) => Number(a) - Number(b))
                                .map(([stepNum, progress]) => (
                                    <div
                                        key={stepNum}
                                        className={clsx('coder-v2-step-item', progress.status, {
                                            'current': Number(stepNum) === currentStep
                                        })}
                                    >
                                        <div className="step-header">
                                            <div className="step-icon">
                                                {getStepIcon(Number(stepNum))}
                                            </div>
                                            <div className="step-info">
                                                <span className="step-title">
                                                    Step {stepNum}: {progress.description || 'Executing...'}
                                                </span>
                                                {progress.expectedOutput && (
                                                    <span className="step-expected">
                                                        <Target size={10} />
                                                        {progress.expectedOutput}
                                                    </span>
                                                )}
                                            </div>
                                            {progress.score !== undefined && (
                                                <span className={clsx('score-badge', getScoreBadgeClass(progress.score))}>
                                                    {progress.score}
                                                </span>
                                            )}
                                        </div>

                                        {/* Feedback/Issues */}
                                        {progress.feedback && progress.status !== 'completed' && (
                                            <div className="step-feedback">
                                                {progress.feedback}
                                            </div>
                                        )}

                                        {/* Issues list */}
                                        {progress.issues && progress.issues.length > 0 && (
                                            <div className="step-issues">
                                                {progress.issues.map((issue, i) => (
                                                    <div key={i} className="issue-item">
                                                        <AlertCircle size={10} />
                                                        {issue}
                                                    </div>
                                                ))}
                                            </div>
                                        )}

                                        {/* Retry indicator */}
                                        {progress.status === 'retrying' && (
                                            <div className="step-retry">
                                                <RefreshCw size={12} />
                                                Retrying (attempt {progress.attempt}/{progress.maxRetries})
                                            </div>
                                        )}

                                        {/* Error */}
                                        {progress.error && (
                                            <div className="step-error">
                                                <AlertCircle size={12} />
                                                {progress.error}
                                            </div>
                                        )}

                                        {/* Variables/Files created */}
                                        {progress.status === 'completed' && (
                                            <div className="step-outputs">
                                                {progress.variablesCreated && progress.variablesCreated.length > 0 && (
                                                    <span className="output-tag vars">
                                                        <Code2 size={10} />
                                                        {progress.variablesCreated.join(', ')}
                                                    </span>
                                                )}
                                                {progress.filesCreated && progress.filesCreated.length > 0 && (
                                                    <span className="output-tag files">
                                                        <FileText size={10} />
                                                        {progress.filesCreated.join(', ')}
                                                    </span>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                ))}
                        </div>
                    </div>
                )}

                {/* Documentation Exports */}
                {Object.keys(exports).length > 0 && (
                    <div className="coder-phase-section">
                        <div className="coder-phase-header">
                            <FileText size={14} />
                            <span>Documentation</span>
                        </div>
                        <div className="coder-phase-content coder-v2-exports">
                            {Object.entries(exports).map(([format, path]) => (
                                <a
                                    key={format}
                                    href={path}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="export-link"
                                >
                                    <ExternalLink size={12} />
                                    {format.toUpperCase()}
                                </a>
                            ))}
                        </div>
                    </div>
                )}

                {/* Summary Section (when complete) */}
                {phase === 'complete' && summary && (
                    <div className="coder-phase-section summary-section">
                        <div className="coder-phase-header">
                            <Layers size={14} />
                            <span>Summary</span>
                        </div>
                        <div className="coder-phase-content coder-v2-summary">
                            <div className="summary-task">
                                {summary.task_summary}
                            </div>
                            <div className="summary-stats">
                                <div className="summary-stat">
                                    <CheckCircle2 size={14} />
                                    <span>{summary.steps_completed}/{summary.total_steps} steps</span>
                                </div>
                                <div className="summary-stat">
                                    <Code2 size={14} />
                                    <span>{summary.cells_created} cells</span>
                                </div>
                                {summary.execution_time > 0 && (
                                    <div className="summary-stat">
                                        <Clock size={14} />
                                        <span>{summary.execution_time}s</span>
                                    </div>
                                )}
                            </div>
                            {summary.files_created && summary.files_created.length > 0 && (
                                <div className="summary-files">
                                    <span className="summary-label">Files created:</span>
                                    {summary.files_created.map((file, i) => (
                                        <span key={i} className="summary-file">{file}</span>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
