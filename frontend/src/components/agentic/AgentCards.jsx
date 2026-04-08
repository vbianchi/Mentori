import React, { useState, useMemo } from 'react';
import { User, BrainCircuit, Terminal, CheckCircle2, Copy, ChevronDown, ChevronRight, Bot, Loader2, AlertCircle, ClipboardCheck, Circle, ClipboardList, Wrench, ArrowUpRight, ArrowDownLeft, AlertTriangle } from 'lucide-react';
import clsx from 'clsx';
import config from '../../config';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeHighlight from 'rehype-highlight';
import rehypeKatex from 'rehype-katex';
import 'highlight.js/styles/atom-one-dark.css'; // Good default, override via CSS if needed
import { copyToClipboard } from '../../utils/clipboard';
import { remarkCitations } from '../../utils/remarkCitations';
import { parseSources } from '../../utils/parseSources';
import { CitationTooltip } from '../ui/CitationTooltip';
import './OrchestratorCards.css'; // MIGRATED: Use new CSS
import './Markdown.css';

/**
 * Copy Button Helper
 */
const CopyButton = ({ text, className }) => {
    const [copied, setCopied] = useState(false);

    const handleCopy = async (e) => {
        e.stopPropagation();
        try {
            await copyToClipboard(text);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    };

    return (
        <button
            className={clsx("cursor-pointer bg-transparent border-0 p-1 rounded hover:bg-white/10 text-gray-500 hover:text-white transition-all", className)}
            onClick={handleCopy}
            title={copied ? "Copied!" : "Copy Content"}
        >
            {copied ? <ClipboardCheck size={14} className="text-green-500 font-bold" /> : <Copy size={14} />}
        </button>
    );
};

/**
 * Custom Code Block Renderer
 * Adds a header with language and copy button.
 */
const PreBlock = ({ children, ...props }) => {
    if (!children || !children.props) return <pre {...props}>{children}</pre>;

    // Extract code content and language
    const codeProps = children.props;
    const className = codeProps.className || "";
    const language = className.replace("language-", "") || "text";
    // Get raw code content without trailing newline
    const content = String(codeProps.children || '').replace(/\n$/, "");

    return (
        <div className="code-block-wrapper my-4 rounded-lg border border-white/10 overflow-hidden bg-slate-950">
            <div className="code-header flex items-center justify-between px-3 py-2 bg-white/5 border-b border-white/5">
                <span className="text-xs font-mono text-muted uppercase tracking-wider">{language}</span>
                <CopyButton text={content} className="hover:text-white" />
            </div>
            <div className="code-body overflow-x-auto">
                <pre {...props} className="!m-0 !bg-transparent !border-0 !shadow-none">
                    {children}
                </pre>
            </div>
        </div>
    );
};

/**
 * Base Card Wrapper - Adapted to Orchestrator Styles
 */
const BaseCard = ({ children, role, className, header, contentForCopy }) => {

    // Map role to specific card class if needed, or default to generic orchestrator-card
    const cardClass = role === 'user' ? 'orchestrator-card user-card' :
        role === 'assistant' ? 'orchestrator-card step-card' : // Assistant messages look like steps/synthesis
            role === 'tool' ? 'orchestrator-card step-card' : // Tools look like steps
                'orchestrator-card';

    return (
        <div className={clsx(cardClass, className, "fade-in")}>
            {/* Header */}
            <div className="step-card-header" style={{ justifyContent: 'space-between', background: role === 'user' ? 'var(--orch-bg-secondary)' : 'var(--orch-bg-tertiary)' }}>
                {header}
                <div className="flex-shrink-0 ml-1.5">
                    <CopyButton text={contentForCopy} />
                </div>
            </div>

            {/* Main Content */}
            <div className="step-card-body">
                {children}
            </div>
        </div>
    );
};


/**
 * User Message Card
 * @param {string} content - The message content
 * @param {boolean} showMarkdown - Whether to render markdown
 * @param {string} userName - Optional username to display (defaults to "You")
 */
export const UserMessage = ({ content, showMarkdown = true, userName = "This is you" }) => {
    const headerContent = (
        <div className="flex items-center gap-2">
            <div className="user-avatar">
                <User size={14} />
            </div>
            <span className="user-badge">
                {userName}
            </span>
        </div>
    );

    return (
        <div className="orchestrator-card user-card fade-in">
            <div className="user-card-header" style={{ justifyContent: 'space-between' }}>
                {headerContent}
                <CopyButton text={content} />
            </div>
            <div className="user-card-content">
                <div className={clsx("message-text", { "font-mono text-xs": !showMarkdown })}>
                    {showMarkdown ? (
                        <div className="markdown-content">
                            <ReactMarkdown
                                remarkPlugins={[remarkGfm, remarkMath]}
                                rehypePlugins={[rehypeHighlight, rehypeKatex]}
                                components={{
                                    pre: PreBlock
                                }}
                            >
                                {content}
                            </ReactMarkdown>
                        </div>
                    ) : (
                        content
                    )}
                </div>
            </div>
        </div>
    );
};

/**
 * Thinking Card (Collapsible) - Reusing Orchestrator Logic
 */
export const ThinkingCard = ({ content, isOpen = false }) => {
    const [expanded, setExpanded] = useState(isOpen);
    if (!content) return null;

    return (
        <div className="thinking-section">
            <div className="thinking-header" onClick={() => setExpanded(!expanded)}>
                <span className={clsx("thinking-toggle-icon", { "open": expanded })}>
                    <ChevronRight size={14} />
                </span>
                <span className="thinking-title">Thinking Process</span>
            </div>
            <div className={clsx("thinking-body", { "collapsed": !expanded })}>
                {content}
            </div>
        </div>
    );
};

/**
 * To-do tool visualization - updated to match Orchestrator look
 */
const TodoCardVisualization = ({ data }) => {
    if (!data || data.error) {
        return <div className="text-red-400 text-sm">{data?.error || "Invalid todo data"}</div>;
    }

    return (
        <div className="mt-2 text-sm">
            <div className="flex items-center gap-2 mb-3 pb-2 border-b border-white/10">
                <ClipboardList size={16} className="text-purple-400" />
                <span className="font-semibold text-gray-200">{data.title || "Execution Plan"}</span>
                <span className="ml-auto text-xs text-gray-400 bg-white/5 px-2 py-0.5 rounded font-mono">
                    {data.todo_id?.slice(0, 8) || "---"}
                </span>
            </div>

            <div className="space-y-2">
                {data.steps?.map((step, idx) => (
                    <div key={step.id || idx} className="py-2 border-b border-white/5 last:border-0">
                        <div className="flex items-center gap-3">
                            <div className="w-5 h-5 flex items-center justify-center">
                                {step.status === 'completed' ? <CheckCircle2 size={14} className="text-green-500" /> :
                                    step.status === 'in_progress' ? <Loader2 className="w-4 h-4 text-blue-400 animate-spin" /> :
                                        step.status === 'failed' ? <AlertCircle className="w-4 h-4 text-red-500" /> :
                                            <Circle className="w-4 h-4 text-gray-600" />}
                            </div>
                            <span className={clsx("flex-grow", step.status === 'completed' ? "text-gray-500 line-through" : "text-gray-300")}>
                                {step.title}
                            </span>
                            <span className="text-xs px-2 py-0.5 rounded bg-white/5 text-gray-400">
                                {step.assigned_agent}
                            </span>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

const TODO_TOOLS = ['create_todo_card', 'update_todo_step', 'get_todo_card', 'get_todo_context', 'add_todo_step', 'remove_todo_step'];

/**
 * Tool Execution Card - Migrated to Orchestrator Style
 */
export const ToolCard = ({ toolName, input, output, content, name, status = 'success', agentRole }) => {
    const finalOutput = output || content || "(No output)";
    const finalInput = input || "(Arguments Hidden)";
    const finalName = toolName || name || "Tool";

    // Resolve Agent Name
    const agentLabel = AGENT_ROLE_LABELS[agentRole] || agentRole || null;
    const displayName = agentLabel ? `[${agentLabel}] ${finalName}` : finalName;

    const isTodoTool = TODO_TOOLS.includes(finalName);
    const [expanded, setExpanded] = useState(status === 'running' || isTodoTool);

    let todoData = null;
    if (isTodoTool && finalOutput && finalOutput !== "(No output)") {
        try {
            todoData = JSON.parse(finalOutput);
        } catch (e) { }
    }

    const fullContentForCopy = `[Tool: ${finalName}]\n\n[Input]\n${finalInput}\n\n[Output]\n${finalOutput}`;

    let StatusIcon = CheckCircle2;
    let statusColor = "text-green-500"; // --orch-success

    if (status === 'running') {
        StatusIcon = Loader2;
        statusColor = "text-blue-400 animate-spin"; // --orch-info
    } else if (status === 'error' || (finalOutput && finalOutput.startsWith && finalOutput.startsWith("Error"))) {
        StatusIcon = AlertCircle;
        statusColor = "text-red-500"; // --orch-error
    }

    const HeaderIcon = isTodoTool ? ClipboardList : null;

    const header = (
        <div className="flex items-center gap-2 w-full cursor-pointer" onClick={() => setExpanded(!expanded)}>
            <ChevronRight size={12} className={clsx("transition-transform text-gray-500", { "rotate-90": expanded })} />
            <StatusIcon size={14} className={statusColor} />
            {HeaderIcon && <HeaderIcon size={14} className="text-purple-400" />}
            <span className="font-mono text-xs font-semibold text-purple-400">{displayName}</span>
        </div>
    );

    return (
        <BaseCard role="tool" header={header} contentForCopy={fullContentForCopy}>
            {expanded && (
                <div className="mt-2 animated-expand">
                    {isTodoTool && todoData && todoData.steps ? (
                        <TodoCardVisualization data={todoData} />
                    ) : (
                        <>
                            {/* Input */}
                            <div className="tool-section">
                                <div className="tool-section-header">
                                    <ArrowUpRight size={12} />
                                    <span>IN</span>
                                </div>
                                <div className="tool-call-box">
                                    <code className="text-dim">{finalInput}</code>
                                </div>
                            </div>

                            {/* Output */}
                            <div className="tool-section">
                                <div className="tool-section-header">
                                    <ArrowDownLeft size={12} />
                                    <span>OUT</span>
                                </div>
                                <div className="tool-result-box">
                                    {status === 'running' ? (
                                        <div className="flex items-center gap-2 text-gray-500 italic">
                                            <Loader2 size={14} className="animate-spin" />
                                            Running...
                                        </div>
                                    ) : (
                                        <code>{finalOutput}</code>
                                    )}
                                </div>
                            </div>
                        </>
                    )}
                </div>
            )}
        </BaseCard>
    );
};

const AGENT_ROLE_LABELS = {
    lead_researcher: 'Research Leader',
    coder: 'Coder Agent',
    handyman: 'Handyman Agent',
    editor: 'Editor Agent',
    transcriber: 'Transcriber Agent',
    vision: 'Vision Agent',
    default: 'Default Agent'
};

const parseModelThinking = (model) => {
    if (!model) return { baseModel: null, isThinking: false, thinkLevel: null };
    let modelPart = model.split('::').pop();
    const thinkMatch = modelPart.match(/\[think(?::(\w+))?\]$/);
    if (thinkMatch) {
        const baseModel = modelPart.replace(/\[think(?::\w+)?\]$/, '');
        const thinkLevel = thinkMatch[1] || null;
        return { baseModel, isThinking: true, thinkLevel };
    }
    return { baseModel: modelPart, isThinking: false, thinkLevel: null };
};

/**
 * Final Result / Assistant Message
 * Now mimics step-card / synthesis-card style
 */
export const AssistantMessage = ({ content, model, agentRole, showMarkdown = true, thinking }) => {
    const fullContentForCopy = thinking
        ? `[Thinking Process]\n${thinking}\n\n[Response]\n${content}`
        : content;

    const sources = useMemo(() => parseSources(content), [content]);

    const { baseModel, isThinking, thinkLevel } = parseModelThinking(model);

    // Map role to badge style
    const roleConfig = {
        handyman: 'agent-badge-handyman',
        coder: 'agent-badge-coder',
        vision: 'agent-badge-vision',
        editor: 'agent-badge-editor',
        lead_researcher: 'agent-badge-lead',
        transcriber: 'agent-badge-transcriber',
        default: 'agent-badge-default'
    };
    const badgeClass = roleConfig[agentRole] || 'agent-badge-default';
    const roleName = AGENT_ROLE_LABELS[agentRole] || agentRole || 'Agent';
    const modelName = baseModel || 'Model';

    const header = (
        <div className="flex items-center gap-2 flex-wrap">
            <span className={clsx("orchestrator-agent-badge", badgeClass)}>
                {roleName}
            </span>
            <span className="text-xs bg-white/5 border border-white/10 px-1.5 py-0.5 rounded font-mono text-gray-400">
                {modelName}
            </span>
            {isThinking && (
                <span className="text-[10px] uppercase font-bold tracking-wider text-purple-400 border border-purple-500/30 px-1 rounded bg-purple-500/10">
                    Thinking
                    {thinkLevel && `:${thinkLevel}`}
                </span>
            )}
        </div>
    );

    return (
        <BaseCard role="assistant" header={header} contentForCopy={fullContentForCopy}>
            {thinking && (
                <ThinkingCard content={thinking} isOpen={false} />
            )}

            {content && (
                <div className={clsx("message-text", { "font-mono text-xs": !showMarkdown })}>
                    {showMarkdown ? (
                        <div className="markdown-content">
                            <ReactMarkdown
                                remarkPlugins={[remarkGfm, remarkMath, remarkCitations]}
                                rehypePlugins={[rehypeHighlight, rehypeKatex]}
                                components={{
                                    pre: PreBlock,
                                    citation: ({ node, number, children }) => (
                                        <CitationTooltip number={number} sources={sources} />
                                    ),
                                }}
                            >
                                {content}
                            </ReactMarkdown>
                        </div>
                    ) : (
                        <div className="whitespace-pre-wrap">{content}</div>
                    )}
                </div>
            )}
        </BaseCard>
    );
};

const OrchestratorAgentBadge = ({ agentRole }) => {
    // Reusing the AssistantMessage logic effectively
    return null; // Not needed as exported component for now, or adapt if needed
};

/**
 * PipelineErrorCard — shown when the orchestrator or backend emits an error event.
 * Replaces the broken "Agent | System" card that used to appear for errors.
 */
export const PipelineErrorCard = ({ message, severity = 'error' }) => {
    const isInfo = severity === 'info';
    return (
        <div className={`pipeline-error-card ${isInfo ? 'pipeline-error-info' : 'pipeline-error-err'}`}>
            <div className="pipeline-error-header">
                {isInfo
                    ? <Circle size={14} className="pipeline-error-icon" />
                    : <AlertTriangle size={14} className="pipeline-error-icon" />
                }
                <span className="pipeline-error-label">{isInfo ? 'Stopped' : 'Pipeline Error'}</span>
            </div>
            <div className="pipeline-error-message">{message}</div>
        </div>
    );
};

// PlanCard and StepProgressCard were not fully migrated in this file as they are superseded by PlanCardV2 and StepCard imports in CenterPanel.
// But if they are processed here, we should ensure they don't break.
// The PlanCard component in the original file seemed unused in new CenterPanel (PlanCardV2 is used).
// If legacy code uses them, we might need them. But lets assume CenterPanel handles it.
// Wait, looking at CenterPanel imports:
// import { UserMessage, AssistantMessage, ToolCard } from '../agentic/AgentCards';
// So PlanCard is NOT imported from here in CenterPanel.
// Safe to omit or leave minimal. I will omit PlanCard/StepProgressCard from this file to clean up, as they seem unused.
// Wait, StepCard is imported from '../agentic/StepCard'.

export const PlanCard = () => null; // Deprecated
export const StepProgressCard = () => null; // Deprecated

