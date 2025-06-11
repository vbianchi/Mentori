import { h } from 'preact';
import { useState, useEffect, useRef, useCallback } from 'preact/hooks';

// --- SVG Icons (from your version) ---
const ChevronsLeftIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><path d="m11 17-5-5 5-5" /><path d="m18 17-5-5 5-5" /></svg> );
const ChevronsRightIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><path d="m6 17 5-5-5-5" /><path d="m13 17 5-5-5-5" /></svg> );
const FileIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" /><polyline points="14 2 14 8 20 8" /></svg> );
const ArrowLeftIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><path d="m12 19-7-7 7-7"/><path d="M19 12H5"/></svg> );
const UploadCloudIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="M12 12v9"/><path d="m16 16-4-4-4 4"/></svg> );
const ClipboardIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><rect width="8" height="4" x="8" y="2" rx="1" ry="1" /><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" /></svg> );
const ClipboardCheckIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><rect width="8" height="4" x="8" y="2" rx="1" ry="1" /><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" /><path d="m9 14 2 2 4-4" /></svg> );
const CheckCircleIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg> );
const ZapIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg> );
const LoaderIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="animate-spin" {...props}><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg> );
const CircleDotIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="1"/></svg> );
const ChevronDownIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><path d="m6 9 6 6 6-6"/></svg> );
const SlidersIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><line x1="4" x2="4" y1="21" y2="14" /><line x1="4" x2="4" y1="10" y2="3" /><line x1="12" x2="12" y1="21" y2="12" /><line x1="12" x2="12" y1="8" y2="3" /><line x1="20" x2="20" y1="21" y2="16" /><line x1="20" x2="20" y1="12" y2="3" /><line x1="2" x2="6" y1="14" y2="14" /><line x1="10" x2="14" y1="8" y2="8" /><line x1="18" x2="22" y1="16" y2="16" /></svg> );
const BrainCircuitIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><path d="M12 5a3 3 0 1 0-5.993.142" /><path d="M12 5a3 3 0 1 1 5.993.142" /><path d="M12 12a3 3 0 1 0-5.993.142" /><path d="M12 12a3 3 0 1 1 5.993.142" /><path d="M12 19a3 3 0 1 0-5.993.142" /><path d="M12 19a3 3 0 1 1 5.993.142" /><path d="M20 12h-2" /><path d="M6 12H4" /><path d="M12 15v-3" /><path d="M12 8V6" /><path d="M15 12a3 3 0 1 0-6 0" /><path d="M12 9a3 3 0 1 1-6 0" /></svg> );
const BotIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><path d="M12 8V4H8" /><rect width="16" height="12" x="4" y="8" rx="2" /><path d="M2 14h2" /><path d="M20 14h2" /><path d="M15 13v2" /><path d="M9 13v2" /></svg> );

// --- UI Components ---
const CopyButton = ({ textToCopy, className = '' }) => {
    const [copied, setCopied] = useState(false);
    const handleCopy = (e) => {
        e.stopPropagation();
        const textArea = document.createElement("textarea");
        textArea.value = textToCopy;
        textArea.style.position = "fixed";
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try { document.execCommand('copy'); setCopied(true); setTimeout(() => setCopied(false), 2000); } 
        catch (err) { console.error('Failed to copy text: ', err); }
        document.body.removeChild(textArea);
    };
    return (
        <button onClick={handleCopy} class={`p-1.5 rounded-md hover:bg-gray-700 ${className}`}>
            {copied ? <ClipboardCheckIcon class="h-4 w-4 text-green-400" /> : <ClipboardIcon class="h-4 w-4 text-gray-400" />}
        </button>
    );
};

const ToggleButton = ({ isVisible, onToggle, side }) => {
    if (isVisible) return null;
    const positionClass = side === 'left' ? 'left-4' : 'right-4';
    return (
        <div class={`fixed top-1/2 -translate-y-1/2 z-20 ${positionClass}`}>
            <button onClick={onToggle} class="bg-gray-800 hover:bg-gray-700 text-white p-2 h-12 rounded-md border border-gray-600">
                {side === 'left' ? <ChevronsRightIcon class="h-5 w-5" /> : <ChevronsLeftIcon class="h-5 w-5" />}
            </button>
        </div>
    );
};

const InfoBlock = ({ icon, title, children }) => (
    <div class="mt-4 first:mt-0">
        <div class="flex items-center gap-2">
            {icon}
            <h4 class="text-sm font-semibold text-gray-400">{title}</h4>
        </div>
        <div class="mt-1 ml-7 text-sm text-gray-200">{children}</div>
    </div>
);

const StepCard = ({ step }) => {
    const [isExpanded, setIsExpanded] = useState(true);
    const getStatusIcon = () => {
        switch (step.status) {
            case 'in-progress': return <LoaderIcon class="h-5 w-5 text-yellow-400" />;
            case 'completed': return <CheckCircleIcon class="h-5 w-5 text-green-400" />;
            case 'pending': default: return <CircleDotIcon class="h-5 w-5 text-gray-500" />;
        }
    };
    return (
        <div class="bg-gray-800/50 rounded-lg border border-gray-700/50 mb-2 last:mb-0 transition-all">
             <div class="flex items-center gap-4 p-4 cursor-pointer" onClick={() => setIsExpanded(!isExpanded)}>
                {getStatusIcon()}
                <p class="text-gray-200 font-medium flex-1">{step.instruction}</p>
                <ChevronDownIcon class={`h-5 w-5 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
             </div>
             {isExpanded && step.status === 'completed' && step.toolCall && (
                 <div class="p-4 pt-0">
                     <div class="ml-9 pl-4 border-l border-gray-700">
                         <InfoBlock icon={<ZapIcon class="h-4 w-4 text-gray-400" />} title="Action">
                            <pre class="text-xs text-cyan-300 overflow-x-auto p-2 bg-black/20 rounded-md font-mono relative">
                                <CopyButton textToCopy={JSON.stringify(step.toolCall, null, 2)} className="absolute top-1 right-1" />
                                <code>{JSON.stringify(step.toolCall, null, 2)}</code>
                            </pre>
                         </InfoBlock>
                         <InfoBlock icon={<ChevronsRightIcon class="h-4 w-4 text-gray-400" />} title="Observation">
                             <pre class="text-xs text-gray-300 mt-1 whitespace-pre-wrap font-mono relative">
                                 <CopyButton textToCopy={step.toolOutput} className="absolute top-1 right-1" />
                                 {step.toolOutput}
                               </pre>
                         </InfoBlock>
                     </div>
                 </div>
             )}
        </div>
    );
};

// --- NEW COMPONENT FOR DIRECT ANSWERS ---
const AnswerCard = ({ answer, model }) => (
    <div class="p-4 rounded-lg shadow-md bg-gray-800/50 border border-gray-700/50 mb-4">
        <div class="flex items-center gap-3 mb-3">
            <BotIcon class="h-6 w-6 text-green-400" />
            <h3 class="font-bold text-sm text-gray-300 capitalize">Librarian's Answer</h3>
        </div>
        <p class="text-white whitespace-pre-wrap font-medium">{answer}</p>
        <div class="mt-3 pt-2 border-t border-gray-700/50">
            <InfoBlock icon={<BrainCircuitIcon class="h-4 w-4 text-purple-400" />} title="Model Used">
                <span class="text-xs font-medium text-purple-300 font-mono">{model}</span>
            </InfoBlock>
        </div>
    </div>
);

const ModelSelector = ({ label, roleKey, selectedModel, onModelChange, models }) => (
    <div class="mb-4 last:mb-0">
        <label class="block text-sm font-medium text-gray-400 mb-1">{label}</label>
        <div class="relative">
            <select
                value={selectedModel}
                onChange={(e) => onModelChange(roleKey, e.target.value)}
                class="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:ring-2 focus:ring-blue-500 focus:outline-none appearance-none text-sm"
                disabled={!selectedModel || models.length === 0}
            >
                {models.map(model => <option key={model.id} value={model.id}>{model.name}</option>)}
            </select>
            <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-400">
                <ChevronDownIcon class="h-4 w-4" />
            </div>
        </div>
    </div>
);

const SettingsPanel = ({ models, selectedModels, onModelChange }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    return (
        <div class="mt-auto border-t border-gray-700 pt-4">
             <div class="flex items-center justify-between cursor-pointer" onClick={() => setIsExpanded(!isExpanded)}>
                <div class="flex items-center gap-2">
                   <SlidersIcon class="h-5 w-5 text-gray-400" />
                   <h3 class="text-lg font-semibold text-gray-200">Agent Models</h3>
                </div>
                <ChevronDownIcon class={`h-5 w-5 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
             </div>
             {isExpanded && (
                 <div class="mt-4 pl-7">
                     <ModelSelector label="Router Model" roleKey="ROUTER_LLM_ID" models={models} selectedModel={selectedModels.ROUTER_LLM_ID} onModelChange={onModelChange} />
                     <p class="text-xs text-gray-500 -mt-2 mb-4">Classifies intent to route tasks.</p>

                     <ModelSelector label="Planner Model" roleKey="PLANNER_LLM_ID" models={models} selectedModel={selectedModels.PLANNER_LLM_ID} onModelChange={onModelChange} />
                     <p class="text-xs text-gray-500 -mt-2 mb-4">Creates the high-level plan.</p>
                     
                     <ModelSelector label="Controller Model" roleKey="CONTROLLER_LLM_ID" models={models} selectedModel={selectedModels.CONTROLLER_LLM_ID} onModelChange={onModelChange} />
                     <p class="text-xs text-gray-500 -mt-2 mb-4">Handles advanced logic (future self-correction).</p>
                     
                      <ModelSelector label="Executor (Default)" roleKey="EXECUTOR_LLM_ID" models={models} selectedModel={selectedModels.EXECUTOR_LLM_ID} onModelChange={onModelChange} />
                     <p class="text-xs text-gray-500 -mt-2 mb-4">Fallback for simple tool use.</p>

                     <ModelSelector label="Evaluator Model" roleKey="EVALUATOR_LLM_ID" models={models} selectedModel={selectedModels.EVALUATOR_LLM_ID} onModelChange={onModelChange} />
                     <p class="text-xs text-gray-500 -mt-2 mb-4">Validates step outcomes.</p>
                 </div>
             )}
        </div>
    )
}

// --- Main App Component (Integrated) ---
export function App() {
    const [prompt, setPrompt] = useState("");
    const [planSteps, setPlanSteps] = useState([]);
    const [isThinking, setIsThinking] = useState(false);
    // --- NEW STATE FOR DIRECT ANSWERS ---
    const [directAnswer, setDirectAnswer] = useState(null);
    const [inputValue, setInputValue] = useState("");
    const [connectionStatus, setConnectionStatus] = useState("Disconnected");
    const [workspacePath, setWorkspacePath] = useState(null);
    const [workspaceFiles, setWorkspaceFiles] = useState([]);
    const [workspaceLoading, setWorkspaceLoading] = useState(false);
    const [workspaceError, setWorkspaceError] = useState(null);
    const [selectedFile, setSelectedFile] = useState(null);
    const [fileContent, setFileContent] = useState('');
    const [isFileLoading, setIsFileLoading] = useState(false);
    const [isLeftSidebarVisible, setIsLeftSidebarVisible] = useState(true);
    const [isRightSidebarVisible, setIsRightSidebarVisible] = useState(true);
    const [runModels, setRunModels] = useState(null);
    
    const [availableModels, setAvailableModels] = useState([]);
    const [selectedModels, setSelectedModels] = useState({});

    const handleModelChange = (roleKey, modelId) => {
        setSelectedModels(prev => ({ ...prev, [roleKey]: modelId }));
    };

    const ws = useRef(null);
    const messagesEndRef = useRef(null);
    const fileInputRef = useRef(null);

    const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });

    const fetchWorkspaceFiles = useCallback(async (path) => {
        if (!path) return;
        setWorkspaceLoading(true); setWorkspaceError(null);
        try {
            const workspaceId = path.split('/').pop();
            const response = await fetch(`http://localhost:8766/files?path=${workspaceId}`);
            if (!response.ok) throw new Error((await response.json()).error || 'Failed to fetch files');
            const data = await response.json();
            setWorkspaceFiles(data.files || []);
        } catch (error) {
            console.error("Failed to fetch workspace files:", error); setWorkspaceError(error.message);
        } finally {
            setWorkspaceLoading(false);
        }
    }, []);

    const fetchFileContent = useCallback(async (filename) => {
        if (!workspacePath || !filename) return;
        setIsFileLoading(true); setSelectedFile(filename); setFileContent('');
        try {
            const workspaceId = workspacePath.split('/').pop();
            const response = await fetch(`http://localhost:8766/file-content?path=${workspaceId}&filename=${filename}`);
            if (!response.ok) throw new Error((await response.json()).error || 'Failed to fetch file content');
            setFileContent(await response.text());
        } catch (error) {
            console.error("Failed to fetch file content:", error); setFileContent(`Error loading file: ${error.message}`);
        } finally {
            setIsFileLoading(false);
        }
    }, [workspacePath]);

    const handleFileUpload = useCallback(async (e) => {
        const file = e.target.files[0];
        if (!file || !workspacePath) return;
        setWorkspaceLoading(true);
        const workspaceId = workspacePath.split('/').pop();
        const formData = new FormData();
        formData.append('file', file);
        formData.append('workspace_id', workspaceId);
        try {
            const response = await fetch('http://localhost:8766/upload', { method: 'POST', body: formData });
            if (!response.ok) throw new Error((await response.json()).error || 'File upload failed');
            await fetchWorkspaceFiles(workspacePath);
        } catch (error) {
            console.error('File upload error:', error); setWorkspaceError(`Upload failed: ${error.message}`);
        } finally {
            setWorkspaceLoading(false);
            if(fileInputRef.current) fileInputRef.current.value = "";
        }
    }, [workspacePath, fetchWorkspaceFiles]);

    useEffect(() => {
        const fetchModels = async () => {
            try {
                const response = await fetch('http://localhost:8766/api/models');
                if (!response.ok) throw new Error('Failed to fetch model configuration.');
                const config = await response.json();
                if (config.available_models && config.available_models.length > 0) {
                    setAvailableModels(config.available_models);
                    setSelectedModels(config.default_models);
                } else {
                    console.error("No available models returned from the backend.");
                }
            } catch (error) {
                console.error("Failed to fetch models:", error);
            }
        };
        fetchModels();
    }, []);

    // Effect for WebSocket connection
    useEffect(() => {
        function connect() {
            setConnectionStatus("Connecting...");
            ws.current = new WebSocket("ws://localhost:8765");
            ws.current.onopen = () => setConnectionStatus("Connected");
            ws.current.onclose = () => { setConnectionStatus("Disconnected"); setTimeout(connect, 3000); };
            ws.current.onerror = () => ws.current.close();
            ws.current.onmessage = (event) => {
                const newEvent = JSON.parse(event.data);

                // --- LIBRARIAN FIX: Handle the new message type ---
                if (newEvent.type === 'direct_answer') {
                    setDirectAnswer(newEvent.data);
                    setIsThinking(false);
                    return; // Stop processing this event
                }
                
                if (newEvent.type === 'agent_event') {
                    const eventWorkspacePath = newEvent.data?.output?.workspace_path || newEvent.data?.input?.workspace_path;
                    if (eventWorkspacePath) {
                        setWorkspacePath(path => path || eventWorkspacePath);
                    }
    
                    setPlanSteps(prevSteps => {
                        const data = newEvent.data?.output || {};
                        const inputData = newEvent.data?.input || {};
                        if (newEvent.name === 'Chief_Architect' && newEvent.event.includes('end')) {
                            setIsThinking(false);
                            const plan = data.plan || [];
                            return plan.map(step => ({ ...step, status: 'pending' }));
                        }
                        if (newEvent.name === 'Site_Foreman' && newEvent.event.includes('start')) {
                            const stepIndex = inputData.current_step_index;
                            if (prevSteps[stepIndex]) {
                                const newSteps = [...prevSteps];
                                newSteps[stepIndex] = { ...newSteps[stepIndex], status: 'in-progress' };
                                return newSteps;
                            }
                        }
                        if (newEvent.name === 'Worker' && newEvent.event.includes('end')) {
                            const stepIndex = inputData.current_step_index;
                             if (prevSteps[stepIndex]) {
                                const newSteps = [...prevSteps];
                                newSteps[stepIndex] = { ...newSteps[stepIndex], status: 'completed', toolCall: inputData.current_tool_call, toolOutput: data.tool_output };
                                return newSteps;
                             }
                        }
                        return prevSteps;
                    });
                }
            };
        }
        connect();
        return () => { if (ws.current) { ws.current.onclose = null; ws.current.close(); }};
    }, []);

    useEffect(() => { scrollToBottom(); }, [planSteps, prompt, directAnswer]);

    useEffect(() => {
        if (workspacePath) {
             fetchWorkspaceFiles(workspacePath);
        }
    }, [planSteps, workspacePath, fetchWorkspaceFiles]);


    const handleSendMessage = (e) => {
        e.preventDefault();
        const message = inputValue.trim();
        if (message && ws.current?.readyState === WebSocket.OPEN) {
            setPrompt(message);
            // --- LIBRARIAN FIX: Reset both plan steps and direct answer ---
            setPlanSteps([]);
            setDirectAnswer(null);
            setIsThinking(true);
            setWorkspacePath(null); 
            setWorkspaceFiles([]); 
            setWorkspaceError(null); 
            setSelectedFile(null);
            setRunModels(selectedModels);
            
            const payload = {
                prompt: message,
                llm_config: selectedModels,
            };
            ws.current.send(JSON.stringify(payload));
            
            setInputValue("");
        }
    };

    const getModelNameById = (id) => {
        const model = availableModels.find(m => m.id === id);
        return model ? model.name : id;
    }
    
    return (
        <div class="flex h-screen w-screen p-4 gap-4 bg-gray-900 text-gray-200" style={{fontFamily: "'Inter', sans-serif"}}>
            {!isLeftSidebarVisible && <ToggleButton onToggle={() => setIsLeftSidebarVisible(true)} side="left" />}
            {isLeftSidebarVisible && (
                <div class="h-full w-1/4 min-w-[300px] bg-gray-800/50 rounded-lg border border-gray-700/50 shadow-2xl flex flex-col">
                    <div class="flex justify-between items-center p-6 pb-4 border-b border-gray-700 flex-shrink-0">
                        <h2 class="text-xl font-bold text-white">Tasks</h2>
                        <button onClick={() => setIsLeftSidebarVisible(false)} class="p-1.5 rounded-md hover:bg-gray-700" title="Hide Sidebar"><ChevronsLeftIcon class="h-4 w-4" /></button>
                    </div>
                    <div class="flex flex-col flex-grow p-6 pt-4 min-h-0">
                        <div class="flex-grow overflow-y-auto">
                            <p class="text-gray-400">// Task list will go here.</p>
                        </div>
                        <SettingsPanel 
                            models={availableModels}
                            selectedModels={selectedModels}
                            onModelChange={handleModelChange}
                        />
                    </div>
                </div>
            )}
            
            <div class="flex-1 flex flex-col h-full bg-gray-800/50 rounded-lg border border-gray-700/50 shadow-2xl min-w-0">
                <div class="flex items-center justify-between p-6 border-b border-gray-700 flex-shrink-0">
                   <h1 class="text-2xl font-bold text-white">ResearchAgent</h1>
                   <div class="flex items-center gap-2">
                       <span class="relative flex h-3 w-3">
                         {connectionStatus === 'Connected' && <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>}
                         <span class={`relative inline-flex rounded-full h-3 w-3 ${connectionStatus === 'Connected' ? 'bg-green-500' : 'bg-red-500'}`}></span>
                       </span>
                       <span class="text-sm text-gray-400">{connectionStatus}</span>
                   </div>
                </div>
                <div class="flex-1 overflow-y-auto p-6">
                   {prompt && (
                       <div class="p-4 rounded-lg shadow-md bg-blue-900/50 border border-gray-700/50 mb-4">
                           <h3 class="font-bold text-sm text-gray-300 mb-2 capitalize">You</h3>
                           <p class="text-white whitespace-pre-wrap font-medium">{prompt}</p>
                       </div>
                    )}
                    {isThinking && (
                        <div class="flex items-center gap-4 p-4">
                           <LoaderIcon class="h-5 w-5 text-yellow-400" />
                           <p class="text-gray-300 font-medium">Agent is thinking...</p>
                        </div>
                    )}
                    {/* --- LIBRARIAN FIX: Render the direct answer if it exists --- */}
                    {directAnswer && (
                        <AnswerCard answer={directAnswer} model={getModelNameById(runModels?.ROUTER_LLM_ID)} />
                    )}
                    {planSteps.length > 0 && (
                        <div class="mt-4 border-l-2 border-gray-700/50 pl-6 ml-4">
                            <div class="mb-4 -ml-10">
                                <InfoBlock icon={<BrainCircuitIcon class="h-5 w-5 text-purple-400" />} title="Planner Model">
                                    <span class="text-sm font-medium text-purple-300 font-mono">
                                        {getModelNameById(runModels?.PLANNER_LLM_ID)}
                                    </span>
                                </InfoBlock>
                            </div>
                            <h3 class="text-sm font-bold text-gray-400 mb-2 -ml-2">Execution Plan</h3>
                            {planSteps.map((step, index) => <StepCard key={index} step={step} />)}
                        </div>
                    )}
                   <div ref={messagesEndRef} />
                </div>
                <div class="p-6 border-t border-gray-700 flex-shrink-0">
                    <form onSubmit={handleSendMessage} class="flex gap-3">
                        <textarea value={inputValue} onInput={e => setInputValue(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) handleSendMessage(e); }}
                            class="flex-1 p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:outline-none resize-none"
                            placeholder="Send a message to the agent..." rows="2"
                        ></textarea>
                        <button type="submit" class="px-6 py-2 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:bg-gray-500 transition-colors" disabled={connectionStatus !== 'Connected' || isThinking}>Send</button>
                    </form>
                </div>
            </div>

            {!isRightSidebarVisible && <ToggleButton onToggle={() => setIsRightSidebarVisible(true)} side="right" />}
            {isRightSidebarVisible && (
                <div class="h-full w-1/4 min-w-[300px] bg-gray-800/50 rounded-lg border border-gray-700/50 shadow-2xl flex flex-col">
                    <div class="flex justify-between items-center p-6 pb-4 border-b border-gray-700">
                        <h2 class="text-xl font-bold text-white">Agent Workspace</h2>
                         <button onClick={() => setIsRightSidebarVisible(false)} class="p-1.5 rounded-md hover:bg-gray-700" title="Hide Workspace"><ChevronsRightIcon class="h-4 w-4" /></button>
                    </div>
                    <div class="flex flex-col flex-grow min-h-0 px-6 pb-6 pt-4">
                        {selectedFile ? (
                            <div class="flex flex-col h-full">
                                <div class="flex items-center justify-between gap-2 pb-2 mb-2 border-b border-gray-700 flex-shrink-0">
                                    <div class="flex items-center gap-2 min-w-0">
                                        <button onClick={() => setSelectedFile(null)} class="p-1.5 rounded-md hover:bg-gray-700 flex-shrink-0"><ArrowLeftIcon class="h-4 w-4" /></button>
                                        <span class="font-mono text-sm text-white truncate">{selectedFile}</span>
                                    </div>
                                    <CopyButton textToCopy={fileContent} />
                                </div>
                                <div class="flex-grow bg-gray-900/50 rounded-md overflow-hidden">
                                    <pre class="h-full w-full overflow-auto p-4 text-sm text-gray-300 font-mono">
                                        {isFileLoading ? 'Loading...' : <code>{fileContent}</code>}
                                    </pre>
                                </div>
                            </div>
                        ) : (
                             <div class="flex flex-col flex-grow min-h-0">
                                <div class="flex justify-between items-center mb-2 flex-shrink-0">
                                    <div class="text-xs text-gray-500 truncate" title={workspacePath || 'No active workspace'}>{workspacePath ? `Path: ...${workspacePath.slice(-36)}` : 'No active workspace'}</div>
                                    <input type="file" ref={fileInputRef} onChange={handleFileUpload} class="hidden" />
                                    <button onClick={() => fileInputRef.current?.click()} disabled={!workspacePath || workspaceLoading} class="p-1.5 rounded-md hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed" title="Upload File">
                                        <UploadCloudIcon class="h-4 w-4" />
                                    </button>
                                </div>
                                 <div class="flex-grow bg-gray-900/50 rounded-md p-4 text-sm text-gray-400 font-mono overflow-y-auto">
                                    {workspaceLoading ? <p>Uploading/Refreshing...</p> : workspaceError ? <p class="text-red-400">Error: {workspaceError}</p> : workspaceFiles.length === 0 ? <p>// Workspace is empty.</p> : (
                                        <ul>
                                            {workspaceFiles.map(file => (
                                                <li key={file} onClick={() => fetchFileContent(file)} class="flex items-center gap-2 mb-1 hover:text-white cursor-pointer">
                                                    <FileIcon class="h-4 w-4 text-gray-500" />{file}
                                                </li>
                                            ))}
                                        </ul>
                                    )}
                                 </div>
                             </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
