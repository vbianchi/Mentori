import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import AppShell from './layout/AppShell';
import Sidebar from './panels/Sidebar';
import CenterPanel from './panels/CenterPanel';
import ArtifactPanel from './panels/ArtifactPanel';
import OrchestratorDebugPanel from './agentic/OrchestratorDebugPanel';
import { ErrorBoundary } from './ui/ErrorBoundary';
import { copyToClipboard } from '../utils/clipboard';
import { feedToMarkdown, downloadMarkdown, extractFollowUpSuggestions } from '../utils/exportChat';
import config from '../config';
import './ui/ErrorBoundary.css';
import '../index.css';

/* --- Sizing Constants --- */
const NORMAL_PX = 512;
const SMALL_PX = 256;
const LARGE_PX = 768;
const widthFor = (size) => (size === 'small' ? SMALL_PX : size === 'large' ? LARGE_PX : NORMAL_PX);

export default function Dashboard() {
    const navigate = useNavigate();

    // --- State: Auth ---
    const [user, setUser] = useState(null);
    const [loadingAuth, setLoadingAuth] = useState(true);

    // --- State: Tasks ---
    const [tasks, setTasks] = useState([]);
    const [activeTaskId, setActiveTaskId] = useState(null);

    // --- State: Feed ---
    const [feed, setFeed] = useState([]);

    // --- State: Connection ---
    const [connectionStatus, setConnectionStatus] = useState({ backend: 'connected', tools: 'error' });

    // --- State: Activity ---
    const [isProcessing, setIsProcessing] = useState(false);
    const [activityStatus, setActivityStatus] = useState("Ready");
    const [backendLogs, setBackendLogs] = useState([]);

    // --- State: Orchestrator ---
    const [orchestratorPhase, setOrchestratorPhase] = useState(null);
    const [isOrchestrated, setIsOrchestrated] = useState(false);
    const [stepStatuses, setStepStatuses] = useState({});

    // --- State: Global Thinking Toggle ---
    const [globalThinkingOpen, setGlobalThinkingOpen] = useState(true);

    // --- State: Debug Panel ---
    const [showDebugPanel, setShowDebugPanel] = useState(false);
    const [eventLog, setEventLog] = useState([]);

    // --- State: Sidebar Sizing ---
    const [leftSidebarSize, setLeftSidebarSize] = useState('normal');
    const [rightSidebarSize, setRightSidebarSize] = useState('normal');

    // --- State: File System Refresh Trigger ---
    const [fileSystemRefresh, setFileSystemRefresh] = useState(0);

    // --- State: SSE Reconnect Trigger ---
    // Increment this to force SSE reconnection (e.g., after Stop then send new message)
    const [sseReconnectKey, setSseReconnectKey] = useState(0);

    // --- Refs ---
    const chatAbortControllerRef = useRef(null);
    const feedCacheRef = useRef(new Map());
    const prevTaskIdRef = useRef(null);

    // --- State: Editor ---
    const [activeFile, setActiveFile] = useState({
        name: 'untitled.txt',
        content: '',
        language: 'text',
        path: ''
    });

    // --- State: Coder Mode / Notebook Viewer ---
    const [isCoderMode, setIsCoderMode] = useState(false);
    const [notebookData, setNotebookData] = useState(null); // { name, cells, activeCellId }
    const [availableNotebooks, setAvailableNotebooks] = useState([]); // List of notebook names for current task
    const [isRunningAllCells, setIsRunningAllCells] = useState(false);

    // Initial load & Auth
    useEffect(() => {
        const loadUserAndTasks = async () => {
            const token = localStorage.getItem("mentori_token");
            if (!token) {
                navigate('/login');
                return;
            }

            try {
                const meRes = await fetch(`${config.API_BASE_URL}/auth/me`, {
                    headers: { "Authorization": `Bearer ${token}` }
                });

                if (meRes.status === 401) {
                    localStorage.removeItem("mentori_token");
                    navigate('/login');
                    return;
                }

                if (!meRes.ok) throw new Error("Failed to fetch profile");

                const userData = await meRes.json();
                setUser(userData);

                const tRes = await fetch(`${config.API_BASE_URL}/tasks/`, {
                    headers: { "Authorization": `Bearer ${token}` }
                });

                if (tRes.ok) {
                    const taskList = await tRes.json();
                    const mapped = taskList.map(t => ({
                        id: t.id,
                        name: t.title || "Untitled Task",
                        model: t.model_identifier,
                        displayId: t.display_id,
                        tokens: {
                            total: t.total_tokens || 0,
                            input: t.input_tokens || 0,
                            output: t.output_tokens || 0
                        }
                    }));
                    setTasks(mapped);
                    if (mapped.length > 0 && !activeTaskId) setActiveTaskId(mapped[0].id);
                }

                // Tools check is fire-and-forget with a 4s timeout — don't block the UI for it
                const toolsController = new AbortController();
                const toolsTimeout = setTimeout(() => toolsController.abort(), 4000);
                fetch(`${config.API_BASE_URL}/tools/`, {
                    headers: { "Authorization": `Bearer ${token}` },
                    signal: toolsController.signal
                }).then(r => {
                    clearTimeout(toolsTimeout);
                    setConnectionStatus(prev => ({ ...prev, tools: r.ok ? 'connected' : 'error' }));
                }).catch(() => {
                    setConnectionStatus(prev => ({ ...prev, tools: 'error' }));
                });
            } catch (e) {
                console.error("Auth/Init Failed", e);
                setConnectionStatus(prev => ({ ...prev, backend: 'error' }));
            } finally {
                setLoadingAuth(false);
            }
        };
        loadUserAndTasks();
    }, [navigate]);

    // Load History and Subscribe to Events
    useEffect(() => {
        if (chatAbortControllerRef.current) {
            chatAbortControllerRef.current.abort();
        }

        // Save current feed to cache before switching away
        const prevTaskId = prevTaskIdRef.current;
        if (prevTaskId && feed.length > 0) {
            feedCacheRef.current.set(prevTaskId, feed);
        }
        prevTaskIdRef.current = activeTaskId;

        const controller = new AbortController();
        chatAbortControllerRef.current = controller;
        const signal = controller.signal;

        if (!activeTaskId) {
            setFeed([]);
            setBackendLogs([]);
            setIsProcessing(false);
            setActivityStatus("Ready");
            setOrchestratorPhase(null);
            setIsOrchestrated(false);
            setStepStatuses({});
            return;
        }

        // Check cache for the new task
        const cachedFeed = feedCacheRef.current.get(activeTaskId);
        const hasCachedFeed = cachedFeed && cachedFeed.length > 0;

        if (hasCachedFeed) {
            setFeed(cachedFeed);
            // Restore orchestrated state from cached feed
            const hasOrchestratorCards = cachedFeed.some(item =>
                ['analysis', 'plan', 'step', 'synthesis'].includes(item.type)
            );
            if (hasOrchestratorCards) {
                setIsOrchestrated(true);
            }
            // Restore step statuses from cached feed
            const cachedStepStatuses = {};
            for (const item of cachedFeed) {
                if (item.type === 'step' && item.stepId && item.status) {
                    cachedStepStatuses[item.stepId] = item.status;
                }
            }
            if (Object.keys(cachedStepStatuses).length > 0) {
                setStepStatuses(cachedStepStatuses);
            }
        } else {
            setFeed([]);
            setStepStatuses({});
        }

        setBackendLogs([]);
        setIsProcessing(false);
        setActivityStatus("Ready");
        setOrchestratorPhase(null);
        if (!hasCachedFeed) {
            setIsOrchestrated(false);
        }
        setIsCoderMode(false);
        setNotebookData(null);
        setAvailableNotebooks([]);

        const loadAndSubscribe = async () => {
            const token = localStorage.getItem("mentori_token");
            if (!token) return;

            try {
                const [messagesRes, logsRes, notebooksRes] = await Promise.all([
                    fetch(`${config.API_BASE_URL}/tasks/${activeTaskId}/messages`, {
                        headers: { "Authorization": `Bearer ${token}` },
                        signal
                    }),
                    fetch(`${config.API_BASE_URL}/tasks/${activeTaskId}/logs`, {
                        headers: { "Authorization": `Bearer ${token}` },
                        signal
                    }).catch(() => null),
                    fetch(`${config.API_BASE_URL}/tasks/${activeTaskId}/notebooks`, {
                        headers: { "Authorization": `Bearer ${token}` },
                        signal
                    }).catch(() => null)
                ]);

                // Load available notebooks for this task
                if (notebooksRes?.ok) {
                    try {
                        const nbData = await notebooksRes.json();
                        if (!signal.aborted) {
                            setAvailableNotebooks(nbData.notebooks || []);
                        }
                    } catch (e) {
                        console.warn("Failed to parse notebooks response:", e);
                    }
                }

                if (signal.aborted) return;

                if (logsRes?.ok) {
                    const logs = await logsRes.json();
                    if (!signal.aborted) {
                        const formattedLogs = logs.map(l => {
                            const time = new Date(l.timestamp).toLocaleTimeString();
                            return `${time} - [${l.level}] - ${l.message}`;
                        });
                        setBackendLogs(formattedLogs);
                    }
                }

                if (messagesRes.ok && !hasCachedFeed) {
                    const msgs = await messagesRes.json();
                    if (signal.aborted) return;

                    // === RECONSTRUCTION LOGIC With Metadata ===
                    const reconstructedFeed = [];
                    let planCardIndex = -1; // To track last plan for superseding

                    let i = 0;
                    while (i < msgs.length) {
                        const m = msgs[i];
                        const meta = m.metadata_blob || m.metadata || {}; // Handle potential API variations

                        // Check if session was orchestrated based on metadata presence
                        if (meta.phase) {
                            setIsOrchestrated(true);
                        }

                        // 1. User Message
                        if (m.role === 'user') {
                            reconstructedFeed.push({
                                type: 'user',
                                content: m.content,
                                showMarkdown: true
                            });
                            i++;
                            continue;
                        }

                        // 2. Orchestrator Messages (based on metadata)
                        if (meta.phase) {

                            // ANALYSIS
                            if (meta.phase === 'analyzing') {
                                // Parse model name and thinking level
                                let analysisModelName = meta.model_name || "System";
                                let analysisThinkingLevel = null;
                                const thinkMatch = analysisModelName.match(/\[think(?::(\w+))?\]/);
                                if (thinkMatch) {
                                    analysisThinkingLevel = thinkMatch[1] || 'enabled';
                                    analysisModelName = analysisModelName.replace(/\[think(?::\w+)?\]$/, '').trim();
                                }
                                reconstructedFeed.push({
                                    type: 'analysis',
                                    thinking: m.thinking,
                                    decision: meta.decision,
                                    decisionReason: meta.reasoning,
                                    agentName: meta.agent_name || "Lead Researcher",
                                    agentModel: analysisModelName,
                                    thinkingLevel: analysisThinkingLevel,
                                    isStreaming: false
                                });
                                i++;
                                continue;
                            }

                            // PLANNING - Handle both orchestrator plans and coder_v2 algorithms
                            if (meta.phase === 'planning') {
                                // Check if this is coder_v2 mode - create coder_v2 card instead of plan card
                                if (meta.mode === 'coder_v2' && meta.algorithm) {
                                    const algorithm = meta.algorithm;
                                    const steps = algorithm.steps || [];

                                    // Look ahead to collect step progress from subsequent messages
                                    const stepProgress = {};
                                    let scanIdx = i + 1;
                                    while (scanIdx < msgs.length) {
                                        const scanMeta = msgs[scanIdx].metadata_blob || {};
                                        if (scanMeta.mode === 'coder_v2' && scanMeta.phase === 'executing') {
                                            const stepNum = scanMeta.step_number;
                                            if (stepNum) {
                                                stepProgress[stepNum] = {
                                                    status: 'completed',
                                                    score: scanMeta.score || 0,
                                                    cellId: scanMeta.cell_id,
                                                    description: steps[stepNum - 1]?.description || `Step ${stepNum}`,
                                                    expectedOutput: steps[stepNum - 1]?.expected_output || '',
                                                };
                                            }
                                        }
                                        // Stop if we hit a new user message or different mode
                                        if (msgs[scanIdx].role === 'user') break;
                                        scanIdx++;
                                    }

                                    // Determine phase based on progress
                                    const completedCount = Object.keys(stepProgress).length;
                                    const phase = completedCount >= steps.length ? 'complete' : (completedCount > 0 ? 'executing' : 'algorithm');

                                    reconstructedFeed.push({
                                        type: 'coder_v2',
                                        phase: phase,
                                        algorithm: algorithm,
                                        algorithmCellId: meta.cell_id,
                                        steps: steps,
                                        stepProgress: stepProgress,
                                        currentStep: completedCount > 0 ? Math.max(...Object.keys(stepProgress).map(Number)) : null,
                                        exports: {},
                                    });
                                    i++;
                                    continue;
                                }

                                // Standard orchestrator plan (non-coder mode)
                                // Mark previous plan as superseded
                                if (planCardIndex >= 0 && planCardIndex < reconstructedFeed.length) {
                                    reconstructedFeed[planCardIndex] = { ...reconstructedFeed[planCardIndex], isSuperseded: true };
                                }

                                reconstructedFeed.push({
                                    type: 'plan',
                                    plan: meta.plan, // Requires backend to send 'plan' in metadata
                                    thinking: m.thinking, // Extract thinking from message
                                    version: planCardIndex + 2, // 1-based, increment for each plan found
                                    isSuperseded: false,
                                    isUpdated: planCardIndex >= 0,
                                    agentName: meta.agent_name || "Lead Researcher",
                                    agentModel: meta.model_name || "System",
                                });
                                planCardIndex = reconstructedFeed.length - 1;
                                i++;
                                continue;
                            }

                            // EXECUTING (Step Start)
                            if (meta.phase === 'executing') {
                                // Skip coder_v2 executing messages - they're handled by the coder_v2 card
                                if (meta.mode === 'coder_v2') {
                                    i++;
                                    continue;
                                }
                                // This message describes the step and initiates tool call
                                const stepId = meta.step_id || `step_${i}`;
                                let toolOutput = null;
                                let toolStatus = 'running';
                                let error = null;
                                let nextIdx = i + 1;

                                // Look ahead for tool output (Scanning for 'tool' message)
                                // We scan until we hit another assistant message or end
                                while (nextIdx < msgs.length) {
                                    const nextM = msgs[nextIdx];
                                    if (nextM.role === 'tool') {
                                        // Found a tool output. Assume it's for this step (sequential assumption)
                                        toolOutput = nextM.content;
                                        toolStatus = 'completed';
                                        if (toolOutput && toolOutput.startsWith && toolOutput.startsWith("Error")) {
                                            toolStatus = 'failed';
                                            error = toolOutput;
                                        }
                                        break;
                                    }
                                    if (nextM.role === 'assistant' || nextM.role === 'user') {
                                        // Structure changed, stop scanning
                                        break;
                                    }
                                    nextIdx++;
                                }

                                // === COLLABORATION TOOLS - Render as CollaborationCard ===
                                const COLLABORATION_TOOLS = ['ask_user', 'present_plan', 'share_progress', 'report_failure'];
                                if (COLLABORATION_TOOLS.includes(meta.tool_name)) {
                                    // Extract question from tool call arguments
                                    let toolArgs = {};
                                    if (m.tool_calls && m.tool_calls[0]) {
                                        toolArgs = m.tool_calls[0].function?.arguments || {};
                                        // Parse if string
                                        if (typeof toolArgs === 'string') {
                                            try { toolArgs = JSON.parse(toolArgs); } catch (e) { toolArgs = {}; }
                                        }
                                    }

                                    reconstructedFeed.push({
                                        type: 'collaboration',
                                        collaborationType: meta.tool_name === 'present_plan' ? 'approval' : 'question',
                                        data: {
                                            tool: meta.tool_name,
                                            payload: toolArgs,
                                            step_id: stepId
                                        },
                                        taskId: activeTaskId,
                                        // Mark as completed if we have a tool output (user responded)
                                        submitted: toolOutput ? true : false,
                                        userResponse: toolOutput || null
                                    });

                                    // Advance index
                                    if (toolStatus !== 'running' && nextIdx < msgs.length && msgs[nextIdx].role === 'tool') {
                                        i = nextIdx + 1;
                                    } else {
                                        i++;
                                    }
                                    continue;
                                }

                                // Parse model name and thinking level
                                let stepModelName = meta.model_name || "Model";
                                let stepThinkingLevel = null;
                                const thinkMatch = stepModelName.match(/\[think(?::(\w+))?\]/);
                                if (thinkMatch) {
                                    stepThinkingLevel = thinkMatch[1] || 'enabled';
                                    stepModelName = stepModelName.replace(/\[think(?::\w+)?\]$/, '').trim();
                                }

                                // For coder mode: if message has content or thinking, show it as synthesis before the step
                                // This matches live streaming where reasoning is flushed before tool_call
                                const isCoderMessage = meta.mode === 'coder' || meta.agent_role === 'coder';
                                if (isCoderMessage && (m.content?.trim() || m.thinking?.trim())) {
                                    reconstructedFeed.push({
                                        type: 'synthesis',
                                        content: m.content || '',
                                        thinking: m.thinking || '',
                                        model: stepModelName,
                                        agentName: meta.agent_name || "Coder Agent",
                                        isStreaming: false
                                    });
                                }

                                reconstructedFeed.push({
                                    type: 'step',
                                    stepId: stepId,
                                    description: isCoderMessage ? meta.tool_name || 'Executing tool' : (m.content ? m.content.split('\n')[0].replace('**Step', '').split(':').pop().trim() : 'Executing Step'),
                                    agentRole: meta.agent_role || 'default',
                                    agentName: meta.agent_name || "Agent",
                                    agentModel: stepModelName,
                                    thinkingLevel: stepThinkingLevel,
                                    status: meta.success === false ? 'failed' : toolStatus, // Prefer metadata status
                                    toolName: meta.tool_name,
                                    toolInput: m.tool_calls && m.tool_calls[0] ? JSON.stringify(m.tool_calls[0].function.arguments) : null,
                                    toolOutput: toolOutput,
                                    error: error,
                                    evaluation: "", // Will be filled by 'evaluating' phase message if present
                                    evaluationSummary: "",
                                    isStreaming: false
                                });

                                // Advance index. If we found a tool message at nextIdx, we skip it too.
                                if (toolStatus !== 'running' && nextIdx < msgs.length && msgs[nextIdx].role === 'tool') {
                                    i = nextIdx + 1;
                                } else {
                                    i++;
                                }
                                continue;
                            }

                            // EVALUATING / SUPERVISING (Merge into last step)
                            if (meta.phase === 'evaluating' || meta.phase === 'supervising') {
                                // Find the last step card
                                for (let j = reconstructedFeed.length - 1; j >= 0; j--) {
                                    if (reconstructedFeed[j].type === 'step') {
                                        const qualityScore = meta.quality_score;
                                        const evaluationSummary = qualityScore !== undefined
                                            ? `Quality: ${qualityScore}%`
                                            : (meta.success ? "Verification Passed" : "Verification Failed");

                                        reconstructedFeed[j] = {
                                            ...reconstructedFeed[j],
                                            evaluation: m.thinking,
                                            evaluationSummary: evaluationSummary,
                                            supervisorEvaluation: meta.quality_score !== undefined ? {
                                                qualityScore: meta.quality_score,
                                                issues: meta.issues || [],
                                                shouldRetry: meta.should_retry,
                                                shouldEscalate: meta.should_escalate
                                            } : undefined
                                        };
                                        break;
                                    }
                                }
                                i++;
                                continue;
                            }

                            // DOCUMENTATION (coder_v2 mode) - Update exports on coder_v2 card
                            if (meta.phase === 'documentation' && meta.mode === 'coder_v2') {
                                // Find the coder_v2 card and update its exports
                                for (let j = reconstructedFeed.length - 1; j >= 0; j--) {
                                    if (reconstructedFeed[j].type === 'coder_v2') {
                                        const currentExports = reconstructedFeed[j].exports || {};
                                        if (meta.export_format && meta.export_path) {
                                            currentExports[meta.export_format] = meta.export_path;
                                        }
                                        reconstructedFeed[j] = {
                                            ...reconstructedFeed[j],
                                            exports: currentExports,
                                        };
                                        break;
                                    }
                                }
                                i++;
                                continue;
                            }

                            // SUMMARY (coder_v2 mode) - Update coder_v2 card with summary
                            if (meta.phase === 'summary' && meta.mode === 'coder_v2') {
                                for (let j = reconstructedFeed.length - 1; j >= 0; j--) {
                                    if (reconstructedFeed[j].type === 'coder_v2') {
                                        reconstructedFeed[j] = {
                                            ...reconstructedFeed[j],
                                            phase: 'complete',
                                            summary: meta.summary || {},
                                        };
                                        break;
                                    }
                                }
                                i++;
                                continue;
                            }

                            // SYNTHESIZING / DIRECT ANSWER
                            if (meta.phase === 'synthesizing' || meta.phase === 'direct_answer') {
                                // Parse model name and thinking level
                                let synthesisModelName = meta.model_name || "Ollama";
                                let synthesisThinkingLevel = null;
                                const thinkMatch = synthesisModelName.match(/\[think(?::(\w+))?\]/);
                                if (thinkMatch) {
                                    synthesisThinkingLevel = thinkMatch[1] || 'enabled';
                                    synthesisModelName = synthesisModelName.replace(/\[think(?::\w+)?\]$/, '').trim();
                                }
                                reconstructedFeed.push({
                                    type: 'synthesis',
                                    content: m.content,
                                    thinking: m.thinking,
                                    model: synthesisModelName,
                                    agentName: meta.agent_name || "Lead Researcher",
                                    thinkingLevel: synthesisThinkingLevel,
                                    isStreaming: false
                                });
                                i++;
                                continue;
                            }
                        }

                        // 3. Fallback / Legacy Logic (No metadata or failed match)
                        // This handles coder mode and other non-orchestrated sessions
                        if (m.role === 'assistant') {
                            if (m.tool_calls && m.tool_calls.length > 0) {
                                // If assistant message has BOTH content AND tool_calls,
                                // first create a synthesis card for the content (reasoning)
                                // This matches live streaming behavior where content is flushed before tool_call
                                if (m.content && m.content.trim()) {
                                    reconstructedFeed.push({
                                        type: 'synthesis',
                                        content: m.content,
                                        thinking: m.thinking,
                                        agentName: m.agent_role ? (m.agent_role.charAt(0).toUpperCase() + m.agent_role.slice(1) + " Agent") : "Coder Agent",
                                        model: m.model || "Model",
                                        isStreaming: false
                                    });
                                }

                                // Now create Step card for the tool call
                                const toolCall = m.tool_calls[0];
                                const toolName = toolCall.function.name;
                                let toolOutput = null;
                                let nextIdx = i + 1;
                                while (nextIdx < msgs.length) {
                                    if (msgs[nextIdx].role === 'tool') {
                                        toolOutput = msgs[nextIdx].content;
                                        break;
                                    }
                                    if (msgs[nextIdx].role === 'assistant' || msgs[nextIdx].role === 'user') break;
                                    nextIdx++;
                                }
                                reconstructedFeed.push({
                                    type: 'step',
                                    stepId: `legacy_${i}`,
                                    description: `Executing ${toolName}...`,
                                    agentRole: m.agent_role || 'coder',
                                    agentName: m.agent_role ? (m.agent_role.charAt(0).toUpperCase() + m.agent_role.slice(1) + " Agent") : "Coder Agent",
                                    agentModel: m.model || "Model",
                                    status: toolOutput ? 'completed' : 'running',
                                    toolName: toolName,
                                    toolInput: JSON.stringify(toolCall.function.arguments),
                                    toolOutput: toolOutput,
                                    evaluation: "",  // Thinking is now in the synthesis card above
                                    isStreaming: false
                                });
                                if (toolOutput) i = nextIdx + 1;
                                else i++;
                            } else {
                                // Treat as Synthesis/Simple (no tool calls)
                                reconstructedFeed.push({
                                    type: 'synthesis',
                                    content: m.content,
                                    thinking: m.thinking,
                                    agentName: m.agent_role ? (m.agent_role.charAt(0).toUpperCase() + m.agent_role.slice(1) + " Agent") : "Coder Agent",
                                    model: m.model || "Model",
                                    isStreaming: false
                                });
                                i++;
                            }
                        } else if (m.role === 'tool') {
                            // Orphaned tool message
                            i++;
                        } else {
                            i++;
                        }
                    }
                    setFeed(reconstructedFeed);

                    // Extract step statuses from reconstructed feed for PlanCardV2
                    const reconstructedStepStatuses = {};
                    for (const item of reconstructedFeed) {
                        if (item.type === 'step' && item.stepId && item.status) {
                            reconstructedStepStatuses[item.stepId] = item.status;
                        }
                    }
                    if (Object.keys(reconstructedStepStatuses).length > 0) {
                        setStepStatuses(reconstructedStepStatuses);
                    }
                }

                // Subscribe to Event Stream
                while (!signal.aborted) {
                    try {
                        const eventRes = await fetch(`${config.API_BASE_URL}/tasks/${activeTaskId}/events`, {
                            headers: { "Authorization": `Bearer ${token}` },
                            signal
                        });

                        if (!eventRes.ok) {
                            await new Promise(r => setTimeout(r, 2000));
                            continue;
                        }

                        const reader = eventRes.body.getReader();
                        const decoder = new TextDecoder("utf-8");
                        let buffer = "";

                        // === STATE TRACKING ===
                        let currentPhase = null;          // 'analyzing' | 'planning' | 'executing' | 'evaluating' | 'synthesizing' | 'direct_answer'
                        let currentStepId = null;         // Current step being executed
                        let currentAgentRole = "default";
                        let currentAgentModel = "Ollama";
                        let currentAgentName = "System"; // For display
                        let currentThinkingLevel = null;  // Track thinking level for display
                        let isOrchestratedMode = false;
                        let isCoderModeLocal = false;     // Track coder mode locally in event loop
                        let isCoderV2 = false;           // Track V2 mode to skip V1-style step cards
                        let planVersion = 0;

                        // Accumulators (Source of Truth for Streaming Text)
                        let analysisThinking = "";
                        let planningThinking = ""; // New accumulator for Plan Card persistence
                        let synthesisThinking = "";
                        let synthesisContent = "";
                        let stepEvaluation = "";

                        // Coder Mode Accumulators (kept separate, only flushed on complete)
                        let coderContent = "";
                        let coderThinking = "";
                        let coderStepCounter = 0;  // Track step IDs for coder tool calls

                        // Legacy Accumulators
                        let accumulatedContent = "";
                        let accumulatedThinking = "";

                        // Batching State
                        let lastFlushTime = Date.now();
                        const FLUSH_INTERVAL = 50; // ms

                        // Flush helper: updates the React state with current text accumulators
                        const flushUpdates = () => {
                            setFeed(prev => {
                                const newFeed = [...prev];

                                if (isOrchestratedMode) {
                                    // Update Analysis Card
                                    if (currentPhase === 'analyzing' && analysisThinking) {
                                        for (let i = newFeed.length - 1; i >= 0; i--) {
                                            if (newFeed[i].type === 'analysis') {
                                                newFeed[i] = { ...newFeed[i], thinking: analysisThinking };
                                                break;
                                            }
                                        }
                                    }
                                    // Update Plan Card
                                    if (currentPhase === 'planning' && planningThinking) {
                                        for (let i = newFeed.length - 1; i >= 0; i--) {
                                            if (newFeed[i].type === 'plan') {
                                                newFeed[i] = { ...newFeed[i], thinking: planningThinking };
                                                break;
                                            }
                                        }
                                    }
                                    // Update Synthesis Card (Thinking + Content)
                                    if ((currentPhase === 'synthesizing' || currentPhase === 'direct_answer') && (synthesisThinking || synthesisContent)) {
                                        for (let i = newFeed.length - 1; i >= 0; i--) {
                                            if (newFeed[i].type === 'synthesis') {
                                                newFeed[i] = {
                                                    ...newFeed[i],
                                                    thinking: synthesisThinking,
                                                    content: synthesisContent
                                                };
                                                break;
                                            }
                                        }
                                    }
                                    // Update Step Evaluation (handles both 'evaluating' and 'supervising' phases)
                                    if ((currentPhase === 'evaluating' || currentPhase === 'supervising') && currentStepId && stepEvaluation) {
                                        for (let i = newFeed.length - 1; i >= 0; i--) {
                                            if (newFeed[i].type === 'step' && newFeed[i].stepId === currentStepId) {
                                                newFeed[i] = { ...newFeed[i], evaluation: stepEvaluation, isStreaming: true };
                                                break;
                                            }
                                        }
                                    }
                                } else {
                                    // Legacy Update - find last assistant card (may have tool cards after it)
                                    for (let i = newFeed.length - 1; i >= 0; i--) {
                                        if (newFeed[i].type === 'assistant') {
                                            newFeed[i] = {
                                                ...newFeed[i],
                                                content: accumulatedContent,
                                                thinking: accumulatedThinking
                                            };
                                            break;
                                        }
                                    }
                                }
                                return newFeed;
                            });
                            lastFlushTime = Date.now();
                        };

                        while (true) {
                            const { done, value } = await reader.read();
                            if (done) break;

                            buffer += decoder.decode(value, { stream: true });
                            const lines = buffer.split("\n");
                            buffer = lines.pop() || "";

                            let needsFlush = false;

                            for (const line of lines) {
                                if (!line.trim()) continue;
                                try {
                                    const data = JSON.parse(line);

                                    // === UNIVERSAL TOKEN COUNTING ===
                                    if (data.type === 'token_usage' && data.token_usage) {
                                        const usage = data.token_usage;
                                        setTasks(prev => prev.map(t => {
                                            if (t.id === activeTaskId) {
                                                return {
                                                    ...t,
                                                    tokens: {
                                                        total: (t.tokens?.total || 0) + (usage.total || 0),
                                                        input: (t.tokens?.input || 0) + (usage.input || 0),
                                                        output: (t.tokens?.output || 0) + (usage.output || 0)
                                                    }
                                                };
                                            }
                                            return t;
                                        }));
                                    }

                                    // === COLLABORATION HANDLERS ===
                                    if (data.type === 'collaboration_required') {
                                        flushUpdates();
                                        setFeed(prev => [...prev, {
                                            type: 'collaboration',
                                            collaborationType: 'question', // Default to question/tool interaction
                                            data: data, // Contains tool, payload, step_id
                                            taskId: activeTaskId
                                        }]);
                                        // Pause processing indicators as we are waiting
                                        setIsProcessing(false);
                                        setActivityStatus("Waiting for User Input");
                                        continue;
                                    }

                                    if (data.type === 'plan_approval_required') {
                                        flushUpdates();
                                        setFeed(prev => [...prev, {
                                            type: 'collaboration',
                                            collaborationType: 'approval',
                                            data: data, // Contains plan, reasoning
                                            taskId: activeTaskId
                                        }]);
                                        setIsProcessing(false);
                                        setActivityStatus("Waiting for Plan Approval");
                                        continue;
                                    }

                                    if (data.type === 'human_intervention_required') {
                                        flushUpdates();
                                        setFeed(prev => [...prev, {
                                            type: 'collaboration',
                                            collaborationType: 'intervention',
                                            data: data, // Contains step_id, reason, issues, attempts
                                            taskId: activeTaskId
                                        }]);
                                        setIsProcessing(false);
                                        setActivityStatus("Waiting for User Decision");
                                        continue;
                                    }

                                    // === PLAN REJECTED (no extra card — CollaborationCard already shows badge) ===
                                    if (data.type === 'plan_rejected') {
                                        flushUpdates();
                                        setIsProcessing(false);
                                        setActivityStatus("Plan Rejected");
                                        continue;
                                    }

                                    // === RESUMED EVENT (after collaboration response) ===
                                    if (data.type === 'resumed') {
                                        setIsProcessing(true);
                                        setActivityStatus(data.detail || "Resuming execution...");
                                        continue;
                                    }

                                    // === CANCELLED EVENT (task stopped) ===
                                    if (data.type === 'cancelled') {
                                        flushUpdates();
                                        setIsProcessing(false);
                                        setActivityStatus("Stopped");
                                        setFeed(prev => [...prev, {
                                            type: 'pipeline_error',
                                            message: data.reason || 'Cancelled by user',
                                            severity: 'info',
                                        }]);
                                        break; // Exit the event loop
                                    }

                                    logEvent(data.type, data);

                                    // === SESSION INFO ===
                                    if (data.type === 'session_info') {
                                        const info = data.session_info;
                                        currentAgentRole = info.agent_role || 'default';
                                        currentAgentModel = info.model || 'Ollama';
                                        currentAgentName = "Lead Researcher"; // Default for session

                                        // Check for notebook coder mode (from /coder/chat endpoint)
                                        // Supports both V1 (mode: 'coder') and V2 (mode: 'coder_v2')
                                        if (info.mode === 'coder' || info.mode === 'coder_v2') {
                                            isOrchestratedMode = false;
                                            isCoderModeLocal = true;  // Track locally for event handling
                                            setIsOrchestrated(false);
                                            setIsCoderMode(true);
                                            currentAgentName = "Coder Agent";
                                            currentAgentRole = 'coder';
                                            const cellCountLabel = info.cell_count > 0
                                                ? `Notebook: ${info.notebook_name} (${info.cell_count} cells)`
                                                : `Notebook: ${info.notebook_name || 'Loading...'}`;
                                            setActivityStatus(cellCountLabel);
                                            // Only initialize notebookData if not already set
                                            // (follow-up messages will populate via notebook_loaded event)
                                            setNotebookData(prev => {
                                                if (prev && prev.cells && prev.cells.length > 0) {
                                                    // Keep existing cells - notebook_loaded will update if needed
                                                    return { ...prev, name: info.notebook_name || prev.name, path: info.notebook_path || prev.path };
                                                }
                                                return {
                                                    name: info.notebook_name || 'Untitled',
                                                    path: info.notebook_path,
                                                    cells: [],
                                                    activeCellId: null
                                                };
                                            });
                                            // Reset coder accumulators
                                            coderContent = "";
                                            coderThinking = "";
                                            coderStepCounter = 0;
                                            // DON'T create assistant card yet - wait until complete
                                            // This ensures tool/step cards appear first, then final response
                                        } else {
                                            setIsCoderMode(false);
                                            // NOTE: do NOT clear notebookData here — the user may have a
                                            // notebook open and we must not close it when a new chat message
                                            // starts. notebookData is only cleared on task switch (line ~214).
                                            isOrchestratedMode = info.orchestrated || false;
                                            setIsOrchestrated(isOrchestratedMode);
                                            if (isOrchestratedMode) {
                                                setOrchestratorPhase('analyzing');
                                                currentPhase = 'analyzing';
                                            }
                                        }
                                        continue;
                                    }

                                    // === STATUS ===
                                    if (data.type === 'status') {
                                        setActivityStatus(data.status + (data.detail ? ` - ${data.detail}` : ''));
                                        setIsProcessing(data.status !== 'Ready');
                                        continue;
                                    }

                                    // === ERROR ===
                                    if (data.type === 'error') {
                                        flushUpdates(); // Flush before error
                                        setFeed(prev => [...prev, {
                                            type: 'pipeline_error',
                                            message: data.message,
                                            severity: 'error',
                                        }]);
                                        setIsProcessing(false);
                                        continue;
                                    }

                                    // === FILE SYSTEM UPDATE ===
                                    if (data.type === 'fs_update') {
                                        setFileSystemRefresh(prev => prev + 1);
                                        continue;
                                    }

                                    // ===================================
                                    // ORCHESTRATOR HANDLERS
                                    // ===================================
                                    if (isOrchestratedMode) {

                                        // THINKING CHUNK (High Freq)
                                        // Use data.phase (from event) as source of truth to prevent leakage between cards
                                        if (data.type === 'orchestrator_thinking' && data.content) {
                                            const eventPhase = data.phase || currentPhase;  // Prefer event phase, fallback to state
                                            if (eventPhase === 'analyzing') {
                                                analysisThinking += data.content;
                                            }
                                            else if (eventPhase === 'planning') {
                                                // Only update planning accumulator
                                                planningThinking += data.content;
                                            }
                                            else if (eventPhase === 'synthesizing' || eventPhase === 'direct_answer') {
                                                synthesisThinking += data.content;
                                            }
                                            else if (eventPhase === 'evaluating' || eventPhase === 'supervising') {
                                                stepEvaluation += data.content;
                                            }
                                            needsFlush = true;
                                            continue;
                                        }

                                        // CONTENT CHUNK (High Freq)
                                        // Content chunks go to synthesis (chunk events don't have phase, use currentPhase)
                                        if ((data.type === 'chunk' || data.type === 'content') && data.content) {
                                            if (currentPhase === 'synthesizing' || currentPhase === 'direct_answer') {
                                                synthesisContent += data.content;
                                                needsFlush = true;
                                            }
                                            continue;
                                        }

                                        // STRUCTURAL EVENTS (Flush before processing)

                                        if (data.type === 'orchestrator_thinking_start') {
                                            flushUpdates();
                                            currentPhase = data.phase;
                                            setOrchestratorPhase(data.phase);
                                            setIsProcessing(true);

                                            if (data.phase === 'analyzing') {
                                                analysisThinking = "";
                                                // Parse thinking level from model string if present
                                                let analysisModel = currentAgentModel;
                                                let analysisThinkLevel = data.thinking_level || null;
                                                const thinkMatch = analysisModel.match(/\[think(?::(\w+))?\]/);
                                                if (thinkMatch && !analysisThinkLevel) {
                                                    analysisThinkLevel = thinkMatch[1] || 'enabled';
                                                    analysisModel = analysisModel.replace(/\[think(?::\w+)?\]$/, '').trim();
                                                }
                                                currentThinkingLevel = analysisThinkLevel;
                                                setFeed(prev => [...prev, {
                                                    type: 'analysis',
                                                    thinking: "",
                                                    decision: null,
                                                    decisionReason: "",
                                                    agentName: "Lead Researcher",
                                                    agentModel: analysisModel,
                                                    thinkingLevel: analysisThinkLevel,
                                                    isStreaming: true
                                                }]);
                                            } else if (data.phase === 'planning') {
                                                planningThinking = ""; // Initialize isolated planning thinking
                                                // 1. Update Analysis Card to show decision
                                                setFeed(prev => {
                                                    const newFeed = [...prev];
                                                    for (let i = newFeed.length - 1; i >= 0; i--) {
                                                        if (newFeed[i].type === 'analysis') {
                                                            newFeed[i] = {
                                                                ...newFeed[i],
                                                                decision: 'plan',
                                                                decisionReason: 'generating execution plan...',
                                                                isStreaming: false // Stop streaming on analysis card
                                                            };
                                                            break;
                                                        }
                                                    }
                                                    // 2. Create Placeholder Plan Card immediately
                                                    newFeed.push({
                                                        type: 'plan',
                                                        plan: { goal: 'Generating execution plan...', steps: [] },
                                                        thinking: "",
                                                        version: planVersion + 1,
                                                        isSuperseded: false,
                                                        isUpdated: false,
                                                        agentName: "Lead Researcher",
                                                        agentModel: currentAgentModel
                                                    });
                                                    return newFeed;
                                                });
                                            } else if (data.phase === 'synthesizing') {
                                                synthesisThinking = "";
                                                synthesisContent = "";
                                                currentThinkingLevel = data.thinking_level || currentThinkingLevel;
                                                setFeed(prev => [...prev, {
                                                    type: 'synthesis',
                                                    thinking: "",
                                                    content: "",
                                                    model: currentAgentModel,
                                                    agentName: "Lead Researcher",
                                                    thinkingLevel: currentThinkingLevel,
                                                    isStreaming: true
                                                }]);
                                            } else if (data.phase === 'evaluating' || data.phase === 'supervising') {
                                                stepEvaluation = "";
                                            }
                                            continue;
                                        }

                                        if (data.type === 'plan_generated') {
                                            flushUpdates();
                                            planVersion++;
                                            setOrchestratorPhase('planning');

                                            setFeed(prev => {
                                                const newFeed = [...prev];

                                                // Find the placeholder plan we created earlier
                                                let placeholderFound = false;
                                                for (let i = newFeed.length - 1; i >= 0; i--) {
                                                    if (newFeed[i].type === 'plan' && !newFeed[i].isSuperseded) {
                                                        // Update existing placeholder
                                                        newFeed[i] = {
                                                            ...newFeed[i],
                                                            plan: data.plan, // Inject real plan
                                                            thinking: planningThinking, // Confirm final thinking
                                                            version: planVersion,
                                                            isUpdated: planVersion > 1
                                                        };
                                                        placeholderFound = true;
                                                        break;
                                                    }
                                                }

                                                // Fallback if no placeholder (should not happen in normal flow but good for robustness)
                                                if (!placeholderFound) {
                                                    newFeed.push({
                                                        type: 'plan',
                                                        plan: data.plan,
                                                        thinking: planningThinking,
                                                        version: planVersion,
                                                        isSuperseded: false,
                                                        isUpdated: planVersion > 1,
                                                        agentName: "Lead Researcher",
                                                        agentModel: currentAgentModel
                                                    });
                                                }

                                                // Update analysis decision (redundant check but ensures consistency)
                                                for (let i = newFeed.length - 1; i >= 0; i--) {
                                                    if (newFeed[i].type === 'analysis') {
                                                        newFeed[i] = {
                                                            ...newFeed[i],
                                                            decision: 'plan',
                                                            decisionReason: 'requires tools',
                                                            isStreaming: false
                                                        };
                                                        break;
                                                    }
                                                }
                                                return newFeed;
                                            });
                                            continue;
                                        }

                                        if (data.type === 'direct_answer_mode') {
                                            flushUpdates();
                                            setFeed(prev => {
                                                const newFeed = [...prev];
                                                for (let i = newFeed.length - 1; i >= 0; i--) {
                                                    if (newFeed[i].type === 'analysis') {
                                                        newFeed[i] = {
                                                            ...newFeed[i],
                                                            decision: 'direct',
                                                            decisionReason: data.reason || 'no tools needed',
                                                            isStreaming: false
                                                        };
                                                        break;
                                                    }
                                                }
                                                return newFeed;
                                            });

                                            // Immediately start synthesis card for direct answer
                                            currentPhase = 'direct_answer';
                                            synthesisThinking = "";
                                            synthesisContent = "";
                                            currentThinkingLevel = data.thinking_level || currentThinkingLevel;
                                            setFeed(prev => [...prev, {
                                                type: 'synthesis',
                                                thinking: "",
                                                content: "",
                                                model: currentAgentModel,
                                                agentName: "Lead Researcher",
                                                thinkingLevel: currentThinkingLevel,
                                                isStreaming: true
                                            }]);
                                            continue;
                                        }

                                        if (data.type === 'step_start') {
                                            flushUpdates();
                                            currentStepId = data.step_id;
                                            currentAgentRole = data.agent_role || currentAgentRole;
                                            const stepAgentName = data.agent_name || "Agent";
                                            // Use agent_model from data, fallback to currentAgentModel
                                            let stepAgentModel = data.agent_model || currentAgentModel || "Model";
                                            // Parse thinking level from model string if present (e.g., "model[think:low]")
                                            let stepThinkLevel = data.thinking_level || null;
                                            const thinkMatch = stepAgentModel.match(/\[think(?::(\w+))?\]/);
                                            if (thinkMatch && !stepThinkLevel) {
                                                stepThinkLevel = thinkMatch[1] || 'enabled';
                                                // Clean the model string for display
                                                stepAgentModel = stepAgentModel.replace(/\[think(?::\w+)?\]$/, '').trim();
                                            }
                                            currentThinkingLevel = stepThinkLevel; // Track for synthesis

                                            currentPhase = 'executing';
                                            stepEvaluation = "";
                                            setOrchestratorPhase('executing');
                                            setStepStatuses(prev => ({ ...prev, [data.step_id]: 'running' }));
                                            // Clear stale supervisor status message when a new step begins
                                            setActivityStatus(`Executing: ${data.description || data.step_id}`);

                                            setFeed(prev => [...prev, {
                                                type: 'step',
                                                stepId: data.step_id,
                                                description: data.description,
                                                agentRole: data.agent_role || 'default',
                                                agentName: stepAgentName,
                                                agentModel: stepAgentModel,
                                                thinkingLevel: stepThinkLevel,
                                                status: 'running',
                                                toolName: data.tool_name,
                                                toolInput: null,
                                                toolOutput: null,
                                                error: null,
                                                evaluation: "",
                                                evaluationSummary: "",
                                                isStreaming: false
                                            }]);
                                            continue;
                                        }

                                        if (data.type === 'tool_call') {
                                            flushUpdates();
                                            const tc = data.tool_call;
                                            const stepId = data.step_id || currentStepId;

                                            setFeed(prev => {
                                                const newFeed = [...prev];
                                                for (let i = newFeed.length - 1; i >= 0; i--) {
                                                    if (newFeed[i].type === 'step' && newFeed[i].stepId === stepId) {
                                                        newFeed[i] = {
                                                            ...newFeed[i],
                                                            toolName: tc.name,
                                                            toolInput: JSON.stringify(tc.arguments, null, 2)
                                                        };
                                                        break;
                                                    }
                                                }
                                                return newFeed;
                                            });
                                            continue;
                                        }

                                        if (data.type === 'tool_progress') {
                                            // Live progress from long-running tools (RAG, RLM, etc.)
                                            setFeed(prev => {
                                                const newFeed = [...prev];
                                                // Find the last running step card
                                                for (let i = newFeed.length - 1; i >= 0; i--) {
                                                    if (newFeed[i].type === 'step' && newFeed[i].status === 'running') {
                                                        const existing = newFeed[i].toolProgress || [];
                                                        newFeed[i] = {
                                                            ...newFeed[i],
                                                            toolProgress: [...existing, {
                                                                message: data.message,
                                                                phase: data.phase || '',
                                                                step: data.step || 0,
                                                                totalSteps: data.total_steps || 0,
                                                            }],
                                                        };
                                                        break;
                                                    }
                                                }
                                                return newFeed;
                                            });
                                            continue;
                                        }

                                        if (data.type === 'tool_result') {
                                            flushUpdates();
                                            const tr = data.tool_result;
                                            const stepId = data.step_id || currentStepId;

                                            setFeed(prev => {
                                                const newFeed = [...prev];
                                                for (let i = newFeed.length - 1; i >= 0; i--) {
                                                    // Update step cards
                                                    if (newFeed[i].type === 'step' && newFeed[i].stepId === stepId) {
                                                        newFeed[i] = {
                                                            ...newFeed[i],
                                                            toolOutput: tr.content
                                                        };
                                                        break;
                                                    }
                                                    // Update coder cards with execution result
                                                    if (newFeed[i].type === 'coder' && newFeed[i].stepId === stepId) {
                                                        newFeed[i] = {
                                                            ...newFeed[i],
                                                            executionResult: tr.content
                                                        };
                                                        break;
                                                    }
                                                }
                                                return newFeed;
                                            });
                                            if (['list_files', 'read_file', 'write_file', 'move_file', 'delete_path', 'create_directory'].includes(tr.name)) {
                                                setFileSystemRefresh(prev => prev + 1);
                                            }
                                            continue;
                                        }

                                        if (data.type === 'step_complete' || data.type === 'step_failed') {
                                            flushUpdates();
                                            const stepId = data.step_id;
                                            const status = data.type === 'step_complete' ? 'completed' : 'failed';
                                            const summary = data.summary || data.error || '';

                                            setStepStatuses(prev => ({ ...prev, [stepId]: status }));
                                            setFeed(prev => {
                                                const newFeed = [...prev];
                                                for (let i = newFeed.length - 1; i >= 0; i--) {
                                                    if (newFeed[i].type === 'step' && newFeed[i].stepId === stepId) {
                                                        newFeed[i] = {
                                                            ...newFeed[i],
                                                            status: status,
                                                            evaluationSummary: summary,
                                                            error: data.error || null,
                                                            isStreaming: false
                                                        };
                                                        break;
                                                    }
                                                }
                                                return newFeed;
                                            });
                                            continue;
                                        }

                                        // === SUPERVISOR EVENTS (Phase 2A) ===
                                        if (data.type === 'supervisor_evaluation') {
                                            flushUpdates();
                                            const stepId = data.step_id;
                                            const qualityScore = data.quality_score;
                                            const issues = data.issues || [];

                                            // Update the step card with supervisor evaluation
                                            setFeed(prev => {
                                                const newFeed = [...prev];
                                                for (let i = newFeed.length - 1; i >= 0; i--) {
                                                    if (newFeed[i].type === 'step' && newFeed[i].stepId === stepId) {
                                                        newFeed[i] = {
                                                            ...newFeed[i],
                                                            supervisorEvaluation: {
                                                                qualityScore,
                                                                issues,
                                                                shouldRetry: data.should_retry,
                                                                shouldEscalate: data.should_escalate,
                                                                reasoning: data.reasoning
                                                            }
                                                        };
                                                        break;
                                                    }
                                                }
                                                return newFeed;
                                            });
                                            continue;
                                        }

                                        if (data.type === 'micro_adjustment') {
                                            flushUpdates();
                                            const stepId = data.step_id;

                                            // Update step status to show retry in progress
                                            setStepStatuses(prev => ({ ...prev, [stepId]: 'retrying' }));

                                            // Update step card to show the adjustment
                                            setFeed(prev => {
                                                const newFeed = [...prev];
                                                for (let i = newFeed.length - 1; i >= 0; i--) {
                                                    if (newFeed[i].type === 'step' && newFeed[i].stepId === stepId) {
                                                        newFeed[i] = {
                                                            ...newFeed[i],
                                                            status: 'retrying',
                                                            microAdjustment: {
                                                                attemptNumber: data.attempt_number,
                                                                adjustmentType: data.adjustment_type,
                                                                reasoning: data.adjustment_reasoning,
                                                                originalArgs: data.original_args,
                                                                adjustedArgs: data.adjusted_args
                                                            }
                                                        };
                                                        break;
                                                    }
                                                }
                                                return newFeed;
                                            });
                                            continue;
                                        }

                                        if (data.type === 'supervisor_thinking' && data.content) {
                                            // Supervisor thinking goes into step evaluation
                                            if (currentStepId) {
                                                stepEvaluation += data.content;
                                                needsFlush = true;
                                            }
                                            continue;
                                        }

                                        // === CODER AGENT EVENTS ===
                                        if (data.type === 'coder_start') {
                                            flushUpdates();
                                            currentStepId = data.step_id;
                                            currentPhase = 'coder';
                                            setOrchestratorPhase('coder');
                                            setStepStatuses(prev => ({ ...prev, [data.step_id]: 'running' }));

                                            // Create a new coder card
                                            setFeed(prev => [...prev, {
                                                type: 'coder',
                                                stepId: data.step_id,
                                                description: data.description,
                                                agentName: data.agent_name || 'Coder Agent',
                                                agentModel: data.agent_model || 'Model',
                                                thinkingLevel: data.thinking_level,
                                                currentPhase: 'algorithm',
                                                algorithmThinking: '',
                                                algorithmSteps: [],
                                                algorithmStreaming: true,
                                                codeThinking: '',
                                                generatedCode: '',
                                                codeStreaming: false,
                                                executionResult: '',
                                                executionError: null,
                                                attempt: 1,
                                                maxAttempts: 3,
                                                retryError: null,
                                            }]);
                                            continue;
                                        }

                                        if (data.type === 'coder_phase') {
                                            flushUpdates();
                                            const stepId = data.step_id || currentStepId;
                                            setFeed(prev => {
                                                const newFeed = [...prev];
                                                for (let i = newFeed.length - 1; i >= 0; i--) {
                                                    if (newFeed[i].type === 'coder' && newFeed[i].stepId === stepId) {
                                                        newFeed[i] = {
                                                            ...newFeed[i],
                                                            currentPhase: data.phase,
                                                            algorithmStreaming: data.phase === 'algorithm',
                                                            codeStreaming: data.phase === 'generation',
                                                        };
                                                        break;
                                                    }
                                                }
                                                return newFeed;
                                            });
                                            continue;
                                        }

                                        if (data.type === 'coder_thinking' && data.content) {
                                            const stepId = data.step_id || currentStepId;
                                            const phase = data.phase; // 'algorithm' or 'generation'
                                            setFeed(prev => {
                                                const newFeed = [...prev];
                                                for (let i = newFeed.length - 1; i >= 0; i--) {
                                                    if (newFeed[i].type === 'coder' && newFeed[i].stepId === stepId) {
                                                        if (phase === 'algorithm') {
                                                            newFeed[i] = {
                                                                ...newFeed[i],
                                                                algorithmThinking: (newFeed[i].algorithmThinking || '') + data.content,
                                                            };
                                                        } else if (phase === 'generation') {
                                                            newFeed[i] = {
                                                                ...newFeed[i],
                                                                codeThinking: (newFeed[i].codeThinking || '') + data.content,
                                                            };
                                                        }
                                                        break;
                                                    }
                                                }
                                                return newFeed;
                                            });
                                            continue;
                                        }

                                        if (data.type === 'coder_algorithm_complete') {
                                            flushUpdates();
                                            const stepId = data.step_id || currentStepId;
                                            const algorithm = data.algorithm || {};
                                            setFeed(prev => {
                                                const newFeed = [...prev];
                                                for (let i = newFeed.length - 1; i >= 0; i--) {
                                                    if (newFeed[i].type === 'coder' && newFeed[i].stepId === stepId) {
                                                        newFeed[i] = {
                                                            ...newFeed[i],
                                                            algorithmSteps: algorithm.algorithm_steps || [],
                                                            algorithmStreaming: false,
                                                            currentPhase: 'generation',
                                                        };
                                                        break;
                                                    }
                                                }
                                                return newFeed;
                                            });
                                            continue;
                                        }

                                        if (data.type === 'coder_code_chunk' && data.content) {
                                            const stepId = data.step_id || currentStepId;
                                            setFeed(prev => {
                                                const newFeed = [...prev];
                                                for (let i = newFeed.length - 1; i >= 0; i--) {
                                                    if (newFeed[i].type === 'coder' && newFeed[i].stepId === stepId) {
                                                        // Accumulate code chunks
                                                        newFeed[i] = {
                                                            ...newFeed[i],
                                                            generatedCode: (newFeed[i].generatedCode || '') + data.content,
                                                        };
                                                        break;
                                                    }
                                                }
                                                return newFeed;
                                            });
                                            continue;
                                        }

                                        if (data.type === 'coder_code_complete') {
                                            flushUpdates();
                                            const stepId = data.step_id || currentStepId;
                                            setFeed(prev => {
                                                const newFeed = [...prev];
                                                for (let i = newFeed.length - 1; i >= 0; i--) {
                                                    if (newFeed[i].type === 'coder' && newFeed[i].stepId === stepId) {
                                                        newFeed[i] = {
                                                            ...newFeed[i],
                                                            generatedCode: data.code || newFeed[i].generatedCode,
                                                            codeStreaming: false,
                                                            currentPhase: 'execution',
                                                        };
                                                        break;
                                                    }
                                                }
                                                return newFeed;
                                            });
                                            continue;
                                        }

                                        if (data.type === 'coder_retry') {
                                            flushUpdates();
                                            const stepId = data.step_id || currentStepId;
                                            setFeed(prev => {
                                                const newFeed = [...prev];
                                                for (let i = newFeed.length - 1; i >= 0; i--) {
                                                    if (newFeed[i].type === 'coder' && newFeed[i].stepId === stepId) {
                                                        newFeed[i] = {
                                                            ...newFeed[i],
                                                            attempt: data.attempt,
                                                            maxAttempts: data.max_attempts || 3,
                                                            retryError: data.error,
                                                            currentPhase: 'generation', // Back to code generation
                                                            codeThinking: '', // Reset for new attempt
                                                            generatedCode: '',
                                                            codeStreaming: true,
                                                        };
                                                        break;
                                                    }
                                                }
                                                return newFeed;
                                            });
                                            continue;
                                        }

                                        if (data.type === 'coder_success') {
                                            flushUpdates();
                                            const stepId = data.step_id || currentStepId;
                                            setStepStatuses(prev => ({ ...prev, [stepId]: 'completed' }));
                                            setFeed(prev => {
                                                const newFeed = [...prev];
                                                for (let i = newFeed.length - 1; i >= 0; i--) {
                                                    if (newFeed[i].type === 'coder' && newFeed[i].stepId === stepId) {
                                                        newFeed[i] = {
                                                            ...newFeed[i],
                                                            currentPhase: 'complete',
                                                        };
                                                        break;
                                                    }
                                                }
                                                return newFeed;
                                            });
                                            continue;
                                        }

                                        if (data.type === 'coder_failed') {
                                            flushUpdates();
                                            const stepId = data.step_id || currentStepId;
                                            setStepStatuses(prev => ({ ...prev, [stepId]: 'failed' }));
                                            setFeed(prev => {
                                                const newFeed = [...prev];
                                                for (let i = newFeed.length - 1; i >= 0; i--) {
                                                    if (newFeed[i].type === 'coder' && newFeed[i].stepId === stepId) {
                                                        newFeed[i] = {
                                                            ...newFeed[i],
                                                            currentPhase: 'failed',
                                                            executionError: data.last_error,
                                                        };
                                                        break;
                                                    }
                                                }
                                                return newFeed;
                                            });
                                            continue;
                                        }

                                        // === CODER V2 EVENTS ===
                                        if (data.type === 'analysis_complete') {
                                            // V2: Analysis phase complete - update status
                                            console.log('[CoderV2] Analysis complete:', data.classification, data.detected_intent);
                                            setActivityStatus(`Analysis: ${data.classification}`);
                                            continue;
                                        }

                                        if (data.type === 'clarification_needed') {
                                            // V2: Need user clarification - show question
                                            console.log('[CoderV2] Clarification needed:', data.question);
                                            flushUpdates();
                                            setFeed(prev => [...prev, {
                                                type: 'synthesis',
                                                content: `**Clarification needed:**\n\n${data.question}`,
                                                thinking: '',
                                                model: currentAgentModel,
                                                agentName: 'Coder Agent',
                                                isStreaming: false,
                                            }]);
                                            setIsProcessing(false);
                                            setActivityStatus('Waiting for clarification');
                                            continue;
                                        }

                                        if (data.type === 'algorithm_generated') {
                                            flushUpdates();
                                            isCoderV2 = true;  // V2 mode confirmed
                                            const algorithm = data.algorithm || {};
                                            // Create a coder_v2 card for algorithm display
                                            setFeed(prev => [...prev, {
                                                type: 'coder_v2',
                                                phase: 'algorithm',
                                                algorithm: algorithm,
                                                algorithmCellId: data.cell_id,
                                                steps: algorithm.algorithm_steps || algorithm.steps || [],
                                                stepProgress: {},
                                                currentStep: null,
                                                exports: {},
                                            }]);
                                            continue;
                                        }

                                        if (data.type === 'step_started') {
                                            flushUpdates();
                                            const stepNum = data.step_number;
                                            setFeed(prev => {
                                                const newFeed = [...prev];
                                                for (let i = newFeed.length - 1; i >= 0; i--) {
                                                    if (newFeed[i].type === 'coder_v2') {
                                                        newFeed[i] = {
                                                            ...newFeed[i],
                                                            phase: 'executing',
                                                            currentStep: stepNum,
                                                            stepProgress: {
                                                                ...newFeed[i].stepProgress,
                                                                [stepNum]: {
                                                                    status: 'running',
                                                                    description: data.description,
                                                                    expectedOutput: data.expected_output,
                                                                }
                                                            }
                                                        };
                                                        break;
                                                    }
                                                }
                                                return newFeed;
                                            });
                                            continue;
                                        }

                                        if (data.type === 'cell_evaluation') {
                                            const stepNum = data.step_number;
                                            setFeed(prev => {
                                                const newFeed = [...prev];
                                                for (let i = newFeed.length - 1; i >= 0; i--) {
                                                    if (newFeed[i].type === 'coder_v2') {
                                                        const progress = newFeed[i].stepProgress[stepNum] || {};
                                                        newFeed[i] = {
                                                            ...newFeed[i],
                                                            stepProgress: {
                                                                ...newFeed[i].stepProgress,
                                                                [stepNum]: {
                                                                    ...progress,
                                                                    cellId: data.cell_id,
                                                                    score: data.score,
                                                                    meetsExpectations: data.meets_expectations,
                                                                    shouldRetry: data.should_retry,
                                                                    feedback: data.feedback,
                                                                    issues: data.issues || [],
                                                                }
                                                            }
                                                        };
                                                        break;
                                                    }
                                                }
                                                return newFeed;
                                            });
                                            continue;
                                        }

                                        if (data.type === 'step_retry') {
                                            const stepNum = data.step_number;
                                            setFeed(prev => {
                                                const newFeed = [...prev];
                                                for (let i = newFeed.length - 1; i >= 0; i--) {
                                                    if (newFeed[i].type === 'coder_v2') {
                                                        const progress = newFeed[i].stepProgress[stepNum] || {};
                                                        newFeed[i] = {
                                                            ...newFeed[i],
                                                            stepProgress: {
                                                                ...newFeed[i].stepProgress,
                                                                [stepNum]: {
                                                                    ...progress,
                                                                    status: 'retrying',
                                                                    attempt: data.attempt,
                                                                    maxRetries: data.max_retries,
                                                                    retryFeedback: data.feedback,
                                                                }
                                                            }
                                                        };
                                                        break;
                                                    }
                                                }
                                                return newFeed;
                                            });
                                            continue;
                                        }

                                        if (data.type === 'step_failed') {
                                            const stepNum = data.step_number;
                                            setFeed(prev => {
                                                const newFeed = [...prev];
                                                for (let i = newFeed.length - 1; i >= 0; i--) {
                                                    if (newFeed[i].type === 'coder_v2') {
                                                        const progress = newFeed[i].stepProgress[stepNum] || {};
                                                        newFeed[i] = {
                                                            ...newFeed[i],
                                                            stepProgress: {
                                                                ...newFeed[i].stepProgress,
                                                                [stepNum]: {
                                                                    ...progress,
                                                                    status: 'failed',
                                                                    error: data.error,
                                                                }
                                                            }
                                                        };
                                                        break;
                                                    }
                                                }
                                                return newFeed;
                                            });
                                            continue;
                                        }

                                        if (data.type === 'step_complete') {
                                            flushUpdates();
                                            const stepNum = data.step_number;
                                            setFeed(prev => {
                                                const newFeed = [...prev];
                                                for (let i = newFeed.length - 1; i >= 0; i--) {
                                                    if (newFeed[i].type === 'coder_v2') {
                                                        const progress = newFeed[i].stepProgress[stepNum] || {};
                                                        newFeed[i] = {
                                                            ...newFeed[i],
                                                            stepProgress: {
                                                                ...newFeed[i].stepProgress,
                                                                [stepNum]: {
                                                                    ...progress,
                                                                    status: 'completed',
                                                                    cellId: data.cell_id,
                                                                    score: data.score,
                                                                    variablesCreated: data.variables_created || [],
                                                                    filesCreated: data.files_created || [],
                                                                }
                                                            }
                                                        };
                                                        break;
                                                    }
                                                }
                                                return newFeed;
                                            });
                                            continue;
                                        }

                                        if (data.type === 'documentation_created') {
                                            setFeed(prev => {
                                                const newFeed = [...prev];
                                                for (let i = newFeed.length - 1; i >= 0; i--) {
                                                    if (newFeed[i].type === 'coder_v2') {
                                                        newFeed[i] = {
                                                            ...newFeed[i],
                                                            exports: data.exports || {},
                                                        };
                                                        break;
                                                    }
                                                }
                                                return newFeed;
                                            });
                                            continue;
                                        }

                                        if (data.type === 'execution_summary') {
                                            // Update coder_v2 card with summary
                                            setFeed(prev => {
                                                const newFeed = [...prev];
                                                for (let i = newFeed.length - 1; i >= 0; i--) {
                                                    if (newFeed[i].type === 'coder_v2') {
                                                        newFeed[i] = {
                                                            ...newFeed[i],
                                                            phase: 'complete',
                                                            summary: data.summary || {},
                                                        };
                                                        break;
                                                    }
                                                }
                                                return newFeed;
                                            });
                                            continue;
                                        }

                                        if (data.type === 'complete') {
                                            flushUpdates();
                                            setIsProcessing(false);
                                            setFeed(prev => {
                                                const newFeed = [...prev];
                                                for (let i = newFeed.length - 1; i >= 0; i--) {
                                                    if (newFeed[i].type === 'synthesis') {
                                                        newFeed[i] = { ...newFeed[i], isStreaming: false };
                                                    }
                                                }
                                                return newFeed;
                                            });
                                            continue;
                                        }

                                        // Memory events (Phase 2B)
                                        if (data.type === 'memory_loaded') {
                                            console.log(`[Memory] Loaded ${data.session_count} sessions (${data.total_tokens}/${data.max_tokens} tokens)`);
                                            continue;
                                        }

                                        if (data.type === 'memory_consolidation_started') {
                                            console.log('[Memory] Consolidation started');
                                            continue;
                                        }

                                        if (data.type === 'memory_consolidation_complete') {
                                            console.log('[Memory] Consolidation complete');
                                            // Trigger refresh for MemoryPanel
                                            setFsUpdateTrigger(prev => prev + 1);
                                            continue;
                                        }
                                    } else {
                                        // ===================================
                                        // LEGACY HANDLERS
                                        // ===================================

                                        if (data.type === 'sync_state') {
                                            flushUpdates();
                                            setIsProcessing(true);
                                            // Show more context during resuming: phase + step if available
                                            const resumePhase = data.phase ? data.phase.replace(/_/g, ' ') : null;
                                            const resumeStep = data.step_id ? ` · step ${data.step_id}` : '';
                                            setActivityStatus(resumePhase ? `Resuming (${resumePhase}${resumeStep})...` : "Resuming...");

                                            if (data.orchestrated) {
                                                // Orchestrated task: set mode flags, don't create a generic card.
                                                // The cached feed (from Step 1) already has proper orchestrator cards.
                                                // Subsequent SSE events will build/update cards properly.
                                                isOrchestratedMode = true;
                                                setIsOrchestrated(true);
                                                if (data.phase) {
                                                    currentPhase = data.phase;
                                                    setOrchestratorPhase(data.phase);
                                                }
                                                if (data.agent_role) currentAgentRole = data.agent_role;
                                                if (data.model) currentAgentModel = data.model;
                                                continue;
                                            }

                                            // Legacy (non-orchestrated) mode: keep existing behavior
                                            if (data.content) accumulatedContent = data.content;
                                            if (data.thinking) accumulatedThinking = data.thinking;
                                            if (data.agent_role) currentAgentRole = data.agent_role;
                                            if (data.model) currentAgentModel = data.model;

                                            // Need to create the card first
                                            setFeed(prev => [...prev, {
                                                type: 'assistant',
                                                content: accumulatedContent,
                                                thinking: accumulatedThinking,
                                                model: currentAgentModel,
                                                agentRole: currentAgentRole
                                            }]);
                                            continue;
                                        }

                                        if ((data.type === 'chunk' || data.type === 'content') && data.content) {
                                            if (isCoderModeLocal) {
                                                // In coder mode, accumulate but don't flush to UI yet
                                                // Final content will be added as a card on complete
                                                coderContent += data.content;
                                                setIsProcessing(true);
                                            } else {
                                                accumulatedContent += data.content;
                                                needsFlush = true;
                                                setIsProcessing(true);
                                            }
                                            continue;
                                        }

                                        if (data.type === 'thinking_chunk' && data.content) {
                                            if (isCoderModeLocal) {
                                                // In coder mode, accumulate thinking separately
                                                coderThinking += data.content;
                                                setIsProcessing(true);
                                            } else {
                                                accumulatedThinking += data.content;
                                                needsFlush = true;
                                                setIsProcessing(true);
                                            }
                                            continue;
                                        }

                                        if (data.type === 'tool_call') {
                                            if (isCoderModeLocal) {
                                                // V2 mode: CoderCardV2 handles step display via step_started/step_complete.
                                                // Skip V1-style step card creation to avoid duplicates.
                                                if (isCoderV2) {
                                                    continue;
                                                }

                                                // V1 mode: Create step cards for each tool call
                                                // First flush any accumulated reasoning as a synthesis card
                                                if (coderContent.trim() || coderThinking.trim()) {
                                                    const reasoningContent = coderContent;
                                                    const reasoningThinking = coderThinking;
                                                    const reasoningModel = currentAgentModel;
                                                    setFeed(prev => [...prev, {
                                                        type: 'synthesis',
                                                        content: reasoningContent,
                                                        thinking: reasoningThinking,
                                                        model: reasoningModel,
                                                        agentName: 'Coder Agent',
                                                        isStreaming: false
                                                    }]);
                                                    coderContent = "";
                                                    coderThinking = "";
                                                }

                                                const toolName = data.tool_call?.name || data.tool_name;
                                                const toolArgs = data.tool_call?.arguments || data.arguments;
                                                if (toolName) {
                                                    coderStepCounter++;
                                                    const stepId = `coder_step_${coderStepCounter}`;
                                                    setFeed(prev => [...prev, {
                                                        type: 'step',
                                                        stepId: stepId,
                                                        description: toolName,
                                                        agentRole: 'coder',
                                                        agentName: 'Coder Agent',
                                                        agentModel: currentAgentModel,
                                                        status: 'running',
                                                        toolName: toolName,
                                                        toolInput: JSON.stringify(toolArgs || {}),
                                                        toolOutput: null,
                                                        isStreaming: true
                                                    }]);
                                                }
                                                continue;
                                            }
                                            flushUpdates();
                                            accumulatedContent = "";
                                            accumulatedThinking = "";
                                            // Handle both formats: {tool_call: {name, arguments}} and {tool_name, arguments}
                                            const toolName = data.tool_call?.name || data.tool_name;
                                            const toolArgs = data.tool_call?.arguments || data.arguments;
                                            if (toolName) {
                                                setFeed(prev => [...prev, {
                                                    type: 'tool',
                                                    toolName: toolName,
                                                    input: JSON.stringify(toolArgs || {}),
                                                    output: null,
                                                    status: 'running',
                                                    agentRole: data.agent_role || currentAgentRole
                                                }]);
                                            }
                                            continue;
                                        }

                                        if (data.type === 'tool_result') {
                                            if (isCoderModeLocal) {
                                                // V2 mode: skip V1-style step card updates
                                                if (isCoderV2) {
                                                    continue;
                                                }

                                                // V1 mode: update the step card with tool result
                                                const toolName = data.tool_result?.name || data.tool_name;
                                                const toolResult = data.tool_result?.content || data.result;
                                                if (toolName) {
                                                    setFeed(prev => {
                                                        const newFeed = [...prev];
                                                        for (let i = newFeed.length - 1; i >= 0; i--) {
                                                            if (newFeed[i].type === 'step' && newFeed[i].toolName === toolName && !newFeed[i].toolOutput) {
                                                                newFeed[i] = {
                                                                    ...newFeed[i],
                                                                    toolOutput: toolResult,
                                                                    status: 'completed',
                                                                    isStreaming: false
                                                                };
                                                                break;
                                                            }
                                                        }
                                                        return newFeed;
                                                    });
                                                }
                                                continue;
                                            }
                                            flushUpdates();
                                            // Handle both formats: {tool_result: {name, content}} and {tool_name, result}
                                            const toolName = data.tool_result?.name || data.tool_name;
                                            const toolResult = data.tool_result?.content || data.result;

                                            if (toolName) {
                                                setFeed(prev => {
                                                    const newFeed = [...prev];
                                                    for (let i = newFeed.length - 1; i >= 0; i--) {
                                                        if (newFeed[i].type === 'tool' && newFeed[i].toolName === toolName && !newFeed[i].output) {
                                                            newFeed[i] = { ...newFeed[i], output: toolResult, status: 'success' };
                                                            break;
                                                        }
                                                    }
                                                    return newFeed;
                                                });
                                                if (['list_files', 'read_file', 'write_file', 'move_file', 'delete_path', 'create_directory'].includes(toolName)) {
                                                    setFileSystemRefresh(prev => prev + 1);
                                                }
                                            }
                                            continue;
                                        }

                                        // === NOTEBOOK CODER EVENTS ===
                                        // These events come from the /coder/chat endpoint (notebook-based coder)

                                        if (data.type === 'notebook_loaded') {
                                            setActivityStatus(`Notebook: ${data.notebook_name} (${data.cell_count} cells)`);
                                            // Load existing cells into notebook viewer
                                            if (data.cells) {
                                                setNotebookData(prev => ({
                                                    name: data.notebook_name,
                                                    path: prev?.path || data.notebook_path,
                                                    cells: Array.isArray(data.cells) ? data.cells : [],
                                                    activeCellId: prev?.activeCellId || null
                                                }));
                                            }
                                            continue;
                                        }

                                        if (data.type === 'cell_added') {
                                            console.log('[Notebook] cell_added:', data.cell_id, data.cell_type);
                                            setActivityStatus(`Added ${data.cell_type} cell [${data.index}]`);
                                            // Add new cell to notebook viewer
                                            setNotebookData(prev => {
                                                const newCell = {
                                                    id: data.cell_id,
                                                    cell_type: data.cell_type,
                                                    source: data.source || '',
                                                    outputs: [],
                                                    status: 'idle',
                                                    execution_count: null
                                                };
                                                // Initialize notebookData if it's null
                                                if (!prev) {
                                                    console.warn('[Notebook] notebookData was null when cell_added received');
                                                    return {
                                                        name: data.notebook_name || 'Untitled',
                                                        path: data.notebook_path || '',
                                                        cells: [newCell],
                                                        activeCellId: data.cell_id
                                                    };
                                                }
                                                const currentCells = Array.isArray(prev.cells) ? prev.cells : [];
                                                return {
                                                    ...prev,
                                                    cells: [...currentCells, newCell],
                                                    activeCellId: data.cell_id
                                                };
                                            });
                                            continue;
                                        }

                                        if (data.type === 'cell_event') {
                                            const event = data.event || {};
                                            const cellId = event.cell_id;
                                            const cellIdShort = cellId?.slice(0, 8) || '?';

                                            if (event.type === 'execution_start') {
                                                setActivityStatus(`Executing cell ${cellIdShort}...`);
                                                // Update cell status in notebook viewer
                                                setNotebookData(prev => {
                                                    if (!prev || !Array.isArray(prev.cells)) return prev;
                                                    return {
                                                        ...prev,
                                                        activeCellId: cellId,
                                                        cells: prev.cells.map(c =>
                                                            c.id === cellId ? { ...c, status: 'running', outputs: [] } : c
                                                        )
                                                    };
                                                });
                                            } else if (event.type === 'output') {
                                                // Add output to cell
                                                setNotebookData(prev => {
                                                    if (!prev || !Array.isArray(prev.cells)) return prev;
                                                    return {
                                                        ...prev,
                                                        cells: prev.cells.map(c =>
                                                            c.id === cellId ? { ...c, outputs: [...(c.outputs || []), event.output] } : c
                                                        )
                                                    };
                                                });
                                            } else if (event.type === 'execution_complete') {
                                                const status = event.status === 'success' ? '✓' : '✗';
                                                setActivityStatus(`Cell ${cellIdShort} ${status}`);
                                                // Update cell status and outputs
                                                setNotebookData(prev => {
                                                    if (!prev || !Array.isArray(prev.cells)) return prev;
                                                    return {
                                                        ...prev,
                                                        cells: prev.cells.map(c =>
                                                            c.id === cellId ? {
                                                                ...c,
                                                                status: event.status,
                                                                execution_count: event.execution_count
                                                            } : c
                                                        )
                                                    };
                                                });
                                            }
                                            continue;
                                        }

                                        if (data.type === 'cell_deleted') {
                                            const cellId = data.cell_id;
                                            console.log('[Notebook] cell_deleted:', cellId, data.reason);
                                            setNotebookData(prev => {
                                                if (!prev || !Array.isArray(prev.cells)) return prev;
                                                return {
                                                    ...prev,
                                                    cells: prev.cells.filter(c => c.id !== cellId)
                                                };
                                            });
                                            continue;
                                        }

                                        if (data.type === 'cell_edited') {
                                            const cellId = data.cell_id;
                                            setActivityStatus(`Edited cell ${cellId?.slice(0, 8) || '?'}`);
                                            // Update cell source in notebook viewer
                                            setNotebookData(prev => {
                                                if (!prev || !Array.isArray(prev.cells)) return prev;
                                                return {
                                                    ...prev,
                                                    activeCellId: cellId,
                                                    cells: prev.cells.map(c =>
                                                        c.id === cellId ? {
                                                            ...c,
                                                            source: data.source || c.source,
                                                            status: 'idle',
                                                            outputs: []
                                                        } : c
                                                    )
                                                };
                                            });
                                            continue;
                                        }

                                        if (data.type === 'notebook_saved') {
                                            setActivityStatus('Notebook saved');
                                            // Trigger filesystem refresh since notebook file changed
                                            setFileSystemRefresh(prev => prev + 1);
                                            continue;
                                        }

                                        if (data.type === 'file_written') {
                                            setActivityStatus(`Wrote file: ${data.path}`);
                                            // Trigger filesystem refresh since file was created/modified
                                            setFileSystemRefresh(prev => prev + 1);
                                            continue;
                                        }

                                        if (data.type === 'file_read') {
                                            setActivityStatus(`Read file: ${data.path}`);
                                            continue;
                                        }

                                        if (data.type === 'complete') {
                                            flushUpdates();
                                            setIsProcessing(false);
                                            setActivityStatus('Ready');

                                            if (isCoderModeLocal) {
                                                // In coder mode, NOW create the final synthesis card
                                                // This ensures it appears AFTER all the step cards
                                                // Use 'synthesis' type to match what reconstruction creates on refresh
                                                if (coderContent.trim() || coderThinking.trim()) {
                                                    // IMPORTANT: Capture values NOW before the setFeed callback runs
                                                    // The callback is executed asynchronously by React, and we reset
                                                    // the accumulators below. Without capturing, the closure would
                                                    // reference the reset (empty) values.
                                                    const finalContent = coderContent;
                                                    const finalThinking = coderThinking;
                                                    const finalModel = currentAgentModel;
                                                    setFeed(prev => [...prev, {
                                                        type: 'synthesis',
                                                        content: finalContent,
                                                        thinking: finalThinking,
                                                        model: finalModel,
                                                        agentName: 'Coder Agent',
                                                        isStreaming: false
                                                    }]);
                                                } else {
                                                    console.log('[Coder] No content to display in synthesis card');
                                                }
                                                // Reset accumulators
                                                coderContent = "";
                                                coderThinking = "";
                                            } else {
                                                // Non-coder mode: Mark the last assistant card as done streaming
                                                setFeed(prev => {
                                                    const newFeed = [...prev];
                                                    for (let i = newFeed.length - 1; i >= 0; i--) {
                                                        if (newFeed[i].type === 'assistant') {
                                                            newFeed[i] = { ...newFeed[i], isStreaming: false };
                                                            break;
                                                        }
                                                    }
                                                    return newFeed;
                                                });
                                            }
                                            continue;
                                        }
                                    }

                                } catch (e) {
                                    console.error('[SSE Parse Error]', e, 'Line:', line);
                                }
                            }

                            // Perform throttled flush if needed
                            if (needsFlush && (Date.now() - lastFlushTime > FLUSH_INTERVAL)) {
                                flushUpdates();
                            }
                        }
                    } catch (e) {
                        if (signal.aborted) break;
                        console.error("Stream dropped", e);
                        await new Promise(r => setTimeout(r, 2000));
                    }
                }
            } catch (e) {
                if (e.name !== 'AbortError') console.error("Load/Subscribe Error", e);
            }
        };

        loadAndSubscribe();

        return () => {
            controller.abort();
        };
    }, [activeTaskId, sseReconnectKey]);

    // Keep feed cache in sync with live feed updates
    useEffect(() => {
        if (activeTaskId && feed.length > 0) {
            feedCacheRef.current.set(activeTaskId, feed);
        }
    }, [feed, activeTaskId]);

    // Restore sidebar sizes from localStorage
    useEffect(() => {
        const valid = new Set(['small', 'normal', 'large']);
        const L = localStorage.getItem('ui:leftSidebarSize');
        const R = localStorage.getItem('ui:rightSidebarSize');
        if (L && valid.has(L)) setLeftSidebarSize(L);
        if (R && valid.has(R)) setRightSidebarSize(R);
    }, []);

    // Save sidebar sizes to localStorage
    useEffect(() => {
        localStorage.setItem('ui:leftSidebarSize', leftSidebarSize);
    }, [leftSidebarSize]);

    useEffect(() => {
        localStorage.setItem('ui:rightSidebarSize', rightSidebarSize);
    }, [rightSidebarSize]);

    // Global keyboard shortcuts
    useEffect(() => {
        const handleKeyDown = (e) => {
            const mod = e.ctrlKey || e.metaKey;

            // Ctrl+Shift+D — Toggle debug panel
            if (mod && e.shiftKey && e.key === 'D') {
                e.preventDefault();
                setShowDebugPanel(prev => !prev);
                return;
            }

            // Ctrl+Shift+E — Export chat to markdown
            if (mod && e.shiftKey && e.key === 'E') {
                e.preventDefault();
                handleExportChat();
                return;
            }

            // Ctrl+Shift+N — New task
            if (mod && e.shiftKey && e.key === 'N') {
                e.preventDefault();
                handleCreateTask();
                return;
            }

            // Escape — Stop processing (when active)
            if (e.key === 'Escape' && isProcessing) {
                e.preventDefault();
                handleStopTask();
                return;
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isProcessing]);

    // Helper to log events for debug panel
    const logEvent = useCallback((type, data) => {
        const timestamp = new Date().toLocaleTimeString('en-US', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            fractionalSecondDigits: 3
        });
        setEventLog(prev => [...prev, { timestamp, type, data }]);
    }, []);

    const handleClearEventLog = useCallback(() => {
        setEventLog([]);
    }, []);

    // --- Handlers ---
    const handleLogout = () => {
        localStorage.removeItem("mentori_token");
        navigate('/login');
    };

    const handleCreateTask = async () => {
        // Include date in task title for uniqueness across days
        const now = new Date();
        const datePart = now.toISOString().slice(0, 10); // YYYY-MM-DD
        const timePart = now.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
        const title = `Task ${datePart} ${timePart}`;

        const token = localStorage.getItem("mentori_token");
        try {
            const res = await fetch(`${config.API_BASE_URL}/tasks/`, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    title,
                    mode: "chat",
                    model_identifier: "ollama::gpt-oss:20b"
                })
            });

            if (res.ok) {
                const newTask = await res.json();
                setTasks(prev => [{
                    id: newTask.id,
                    name: newTask.title,
                    model: newTask.model_identifier,
                    displayId: newTask.display_id,
                    tokens: { total: 0, input: 0, output: 0 }
                }, ...prev]);
                setActiveTaskId(newTask.id);
                setFileSystemRefresh(prev => prev + 1);
            } else {
                alert(`Failed to create task`);
            }
        } catch (e) {
            alert(`Error: ${e.message}`);
        }
    };

    const handleDeleteTask = async (taskId) => {
        // Direct delete without confirmation for faster workflow
        const oldTasks = [...tasks];
        setTasks(prev => prev.filter(t => t.id !== taskId));
        if (activeTaskId === taskId) setActiveTaskId(null);

        const token = localStorage.getItem("mentori_token");
        try {
            await fetch(`${config.API_BASE_URL}/tasks/${taskId}`, {
                method: "DELETE",
                headers: { "Authorization": `Bearer ${token}` }
            });
            setFileSystemRefresh(prev => prev + 1);
        } catch (e) {
            setTasks(oldTasks);
        }
    };

    const handleRenameTask = async (taskId) => {
        const task = tasks.find(t => t.id === taskId);
        const newName = prompt("Rename Task:", task?.name);
        if (!newName || newName === task?.name) return;

        setTasks(prev => prev.map(t => t.id === taskId ? { ...t, name: newName } : t));

        const token = localStorage.getItem("mentori_token");
        try {
            await fetch(`${config.API_BASE_URL}/tasks/${taskId}`, {
                method: "PUT",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ title: newName })
            });
        } catch (e) {
            console.error("Rename Failed", e);
        }
    };

    const handleReorderTask = async (draggedId, targetId) => {
        const draggedIndex = tasks.findIndex(t => t.id === draggedId);
        const targetIndex = tasks.findIndex(t => t.id === targetId);
        if (draggedIndex === -1 || targetIndex === -1) return;

        const newTasks = [...tasks];
        const [draggedTask] = newTasks.splice(draggedIndex, 1);
        newTasks.splice(targetIndex, 0, draggedTask);
        setTasks(newTasks);

        const token = localStorage.getItem("mentori_token");
        try {
            await fetch(`${config.API_BASE_URL}/tasks/reorder`, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    task_ids: newTasks.map(t => t.id)
                })
            });
        } catch (e) {
            console.error("Reorder Failed", e);
        }
    };

    // --- Notebook Handlers ---
    const handleRefreshNotebooks = useCallback(async () => {
        if (!activeTaskId) return;

        const token = localStorage.getItem("mentori_token");
        try {
            const res = await fetch(`${config.API_BASE_URL}/tasks/${activeTaskId}/notebooks`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setAvailableNotebooks(data.notebooks || []);
            }
        } catch (e) {
            console.error("Failed to refresh notebooks:", e);
        }
    }, [activeTaskId]);

    const handleSelectNotebook = useCallback(async (notebookName) => {
        if (!activeTaskId || !notebookName) return;

        const token = localStorage.getItem("mentori_token");
        try {
            const res = await fetch(`${config.API_BASE_URL}/tasks/${activeTaskId}/notebooks/${notebookName}`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setNotebookData({
                    name: data.name,
                    path: data.path,
                    kernel: data.kernel || 'python3',
                    cells: data.cells || [],
                    activeCellId: null
                });
            } else {
                console.error("Failed to load notebook:", notebookName);
            }
        } catch (e) {
            console.error("Failed to load notebook:", e);
        }
    }, [activeTaskId]);

    const handleExecuteCell = useCallback(async (notebookName, cellId) => {
        if (!activeTaskId || !notebookName || !cellId) return;

        // Update cell status to running
        setNotebookData(prev => {
            if (!prev) return prev;
            return {
                ...prev,
                activeCellId: cellId,
                cells: prev.cells.map(c =>
                    c.id === cellId ? { ...c, status: 'running', outputs: [] } : c
                )
            };
        });

        const token = localStorage.getItem("mentori_token");
        try {
            const res = await fetch(`${config.API_BASE_URL}/tasks/${activeTaskId}/notebooks/${notebookName}/cells/${cellId}/execute`, {
                method: 'POST',
                headers: { "Authorization": `Bearer ${token}` }
            });

            if (res.ok) {
                const data = await res.json();
                // Update cell with result
                setNotebookData(prev => {
                    if (!prev) return prev;
                    return {
                        ...prev,
                        cells: prev.cells.map(c =>
                            c.id === cellId ? {
                                ...c,
                                status: data.status,
                                execution_count: data.execution_count,
                                outputs: data.outputs || []
                            } : c
                        )
                    };
                });
            } else {
                // Mark as error
                setNotebookData(prev => {
                    if (!prev) return prev;
                    return {
                        ...prev,
                        cells: prev.cells.map(c =>
                            c.id === cellId ? { ...c, status: 'error' } : c
                        )
                    };
                });
            }
        } catch (e) {
            console.error("Failed to execute cell:", e);
            setNotebookData(prev => {
                if (!prev) return prev;
                return {
                    ...prev,
                    cells: prev.cells.map(c =>
                        c.id === cellId ? { ...c, status: 'error' } : c
                    )
                };
            });
        }
    }, [activeTaskId]);

    const handleRunAllCells = useCallback(async (notebookName) => {
        if (!activeTaskId || !notebookName) return;

        setIsRunningAllCells(true);

        // Mark all code cells as running
        setNotebookData(prev => {
            if (!prev) return prev;
            return {
                ...prev,
                cells: prev.cells.map(c =>
                    c.cell_type === 'code' && c.source?.trim()
                        ? { ...c, status: 'running', outputs: [] }
                        : c
                )
            };
        });

        const token = localStorage.getItem("mentori_token");
        try {
            const res = await fetch(`${config.API_BASE_URL}/tasks/${activeTaskId}/notebooks/${notebookName}/execute-all`, {
                method: 'POST',
                headers: { "Authorization": `Bearer ${token}` }
            });

            if (res.ok) {
                const data = await res.json();
                // Update each cell with its result
                setNotebookData(prev => {
                    if (!prev) return prev;
                    const resultMap = {};
                    for (const r of (data.results || [])) {
                        resultMap[r.cell_id] = r;
                    }
                    return {
                        ...prev,
                        cells: prev.cells.map(c => {
                            const result = resultMap[c.id];
                            if (result) {
                                return {
                                    ...c,
                                    status: result.status,
                                    execution_count: result.execution_count,
                                    outputs: result.outputs || []
                                };
                            }
                            return c;
                        })
                    };
                });
            } else {
                console.error("Failed to run all cells:", await res.text());
                // Reset cells to idle on failure
                setNotebookData(prev => {
                    if (!prev) return prev;
                    return {
                        ...prev,
                        cells: prev.cells.map(c =>
                            c.status === 'running' ? { ...c, status: 'error' } : c
                        )
                    };
                });
            }
        } catch (e) {
            console.error("Failed to run all cells:", e);
            setNotebookData(prev => {
                if (!prev) return prev;
                return {
                    ...prev,
                    cells: prev.cells.map(c =>
                        c.status === 'running' ? { ...c, status: 'error' } : c
                    )
                };
            });
        } finally {
            setIsRunningAllCells(false);
        }
    }, [activeTaskId]);

    const handleUpdateCell = useCallback(async (notebookName, cellId, source) => {
        if (!activeTaskId || !notebookName || !cellId) return;

        const token = localStorage.getItem("mentori_token");
        try {
            const res = await fetch(`${config.API_BASE_URL}/tasks/${activeTaskId}/notebooks/${notebookName}/cells/${cellId}`, {
                method: 'PUT',
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ source })
            });

            if (res.ok) {
                // Update cell in local state
                setNotebookData(prev => {
                    if (!prev) return prev;
                    return {
                        ...prev,
                        cells: prev.cells.map(c =>
                            c.id === cellId ? { ...c, source, status: 'idle', outputs: [] } : c
                        )
                    };
                });
                return true;
            }
            return false;
        } catch (e) {
            console.error("Failed to update cell:", e);
            return false;
        }
    }, [activeTaskId]);

    const handleSendMessage = async (text, isAgentic = false) => {
        if (!activeTaskId || !text.trim()) return;

        const userMsg = { type: 'user', content: text };
        setFeed(prev => [...prev, userMsg]);
        setIsProcessing(true);
        setActivityStatus("Queueing...");

        const token = localStorage.getItem("mentori_token");
        try {
            // Choose endpoint based on mode:
            // - isAgentic=true (robot icon): Use coder endpoint (notebook-based)
            // - isAgentic=false: Use orchestrated chat endpoint
            const endpoint = isAgentic
                ? `${config.API_BASE_URL}/tasks/${activeTaskId}/coder/chat`
                : `${config.API_BASE_URL}/tasks/${activeTaskId}/chat`;

            const payload = isAgentic
                ? { content: text, role: 'user' }
                : { content: text, orchestrated: true };

            const res = await fetch(endpoint, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Failed to send");
            }

            // Only trigger SSE reconnection if the previous connection was aborted (e.g., after Stop)
            // Don't reconnect on normal message sends as it would disrupt the existing SSE stream
            if (chatAbortControllerRef.current?.signal?.aborted) {
                setSseReconnectKey(prev => prev + 1);
            }
        } catch (e) {
            alert(e.message);
            setIsProcessing(false);
            setActivityStatus("Error");
        }
    };

    const handleStopTask = async () => {
        // First abort the client-side fetch stream
        if (chatAbortControllerRef.current) {
            chatAbortControllerRef.current.abort();
        }

        // Then notify the backend to stop the task
        if (activeTaskId) {
            const token = localStorage.getItem("mentori_token");
            try {
                await fetch(`${config.API_BASE_URL}/tasks/${activeTaskId}/stop`, {
                    method: 'POST',
                    headers: { "Authorization": `Bearer ${token}` }
                });
            } catch (e) {
                console.error("Failed to stop task on backend:", e);
            }
        }

        setIsProcessing(false);
        setActivityStatus("Stopped");
    };

    const handleCopyChat = async () => {
        if (!feed || feed.length === 0) return;

        const formattedChat = feed.map(msg => {
            const role = msg.type.toUpperCase();
            let body = "";

            // Handle different message types
            switch (msg.type) {
                case 'user':
                    body = msg.content || "";
                    break;

                case 'tool':
                    // Orchestrator mode tool calls
                    body = `Tool: ${msg.toolName || 'unknown'}`;
                    if (msg.input) body += `\nInput: ${msg.input}`;
                    if (msg.output) body += `\nOutput: ${msg.output}`;
                    break;

                case 'step':
                    // Coder mode step cards
                    body = `Tool: ${msg.toolName || msg.description || 'unknown'}`;
                    if (msg.toolInput) {
                        try {
                            const parsed = JSON.parse(msg.toolInput);
                            body += `\nInput:\n${JSON.stringify(parsed, null, 2)}`;
                        } catch {
                            body += `\nInput: ${msg.toolInput}`;
                        }
                    }
                    if (msg.toolOutput) body += `\nOutput:\n${msg.toolOutput}`;
                    if (msg.error) body += `\nError: ${msg.error}`;
                    break;

                case 'coder':
                    // Coder agent cards with algorithm/code/execution phases
                    body = `Agent: ${msg.agentName || 'Coder Agent'}`;
                    if (msg.algorithmThinking) {
                        body += `\n\n[Algorithm Design]:\n${msg.algorithmThinking}`;
                    }
                    if (msg.algorithmSteps?.length > 0) {
                        body += `\n\nSteps:\n${msg.algorithmSteps.map((s, i) => `${i + 1}. ${s}`).join('\n')}`;
                    }
                    if (msg.generatedCode) {
                        body += `\n\n[Generated Code]:\n\`\`\`python\n${msg.generatedCode}\n\`\`\``;
                    }
                    if (msg.executionResult) {
                        body += `\n\n[Execution Result]:\n${msg.executionResult}`;
                    }
                    if (msg.executionError) {
                        body += `\n\n[Execution Error]:\n${msg.executionError}`;
                    }
                    break;

                case 'analysis':
                case 'synthesis':
                    // Analysis/Synthesis cards
                    if (msg.thinking) body += `[Thinking]:\n${msg.thinking}\n\n`;
                    body += msg.content || msg.text || "";
                    break;

                default:
                    // Default: assistant/llm messages
                    if (msg.thinking) body += `[Thinking]:\n${msg.thinking}\n\n`;
                    body += msg.content || "";
            }

            return `=== ${role} ===\n${body.trim()}\n`;
        }).join("\n\n");

        try {
            await copyToClipboard(formattedChat);
        } catch (err) {
            console.error("Failed to copy", err);
        }
    };

    const handleExportChat = () => {
        if (!feed || feed.length === 0) return;
        const taskName = tasks.find(t => t.id === activeTaskId)?.name;
        const md = feedToMarkdown(feed, taskName);
        const safeName = (taskName || 'mentori-chat').replace(/[^a-zA-Z0-9_-]/g, '_');
        downloadMarkdown(md, `${safeName}.md`);
    };

    const handleRegenerate = () => {
        // Find the last user message and resend it
        const lastUserMsg = [...feed].reverse().find(m => m.type === 'user');
        if (lastUserMsg?.content) {
            handleSendMessage(lastUserMsg.content, false);
        }
    };

    const handleSaveArtifact = (filename, content) => {
        setActiveFile(prev => ({ ...prev, content }));
    };

    const getActiveTaskTokens = () => {
        const task = tasks.find(t => t.id === activeTaskId);
        return task?.tokens || { total: 0, input: 0, output: 0 };
    };

    if (loadingAuth) {
        return <div className="flex h-screen items-center justify-center bg-gray-950 text-gray-500">Loading Mentori...</div>;
    }

    return (
        <>
            <AppShell
                leftSidebarSize={leftSidebarSize}
                setLeftSidebarSize={setLeftSidebarSize}
                leftSidebarWidth={widthFor(leftSidebarSize)}
                rightSidebarSize={rightSidebarSize}
                setRightSidebarSize={setRightSidebarSize}
                rightSidebarWidth={widthFor(rightSidebarSize)}
                sidebar={
                    <ErrorBoundary name="Sidebar">
                    <Sidebar
                        tasks={tasks}
                        activeTaskId={activeTaskId}
                        onSelectTask={setActiveTaskId}
                        onCreateTask={handleCreateTask}
                        onDeleteTask={handleDeleteTask}
                        onRenameTask={handleRenameTask}
                        onReorderTask={handleReorderTask}
                        user={user}
                        onLogout={handleLogout}
                        onAdminClick={() => navigate('/admin')}
                        connectionStatus={connectionStatus}
                    />
                    </ErrorBoundary>
                }
                centerPanel={
                    <ErrorBoundary name="Chat">
                    <CenterPanel
                        activity={isProcessing ? activityStatus : "Ready"}
                        isProcessing={isProcessing}
                        feedItems={feed}
                        onSendMessage={handleSendMessage}
                        onStop={handleStopTask}
                        onCopyChat={handleCopyChat}
                        onExportChat={handleExportChat}
                        onRegenerate={handleRegenerate}
                        followUpSuggestions={!isProcessing ? extractFollowUpSuggestions(feed) : []}
                        activeTaskTokens={getActiveTaskTokens()}
                        activeTaskName={tasks.find(t => t.id === activeTaskId)?.name}
                        activeTaskDisplayId={tasks.find(t => t.id === activeTaskId)?.displayId}
                        connectionStatus={connectionStatus}
                        backendLogs={backendLogs}
                        orchestratorPhase={orchestratorPhase}
                        isOrchestrated={isOrchestrated}
                        stepStatuses={stepStatuses}
                        globalThinkingOpen={globalThinkingOpen}
                        onToggleGlobalThinking={setGlobalThinkingOpen}
                        user={user}
                        activeTaskId={activeTaskId}
                    />
                    </ErrorBoundary>
                }
                rightPanel={
                    <ErrorBoundary name="Workspace">
                    <ArtifactPanel
                        activeFile={activeFile}
                        onSave={handleSaveArtifact}
                        taskId={activeTaskId}
                        activeTaskDisplayId={tasks.find(t => t.id === activeTaskId)?.displayId}
                        onFileLoad={setActiveFile}
                        triggerRefresh={fileSystemRefresh}
                        isCoderMode={isCoderMode}
                        notebookData={notebookData}
                        availableNotebooks={availableNotebooks}
                        onSelectNotebook={handleSelectNotebook}
                        onRefreshNotebooks={handleRefreshNotebooks}
                        onCloseNotebook={() => setNotebookData(null)}
                        onExecuteCell={handleExecuteCell}
                        onUpdateCell={handleUpdateCell}
                        onRunAllCells={handleRunAllCells}
                        isRunningAllCells={isRunningAllCells}
                    />
                    </ErrorBoundary>
                }
            />

            {/* Debug Panel - Toggle with Ctrl+Shift+D */}
            <OrchestratorDebugPanel
                isVisible={showDebugPanel}
                onClose={() => setShowDebugPanel(false)}
                orchestratorPhase={orchestratorPhase}
                isOrchestrated={isOrchestrated}
                stepStatuses={stepStatuses}
                feed={feed}
                eventLog={eventLog}
                onClearLog={handleClearEventLog}
            />
        </>
    );
}
