import React, { useState, useEffect } from 'react';
import { Code2, Brain, Play, RefreshCw, CheckCircle2, AlertCircle, ChevronRight, Copy, Check, Loader2 } from 'lucide-react';
import clsx from 'clsx';
import SmoothText from '../primitives/SmoothText';
import { copyToClipboard } from '../../utils/clipboard';
import './OrchestratorCards.css';

/**
 * CoderCard - Multi-phase display for the Coder Agent
 *
 * Shows:
 * - Phase 1: Algorithm Design (thinking + steps)
 * - Phase 2: Code Generation (with syntax highlighting)
 * - Phase 3: Execution (result or error)
 * - Retry attempts if any
 */
export default function CoderCard({
    stepId,
    description,
    agentName = 'Coder Agent',
    agentModel = 'Model',
    thinkingLevel = null,
    // Phase states
    currentPhase = 'algorithm', // 'algorithm' | 'generation' | 'execution' | 'complete' | 'failed'
    // Algorithm phase
    algorithmThinking = '',
    algorithmSteps = [],
    algorithmStreaming = false,
    // Code generation phase
    codeThinking = '',
    generatedCode = '',
    codeStreaming = false,
    // Execution phase
    executionResult = '',
    executionError = null,
    // Retry tracking
    attempt = 1,
    maxAttempts = 3,
    retryError = null,
    // UI controls
    thinkingOpen = true,
    onToggleThinking,
}) {
    const [algorithmOpen, setAlgorithmOpen] = useState(thinkingOpen);
    const [codeOpen, setCodeOpen] = useState(true);
    const [copied, setCopied] = useState(false);

    // Sync with global toggle
    useEffect(() => {
        setAlgorithmOpen(thinkingOpen);
    }, [thinkingOpen]);

    const handleCopyCode = async () => {
        await copyToClipboard(generatedCode);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    // Determine overall status
    const getStatus = () => {
        if (currentPhase === 'complete') return 'completed';
        if (currentPhase === 'failed') return 'failed';
        return 'running';
    };

    const status = getStatus();

    // Phase indicators
    const phases = [
        { key: 'algorithm', label: 'Algorithm', icon: Brain },
        { key: 'generation', label: 'Code', icon: Code2 },
        { key: 'execution', label: 'Execute', icon: Play },
    ];

    const getPhaseStatus = (phaseKey) => {
        const phaseOrder = ['algorithm', 'generation', 'execution', 'complete', 'failed'];
        const currentIndex = phaseOrder.indexOf(currentPhase);
        const phaseIndex = phaseOrder.indexOf(phaseKey);

        if (currentPhase === 'failed') {
            // Find which phase failed
            if (phaseIndex < currentIndex) return 'completed';
            return 'failed';
        }

        if (phaseIndex < currentIndex) return 'completed';
        if (phaseIndex === currentIndex) return 'active';
        return 'pending';
    };

    return (
        <div className={clsx('orchestrator-card coder-card fade-in', {
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
                        <span className="orchestrator-header-agent" style={{ color: '#d8b4fe' }}>
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
                    <span className={clsx('orchestrator-phase-badge', {
                        'badge-blue': status === 'running',
                        'badge-green': status === 'completed',
                        'badge-orange': status === 'failed',
                    })}>
                        {status === 'running' ? 'Coding' : status === 'completed' ? 'Done' : 'Failed'}
                    </span>
                    <span className="orchestrator-header-model">{stepId}</span>
                </div>
            </div>

            {/* Phase Progress Indicator */}
            <div className="coder-phase-progress">
                {phases.map((phase, idx) => {
                    const phaseStatus = getPhaseStatus(phase.key);
                    const Icon = phase.icon;
                    return (
                        <React.Fragment key={phase.key}>
                            <div className={clsx('coder-phase-item', phaseStatus)}>
                                <div className="coder-phase-icon">
                                    {phaseStatus === 'completed' ? (
                                        <CheckCircle2 size={14} />
                                    ) : phaseStatus === 'active' ? (
                                        <Loader2 size={14} className="animate-spin" />
                                    ) : (
                                        <Icon size={14} />
                                    )}
                                </div>
                                <span className="coder-phase-label">{phase.label}</span>
                            </div>
                            {idx < phases.length - 1 && (
                                <div className={clsx('coder-phase-connector', {
                                    'completed': getPhaseStatus(phases[idx + 1].key) !== 'pending'
                                })} />
                            )}
                        </React.Fragment>
                    );
                })}
            </div>

            {/* Body - Phase Content */}
            <div className="coder-card-body">
                {/* Algorithm Phase */}
                {(algorithmThinking || algorithmSteps.length > 0) && (
                    <div className="coder-phase-section">
                        <div
                            className="coder-phase-header"
                            onClick={() => setAlgorithmOpen(!algorithmOpen)}
                        >
                            <span className={clsx('coder-phase-toggle', { open: algorithmOpen })}>
                                <ChevronRight size={14} />
                            </span>
                            <Brain size={14} />
                            <span>Algorithm Design</span>
                            {getPhaseStatus('algorithm') === 'completed' && (
                                <CheckCircle2 size={12} className="text-green-400 ml-auto" />
                            )}
                        </div>
                        <div className={clsx('coder-phase-content', { collapsed: !algorithmOpen })}>
                            {algorithmThinking && (
                                <div className="coder-thinking">
                                    <SmoothText text={algorithmThinking} speed={5} />
                                    {algorithmStreaming && <span className="streaming-cursor">|</span>}
                                </div>
                            )}
                            {algorithmSteps.length > 0 && (
                                <div className="coder-algorithm-steps">
                                    {algorithmSteps.map((step, idx) => (
                                        <div key={idx} className="coder-algorithm-step">
                                            <span className="step-number">{idx + 1}</span>
                                            <span className="step-text">{step}</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Code Generation Phase */}
                {(generatedCode || codeThinking || currentPhase === 'generation') && (
                    <div className="coder-phase-section">
                        <div
                            className="coder-phase-header"
                            onClick={() => setCodeOpen(!codeOpen)}
                        >
                            <span className={clsx('coder-phase-toggle', { open: codeOpen })}>
                                <ChevronRight size={14} />
                            </span>
                            <Code2 size={14} />
                            <span>Generated Code</span>
                            {generatedCode && (
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        handleCopyCode();
                                    }}
                                    className={clsx(
                                        "ml-auto coder-copy-btn",
                                        copied ? "text-green-400" : "text-white/40 hover:text-white"
                                    )}
                                    title={copied ? "Copied!" : "Copy Code"}
                                >
                                    {copied ? <Check size={12} /> : <Copy size={12} />}
                                </button>
                            )}
                        </div>
                        <div className={clsx('coder-phase-content', { collapsed: !codeOpen })}>
                            {codeThinking && (
                                <div className="coder-thinking">
                                    <SmoothText text={codeThinking} speed={5} />
                                    {codeStreaming && !generatedCode && <span className="streaming-cursor">|</span>}
                                </div>
                            )}
                            {generatedCode ? (
                                <pre className="coder-code-block">
                                    <code>{generatedCode}</code>
                                </pre>
                            ) : currentPhase === 'generation' && (
                                <div className="coder-code-loading">
                                    <Loader2 size={16} className="animate-spin" />
                                    <span>Generating code...</span>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Retry Indicator */}
                {attempt > 1 && (
                    <div className="coder-retry-indicator">
                        <RefreshCw size={14} />
                        <span>Retry attempt {attempt} of {maxAttempts}</span>
                        {retryError && (
                            <span className="retry-error-hint" title={retryError}>
                                - fixing previous error
                            </span>
                        )}
                    </div>
                )}

                {/* Execution Phase */}
                {(executionResult || executionError || currentPhase === 'execution') && (
                    <div className="coder-phase-section">
                        <div className="coder-phase-header">
                            <Play size={14} />
                            <span>Execution Result</span>
                        </div>
                        <div className="coder-phase-content">
                            {currentPhase === 'execution' && !executionResult && !executionError && (
                                <div className="coder-execution-loading">
                                    <Loader2 size={16} className="animate-spin" />
                                    <span>Executing code...</span>
                                </div>
                            )}
                            {executionError && (
                                <div className="coder-execution-error">
                                    <AlertCircle size={14} />
                                    <span>{executionError}</span>
                                </div>
                            )}
                            {executionResult && !executionError && (
                                <div className="coder-execution-success">
                                    <pre>{executionResult}</pre>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
