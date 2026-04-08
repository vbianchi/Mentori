import { useState, useRef, useLayoutEffect, useEffect } from 'react';
import OmniHeader from '../ui/OmniHeader';
import GlobalStatus from '../ui/GlobalStatus';
import { SendHorizontal, Bot, Loader2, RefreshCw } from 'lucide-react';
import FollowUpChips from '../ui/FollowUpChips';
import '../ui/FollowUpChips.css';
import { UserMessage, AssistantMessage, ToolCard, PipelineErrorCard } from '../agentic/AgentCards';
import { PhaseIndicator } from '../agentic/PhaseIndicator';
import AnalysisCard from '../agentic/AnalysisCard';
import PlanCardV2 from '../agentic/PlanCardV2';
import StepCard from '../agentic/StepCard';
import CoderCard from '../agentic/CoderCard';
import CoderCardV2 from '../agentic/CoderCardV2';
import SynthesisCard from '../agentic/SynthesisCard';
import UserCard from '../agentic/UserCard';
import CollaborationCard from '../agentic/CollaborationCard';
import IconButton from '../primitives/IconButton';
import clsx from 'clsx';
import './CenterPanel.css';

/**
 * CenterPanel
 * The main interaction zone with new orchestrator card architecture.
 */
export default function CenterPanel({
    activity = "Ready",
    isProcessing = false,
    feedItems = [],
    onSendMessage,
    onStop,
    onCopyChat,
    onExportChat,
    onRegenerate,
    followUpSuggestions = [],
    activeTaskTokens,
    activeTaskName = null,
    activeTaskDisplayId = null,
    activeTaskId = null, // UUID for API calls
    connectionStatus = { backend: 'connected', tools: 'connected' },
    backendLogs = [],
    // Orchestrator props
    orchestratorPhase = null,
    isOrchestrated = false,
    stepStatuses = {},
    // Global thinking toggle
    globalThinkingOpen = true,
    onToggleGlobalThinking,
    // User info
    user = null
}) {
    const [showMarkdown, setShowMarkdown] = useState(true);
    const [isAgentic, setIsAgentic] = useState(false);
    const textareaRef = useRef(null);
    const feedContainerRef = useRef(null);
    const [inputValue, setInputValue] = useState("");

    // Local thinking state (syncs with global)
    const [thinkingOpen, setThinkingOpen] = useState(globalThinkingOpen);

    useEffect(() => {
        setThinkingOpen(globalThinkingOpen);
    }, [globalThinkingOpen]);

    // Auto-scroll feed
    useEffect(() => {
        if (feedContainerRef.current) {
            feedContainerRef.current.scrollTop = feedContainerRef.current.scrollHeight;
        }
    }, [feedItems]);

    // Auto-resize textarea
    useLayoutEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = "auto";
            textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 400) + "px";
        }
    }, [inputValue]);

    // Listen for external text insertion events (e.g. from FileTree)
    useEffect(() => {
        const handleInsertText = (e) => {
            const textToInsert = e.detail?.text;
            if (!textToInsert) return;

            const textarea = textareaRef.current;
            if (textarea) {
                const start = textarea.selectionStart;
                const end = textarea.selectionEnd;
                const currentVal = textarea.value;
                const newVal = currentVal.substring(0, start) + textToInsert + currentVal.substring(end);
                setInputValue(newVal);

                requestAnimationFrame(() => {
                    textarea.selectionStart = textarea.selectionEnd = start + textToInsert.length;
                    textarea.focus();
                });
            } else {
                setInputValue(prev => prev + textToInsert);
            }
        };

        window.addEventListener('mentori:insert-chat-text', handleInsertText);
        return () => window.removeEventListener('mentori:insert-chat-text', handleInsertText);
    }, []);

    const handleSend = () => {
        if (!inputValue.trim()) return;
        onSendMessage(inputValue, isAgentic);
        setInputValue("");
    };

    /**
     * Render a single feed item based on its type
     */
    const renderFeedItem = (item, idx) => {
        switch (item.type) {
            case 'user':
                const displayName = user?.first_name
                    ? `${user.first_name}${user.last_name ? ' ' + user.last_name : ''}`
                    : 'You';
                return <UserCard key={idx} content={item.content} showMarkdown={showMarkdown} userName={displayName} />;

            case 'analysis':
                return (
                    <AnalysisCard
                        key={idx}
                        thinking={item.thinking}
                        decision={item.decision}
                        decisionReason={item.decisionReason}
                        agentName={item.agentName}
                        agentModel={item.agentModel}
                        thinkingLevel={item.thinkingLevel}
                        isStreaming={item.isStreaming}
                        thinkingOpen={thinkingOpen}
                        onToggleThinking={setThinkingOpen}
                    />
                );

            case 'plan':
                return (
                    <PlanCardV2
                        key={idx}
                        plan={item.plan}
                        thinking={item.thinking}
                        stepStatuses={stepStatuses}
                        version={item.version || 1}
                        isSuperseded={item.isSuperseded || false}
                        isUpdated={item.isUpdated || false}
                        thinkingOpen={thinkingOpen}
                        onToggleThinking={setThinkingOpen}
                    />
                );

            case 'step':
                return (
                    <StepCard
                        key={idx}
                        stepId={item.stepId}
                        description={item.description}
                        agentRole={item.agentRole}
                        agentName={item.agentName}
                        agentModel={item.agentModel}
                        thinkingLevel={item.thinkingLevel}
                        status={item.status}
                        toolName={item.toolName}
                        toolInput={item.toolInput}
                        toolOutput={item.toolOutput}
                        toolProgress={item.toolProgress}
                        error={item.error}
                        evaluation={item.evaluation}
                        evaluationSummary={item.evaluationSummary}
                        isStreaming={item.isStreaming}
                        thinkingOpen={thinkingOpen}
                        onToggleThinking={setThinkingOpen}
                    />
                );

            case 'coder':
                return (
                    <CoderCard
                        key={idx}
                        stepId={item.stepId}
                        description={item.description}
                        agentName={item.agentName}
                        agentModel={item.agentModel}
                        thinkingLevel={item.thinkingLevel}
                        currentPhase={item.currentPhase}
                        algorithmThinking={item.algorithmThinking}
                        algorithmSteps={item.algorithmSteps}
                        algorithmStreaming={item.algorithmStreaming}
                        codeThinking={item.codeThinking}
                        generatedCode={item.generatedCode}
                        codeStreaming={item.codeStreaming}
                        executionResult={item.executionResult}
                        executionError={item.executionError}
                        attempt={item.attempt}
                        maxAttempts={item.maxAttempts}
                        retryError={item.retryError}
                        thinkingOpen={thinkingOpen}
                        onToggleThinking={setThinkingOpen}
                    />
                );

            case 'coder_v2':
                return (
                    <CoderCardV2
                        key={idx}
                        phase={item.phase}
                        algorithm={item.algorithm}
                        algorithmCellId={item.algorithmCellId}
                        steps={item.steps}
                        stepProgress={item.stepProgress}
                        currentStep={item.currentStep}
                        exports={item.exports}
                        summary={item.summary}
                    />
                );

            case 'synthesis':
                return (
                    <SynthesisCard
                        key={idx}
                        thinking={item.thinking}
                        content={item.content}
                        model={item.model}
                        agentName={item.agentName}
                        thinkingLevel={item.thinkingLevel}
                        isStreaming={item.isStreaming}
                        thinkingOpen={thinkingOpen}
                        onToggleThinking={setThinkingOpen}
                        showMarkdown={showMarkdown}
                    />
                );

            case 'collaboration':
                return (
                    <CollaborationCard
                        key={idx}
                        type={item.collaborationType}
                        data={item.data}
                        taskId={activeTaskId || item.taskId}
                        submitted={item.submitted}
                        userResponse={item.userResponse}
                    />
                );

            case 'pipeline_error':
                return (
                    <PipelineErrorCard
                        key={idx}
                        message={item.message}
                        severity={item.severity || 'error'}
                    />
                );

            case 'assistant':
                // Legacy assistant card (non-orchestrator mode)
                return (
                    <AssistantMessage
                        key={idx}
                        content={item.content}
                        model={item.model}
                        agentRole={item.agentRole}
                        showMarkdown={showMarkdown}
                        thinking={item.thinking}
                    />
                );

            case 'tool':
                // Legacy tool card (non-orchestrator mode or during step execution)
                return <ToolCard key={idx} {...item} />;

            default:
                return null;
        }
    };

    /**
     * Process feed items:
     * - For orchestrator mode: items are already properly typed (analysis, plan, step, synthesis)
     * - For legacy mode: merge thinking into assistant messages
     */
    const processedItems = [];
    let pendingThinking = null;

    feedItems.forEach((item, idx) => {
        if (item.type === 'thinking') {
            pendingThinking = item.content;
        } else if (item.type === 'assistant' && pendingThinking) {
            processedItems.push({ ...item, thinking: pendingThinking });
            pendingThinking = null;
        } else {
            processedItems.push(item);
        }
    });

    // Handle trailing thinking
    if (pendingThinking) {
        processedItems.push({
            type: 'assistant',
            content: '',
            thinking: pendingThinking,
            isThinkingOnly: true
        });
    }

    /**
     * Group items into conversation flows for visual separation
     */
    const flowGroups = [];
    let currentFlow = null;

    processedItems.forEach((item) => {
        if (item.type === 'user') {
            if (currentFlow) {
                flowGroups.push(currentFlow);
                flowGroups.push({ type: 'separator' });
            }
            currentFlow = { type: 'flow', messages: [item] };
        } else {
            if (currentFlow) {
                currentFlow.messages.push(item);
            } else {
                // Edge case: non-user item without preceding user message
                if (!currentFlow) {
                    currentFlow = { type: 'flow', messages: [] };
                }
                currentFlow.messages.push(item);
            }
        }
    });

    if (currentFlow) {
        flowGroups.push(currentFlow);
    }

    return (
        <div className="center-panel-container">
            {/* 1. Header */}
            <OmniHeader
                currentActivity={activity}
                isProcessing={isProcessing}
                onStopTask={onStop}
                onCopyChat={onCopyChat}
                onExportChat={onExportChat}
                tokenStats={activeTaskTokens}
                showMarkdown={showMarkdown}
                onToggleMarkdown={() => setShowMarkdown(!showMarkdown)}
                activeTaskName={activeTaskName}
                activeTaskDisplayId={activeTaskDisplayId}
                connectionStatus={connectionStatus}
                // Global thinking toggle
                thinkingOpen={thinkingOpen}
                onToggleThinking={() => {
                    const newState = !thinkingOpen;
                    setThinkingOpen(newState);
                    if (onToggleGlobalThinking) {
                        onToggleGlobalThinking(newState);
                    }
                }}
            />

            {/* 1.5 Global Status Bar */}
            <GlobalStatus activity={activity} isProcessing={isProcessing} logs={backendLogs} />

            {/* 1.75 Orchestrator Phase Indicator */}
            {isOrchestrated && orchestratorPhase && (
                <PhaseIndicator currentPhase={orchestratorPhase} />
            )}

            {/* 2. Feed (Timeline) */}
            <div
                ref={feedContainerRef}
                className="feed-container scroll-thin"
            >
                {flowGroups.length === 0 ? (
                    <div className="feed-placeholder text-muted">No messages yet. Start a conversation.</div>
                ) : (
                    <>
                        {flowGroups.map((group, groupIdx) => {
                            if (group.type === 'separator') {
                                return <div key={`sep-${groupIdx}`} className="turn-separator"></div>;
                            }

                            if (group.type === 'flow') {
                                return (
                                    <div key={`flow-${groupIdx}`} className="flow-wrapper">
                                        {group.messages.map((item, idx) => renderFeedItem(item, `${groupIdx}-${idx}`))}
                                    </div>
                                );
                            }

                            return renderFeedItem(group, groupIdx);
                        })}

                        {/* Inline Status Indicator - shown during processing */}
                        {isProcessing && (
                            <div className="inline-status">
                                <Loader2 size={14} className="inline-status-icon" />
                                <span className="inline-status-text">
                                    {activity || 'Working'}
                                    <span className="inline-status-dots">...</span>
                                </span>
                            </div>
                        )}
                    </>
                )}
            </div>

            {/* 2.5. Follow-up chips + Regenerate */}
            {!isProcessing && feedItems.length > 0 && (
                <div className="post-feed-actions">
                    {onRegenerate && feedItems.some(m => m.type === 'synthesis' || m.type === 'assistant') && (
                        <button className="regenerate-btn" onClick={onRegenerate} title="Regenerate last response">
                            <RefreshCw size={14} />
                            Regenerate
                        </button>
                    )}
                    <FollowUpChips
                        suggestions={followUpSuggestions}
                        onSelect={(text) => onSendMessage(text, false)}
                        disabled={isProcessing}
                    />
                </div>
            )}

            {/* 3. Input Area */}
            <div className="input-area glass-panel">
                <div className="input-wrapper">
                    <textarea
                        ref={textareaRef}
                        placeholder="Ask the agent or describe a task..."
                        className="chat-input scroll-thin"
                        rows={1}
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleSend();
                            }
                        }}
                    />

                    <IconButton
                        variant={isAgentic ? "primary" : "ghost"}
                        size="lg"
                        icon={<Bot size={22} />}
                        onClick={() => setIsAgentic(!isAgentic)}
                        title={isAgentic ? "Agentic Mode On" : "Enable Agentic Mode"}
                        className={clsx("flex-shrink-0", { "text-accent-primary": isAgentic })}
                    />
                    <button className="send-btn" onClick={handleSend} disabled={!inputValue.trim()}>
                        <SendHorizontal size={22} />
                    </button>
                </div>
            </div>
        </div>
    );
}
