import { h } from 'preact';
import { useState, useEffect, useRef, useCallback } from 'preact/hooks';

// --- SVG Icons ---
const ChevronsLeftIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><path d="m11 17-5-5 5-5" /><path d="m18 17-5-5 5-5" /></svg> );
const ChevronsRightIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><path d="m6 17 5-5-5-5" /><path d="m13 17 5-5-5-5" /></svg> );
const FileIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" /><polyline points="14 2 14 8 20 8" /></svg> );
const ArrowLeftIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><path d="m12 19-7-7 7-7"/><path d="M19 12H5"/></svg> );
const UploadCloudIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="M12 12v9"/><path d="m16 16-4-4-4 4"/></svg> );
const ClipboardIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><rect width="8" height="4" x="8" y="2" rx="1" ry="1" /><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" /></svg> );
const ClipboardCheckIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><rect width="8" height="4" x="8" y="2" rx="1" ry="1" /><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" /><path d="m9 14 2 2 4-4" /></svg> );
const CheckCircleIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg> );
const LoaderIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="animate-spin" {...props}><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg> );
const CircleDotIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="1"/></svg> );
const ChevronDownIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><path d="m6 9 6 6 6-6"/></svg> );
const SlidersIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><line x1="4" x2="4" y1="21" y2="14" /><line x1="4" x2="4" y1="10" y2="3" /><line x1="12" x2="12" y1="21" y2="12" /><line x1="12" x2="12" y1="8" y2="3" /><line x1="20" x2="20" y1="21" y2="16" /><line x1="20" x2="20" y1="12" y2="3" /><line x1="2" x2="6" y1="14" y2="14" /><line x1="10" x2="14" y1="8" y2="8" /><line x1="18" x2="22" y1="16" y2="16" /></svg> );
const UserIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg> );
const PlusCircleIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/></svg> );
const PencilIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/><path d="m15 5 4 4"/></svg> );
const Trash2Icon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="m8 6 4-4 4 4"/></svg> );
const ArchitectIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><path d="M12 21v-8a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v8" /><path d="M6 11V7a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v4" /><path d="M18 11V7a2 2 0 0 0-2-2h-4" /><path d="m18 21 3-3" /><path d="m2 21 3-3" /><path d="m18 9 3 3" /><path d="m6 9-3 3" /><path d="M12 9v12" /></svg> );
const LibrarianIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><path d="M3 6h18" /><path d="M4 6V4a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v2" /><path d="M5 6v14a1 1 0 0 0 1 1h3a1 1 0 0 0 1-1V6" /><path d="M15 6v14a1 1 0 0 0 1 1h3a1 1 0 0 0 1-1V6" /><path d="M9 12h6" /></svg> );
const EditorIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><path d="M12 20h9" /><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" /><path d="m15 5 3 3" /></svg> );
const ForemanIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><path d="M12 2a10 10 0 0 0-10 10c0 1.85.63 3.58 1.68 4.95" /><path d="m12 12-2-2" /><path d="M22 12a10 10 0 0 0-10-10" /><path d="m14 12 2-2" /><path d="M12 22a10 10 0 0 0 10-10" /><path d="m12 14 2 2" /><path d="M2.32 16.95A10 10 0 0 0 12 22" /><path d="m10 12-2 2" /></svg> );
const WorkerIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><rect x="2" y="6" width="20" height="12" rx="2" /><path d="M12 12h.01" /><path d="M17 12h.01" /><path d="M7 12h.01" /></svg> );
const SupervisorIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><path d="M12 2a10 10 0 1 0 10 10" /><path d="M12 18a10 10 0 0 0-10-10" /><path d="M12 12a5 5 0 0 1 5 5" /><path d="M12 12a5 5 0 0 0-5 5" /><path d="M7 12a5 5 0 0 0 5-5" /><path d="M7 12a5 5 0 0 1 5-5" /></svg> );
const RouterIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><path d="M2 12h20" /><path d="m5 17 5-5-5-5" /><path d="m19 17-5-5 5-5" /></svg> );

// --- UI Components ---

const PromptCard = ({ content }) => (
    <div class="p-4 rounded-lg shadow-md bg-blue-900/50 border border-gray-700/50 mb-6">
        <h3 class="font-bold text-sm text-gray-300 mb-2 capitalize flex items-center gap-2"><UserIcon class="h-5 w-5" /> You</h3>
        <p class="text-white whitespace-pre-wrap font-medium">{content}</p>
    </div>
);

const TaskItem = ({ task, isActive, onSelect, onRename, onDelete }) => {
    const [isEditing, setIsEditing] = useState(false);
    const [editText, setEditText] = useState(task.name);
    const inputRef = useRef(null);

    const handleStartEditing = (e) => {
        e.stopPropagation();
        setIsEditing(true);
        setEditText(task.name);
    };

    const handleSave = () => {
        if (editText.trim()) {
            onRename(task.id, editText.trim());
        }
        setIsEditing(false);
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') handleSave();
        else if (e.key === 'Escape') { setIsEditing(false); setEditText(task.name); }
    };

    useEffect(() => {
        if (isEditing) { inputRef.current?.focus(); inputRef.current?.select(); }
    }, [isEditing]);
    
    return (
        <div onClick={() => onSelect(task.id)} class={`group flex justify-between items-center p-3 mb-2 rounded-lg cursor-pointer transition-colors ${isActive ? 'bg-blue-600/50' : 'hover:bg-gray-700/50'}`}>
            {isEditing ? ( <input ref={inputRef} type="text" value={editText} onInput={(e) => setEditText(e.target.value)} onBlur={handleSave} onKeyDown={handleKeyDown} onClick={(e) => e.stopPropagation()} class="w-full bg-transparent text-white outline-none"/> ) : ( <p class="font-medium text-white truncate">{task.name}</p> )}
            {!isEditing && ( <div class="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity"> <button onClick={handleStartEditing} class="p-1 hover:text-white" title="Rename Task"><PencilIcon class="h-4 w-4" /></button> <button onClick={(e) => { e.stopPropagation(); onDelete(task.id); }} class="p-1 hover:text-red-400" title="Delete Task"><Trash2Icon class="h-4 w-4" /></button> </div> )}
        </div>
    );
};

const CopyButton = ({ textToCopy, className = '' }) => {
    const [copied, setCopied] = useState(false);
    const handleCopy = (e) => {
        e.stopPropagation();
        const textArea = document.createElement("textarea");
        textArea.value = textToCopy;
        textArea.style.position = "fixed"; document.body.appendChild(textArea);
        textArea.focus(); textArea.select();
        try { document.execCommand('copy'); setCopied(true); setTimeout(() => setCopied(false), 2000); }
        catch (err) { console.error('Failed to copy text: ', err); }
        document.body.removeChild(textArea);
    };
    return ( <button onClick={handleCopy} class={`p-1.5 rounded-md hover:bg-gray-700 ${className}`}> {copied ? <ClipboardCheckIcon class="h-4 w-4 text-green-400" /> : <ClipboardIcon class="h-4 w-4 text-gray-400" />} </button> );
};

const ToggleButton = ({ isVisible, onToggle, side }) => {
    if (isVisible) return null;
    const positionClass = side === 'left' ? 'left-4' : 'right-4';
    return ( <div class={`fixed top-1/2 -translate-y-1/2 z-20 ${positionClass}`}> <button onClick={onToggle} class="bg-gray-800 hover:bg-gray-700 text-white p-2 h-12 rounded-md border border-gray-600"> {side === 'left' ? <ChevronsRightIcon class="h-5 w-5" /> : <ChevronsLeftIcon class="h-5 w-5" />} </button> </div> );
};

const AgentResponseCard = ({ icon, title, children }) => (
    <div class="p-4 rounded-lg shadow-md bg-gray-800/50 border border-gray-700/50">
        <h3 class="font-bold text-sm text-gray-300 mb-3 capitalize flex items-center gap-2">{icon}{title}</h3>
        <div class="pl-1">{children}</div>
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
        <div class="bg-gray-900/50 rounded-lg border border-gray-700/50 mb-2 last:mb-0 transition-all">
             <div class="flex items-center gap-4 p-4 cursor-pointer" onClick={() => setIsExpanded(!isExpanded)}>
                {getStatusIcon()}
                <p class="text-gray-200 font-medium flex-1">{step.instruction}</p>
                <ChevronDownIcon class={`h-5 w-5 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
             </div>
             {isExpanded && step.status === 'completed' && step.toolCall && (
                <div class="p-4 pt-0">
                    <div class="ml-9 pl-4 border-l-2 border-gray-700 space-y-4">
                        <div>
                           <div class="flex items-center gap-2 text-sm font-semibold text-gray-400"> <WorkerIcon class="h-4 w-4" /> <span>The Worker: Execute Step</span> </div>
                           <pre class="text-xs text-cyan-300 overflow-x-auto p-2 mt-1 ml-7 bg-black/20 rounded-md font-mono relative"> <CopyButton textToCopy={JSON.stringify(step.toolCall, null, 2)} className="absolute top-1 right-1" /> <code>{JSON.stringify(step.toolCall, null, 2)}</code> </pre>
                        </div>
                        <div>
                           <div class="flex items-center gap-2 text-sm font-semibold text-gray-400"> <SupervisorIcon class="h-4 w-4" /> <span>The Project Supervisor: Evaluation</span> </div>
                           <pre class="text-xs text-gray-300 mt-1 ml-7 whitespace-pre-wrap font-mono relative bg-black/20 p-2 rounded-md"> <CopyButton textToCopy={step.evaluation?.reasoning || 'No evaluation.'} className="absolute top-1 right-1" /> {step.evaluation?.reasoning || 'No evaluation provided.'} </pre>
                        </div>
                    </div>
                </div>
             )}
        </div>
    );
};

// --- NEW/REFINED: Agent Response Components ---

const ArchitectCard = ({ plan }) => (
    <AgentResponseCard icon={<ArchitectIcon class="h-5 w-5" />} title="The Chief Architect">
        <h4 class="text-sm font-bold text-gray-400 mb-2">Proposed Plan</h4>
        <ul class="list-decimal list-inside text-gray-300 space-y-1">
            {plan.steps.map(step => <li key={step.step_id}>{step.instruction}</li>)}
        </ul>
    </AgentResponseCard>
);

const SiteForemanCard = ({ plan }) => (
    <AgentResponseCard icon={<ForemanIcon class="h-5 w-5" />} title="The Site Foreman">
        <h4 class="text-sm font-bold text-gray-400 mb-2">Execution Log</h4>
        {plan.steps.map(step => <StepCard key={step.step_id} step={step} />)}
    </AgentResponseCard>
);

const DirectAnswerCard = ({ answer }) => (
    <AgentResponseCard icon={<LibrarianIcon class="h-5 w-5" />} title="The Librarian">
        <p class="text-white whitespace-pre-wrap font-medium">{answer}</p>
    </AgentResponseCard>
);

const FinalAnswerCard = ({ answer }) => {
    const parsedHtml = window.marked ? window.marked.parse(answer) : answer.replace(/\n/g, '<br />');
    return (
        <AgentResponseCard icon={<EditorIcon class="h-5 w-5" />} title="The Editor">
            <div class="prose prose-sm prose-invert max-w-none text-gray-200" dangerouslySetInnerHTML={{ __html: parsedHtml }}></div>
        </AgentResponseCard>
    );
};

const ModelSelector = ({ label, icon, onModelChange, models, selectedModel, roleKey }) => (
    <div class="mb-4 last:mb-0">
        <label class="block text-sm font-medium text-gray-400 mb-1 flex items-center gap-2">{icon}{label}</label>
        <div class="relative"> <select value={selectedModel} onChange={(e) => onModelChange(roleKey, e.target.value)} class="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:ring-2 focus:ring-blue-500 focus:outline-none appearance-none text-sm" disabled={!selectedModel || models.length === 0}> {models.map(model => <option key={model.id} value={model.id}>{model.name}</option>)} </select> <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-400"> <ChevronDownIcon class="h-4 w-4" /> </div> </div>
    </div>
);

const SettingsPanel = ({ models, selectedModels, onModelChange }) => {
    const [isExpanded, setIsExpanded] = useState(true);
    const agentRoles = [
        { key: 'ROUTER_LLM_ID', label: 'The Router', icon: <RouterIcon className="h-4 w-4"/>, desc: "Classifies tasks." },
        { key: 'LIBRARIAN_LLM_ID', label: 'The Librarian', icon: <LibrarianIcon className="h-4 w-4"/>, desc: "Answers simple questions." },
        { key: 'CHIEF_ARCHITECT_LLM_ID', label: 'The Chief Architect', icon: <ArchitectIcon className="h-4 w-4"/>, desc: "Creates the high-level plan." },
        { key: 'SITE_FOREMAN_LLM_ID', label: 'The Site Foreman', icon: <ForemanIcon className="h-4 w-4"/>, desc: "Prepares tool calls." },
        { key: 'WORKER_LLM_ID', label: 'The Worker', icon: <WorkerIcon className="h-4 w-4"/>, desc: "Executes tools (future use)." },
        { key: 'PROJECT_SUPERVISOR_LLM_ID', label: 'The Project Supervisor', icon: <SupervisorIcon className="h-4 w-4"/>, desc: "Validates step outcomes." },
        { key: 'EDITOR_LLM_ID', label: 'The Editor', icon: <EditorIcon className="h-4 w-4"/>, desc: "Synthesizes the final report." },
    ];

    return (
        <div class="mt-auto border-t border-gray-700 pt-4">
             <div class="flex items-center justify-between cursor-pointer" onClick={() => setIsExpanded(!isExpanded)}>
                <div class="flex items-center gap-2"> <SlidersIcon class="h-5 w-5 text-gray-400" /> <h3 class="text-lg font-semibold text-gray-200">Agent Models</h3> </div>
                <ChevronDownIcon class={`h-5 w-5 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
             </div>
             {isExpanded && (
                 <div class="mt-4 pl-2">
                     {agentRoles.map(role => (
                        <div key={role.key}>
                            <ModelSelector label={role.label} roleKey={role.key} icon={role.icon} models={models} selectedModel={selectedModels[role.key]} onModelChange={onModelChange}/>
                            <p class="text-xs text-gray-500 -mt-2 mb-4 pl-7">{role.desc}</p>
                        </div>
                     ))}
                 </div>
             )}
        </div>
    )
}

// --- Main App Component ---
export function App() {
    const [tasks, setTasks] = useState([]);
    const [activeTaskId, setActiveTaskId] = useState(null);
    const [isThinking, setIsThinking] = useState(false);
    const [inputValue, setInputValue] = useState("");
    const [connectionStatus, setConnectionStatus] = useState("Disconnected");
    const [workspaceFiles, setWorkspaceFiles] = useState([]);
    const [workspaceLoading, setWorkspaceLoading] = useState(false);
    const [workspaceError, setWorkspaceError] = useState(null);
    const [selectedFile, setSelectedFile] = useState(null);
    const [fileContent, setFileContent] = useState('');
    const [isFileLoading, setIsFileLoading] = useState(false);
    const [isLeftSidebarVisible, setIsLeftSidebarVisible] = useState(true);
    const [isRightSidebarVisible, setIsRightSidebarVisible] = useState(true);
    const [availableModels, setAvailableModels] = useState([]);
    const [selectedModels, setSelectedModels] = useState({});

    const ws = useRef(null);
    const messagesEndRef = useRef(null);
    const fileInputRef = useRef(null);
    const runModelsRef = useRef({});

    useEffect(() => {
        const savedTasks = localStorage.getItem('research_agent_tasks');
        const savedActiveId = localStorage.getItem('research_agent_active_task_id');
        const loadedTasks = savedTasks ? JSON.parse(savedTasks) : [];
        setTasks(loadedTasks);
        if (savedActiveId && loadedTasks.some(t => t.id === savedActiveId)) { setActiveTaskId(savedActiveId); }
        else if (loadedTasks.length > 0) { setActiveTaskId(loadedTasks[0].id); }
    }, []);

    useEffect(() => {
        if (tasks.length > 0) { localStorage.setItem('research_agent_tasks', JSON.stringify(tasks)); }
        else { localStorage.removeItem('research_agent_tasks'); }
    }, [tasks]);

    useEffect(() => {
        if (activeTaskId) { localStorage.setItem('research_agent_active_task_id', activeTaskId); }
        else { localStorage.removeItem('research_agent_active_task_id'); }
    }, [activeTaskId]);
    
    const resetWorkspaceViews = () => { setWorkspaceFiles([]); setWorkspaceError(null); setSelectedFile(null); };

    const selectTask = (taskId) => {
        if (taskId !== activeTaskId) { setActiveTaskId(taskId); setIsThinking(false); resetWorkspaceViews(); }
    };
    
    const createNewTask = () => {
        const newTaskId = `task_${Date.now()}`;
        const newTask = { id: newTaskId, name: `New Task ${tasks.length + 1}`, history: [] };
        if (ws.current?.readyState === WebSocket.OPEN) { ws.current.send(JSON.stringify({ type: 'task_create', task_id: newTaskId })); setTasks(prevTasks => [...prevTasks, newTask]); selectTask(newTaskId); }
        else { alert("Connection not ready. Please wait a moment and try again."); }
    };

    const handleRenameTask = (taskId, newName) => { setTasks(prevTasks => prevTasks.map(task => task.id === taskId ? { ...task, name: newName } : task)); };

    const handleDeleteTask = (taskIdToDelete) => {
        if (ws.current?.readyState === WebSocket.OPEN) { ws.current.send(JSON.stringify({ type: 'task_delete', task_id: taskIdToDelete })); }
        else { alert("Connection not ready. Please wait a moment and try again."); return; }
        setTasks(currentTasks => {
            const remainingTasks = currentTasks.filter(task => task.id !== taskIdToDelete);
            if (activeTaskId === taskIdToDelete) {
                if (remainingTasks.length > 0) { const deletedIndex = currentTasks.findIndex(task => task.id === taskIdToDelete); const newActiveIndex = Math.max(0, deletedIndex - 1); selectTask(remainingTasks[newActiveIndex].id); }
                else { setActiveTaskId(null); resetWorkspaceViews(); }
            }
            return remainingTasks;
        });
    };

    const handleModelChange = (roleKey, modelId) => { setSelectedModels(prev => ({ ...prev, [roleKey]: modelId })); };
    const scrollToBottom = () => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }); };
    
    const fetchWorkspaceFiles = useCallback(async (path) => {
        if (!path) return;
        setWorkspaceLoading(true); setWorkspaceError(null);
        try {
            const response = await fetch(`http://localhost:8766/files?path=${path}`);
            if (!response.ok) throw new Error((await response.json()).error || 'Failed to fetch files');
            const data = await response.json();
            setWorkspaceFiles(data.files || []);
        } catch (error) { console.error("Failed to fetch workspace files:", error); setWorkspaceError(error.message); }
        finally { setWorkspaceLoading(false); }
    }, []);

    const fetchFileContent = useCallback(async (filename) => {
        if (!activeTaskId || !filename) return;
        setIsFileLoading(true); setSelectedFile(filename); setFileContent('');
        try {
            const response = await fetch(`http://localhost:8766/file-content?path=${activeTaskId}&filename=${filename}`);
            if (!response.ok) throw new Error((await response.json()).error || 'Failed to fetch file content');
            setFileContent(await response.text());
        } catch (error) { console.error("Failed to fetch file content:", error); setFileContent(`Error loading file: ${error.message}`); }
        finally { setIsFileLoading(false); }
    }, [activeTaskId]);

    const handleFileUpload = useCallback(async (e) => {
        const file = e.target.files[0];
        if (!file || !activeTaskId) return;
        setWorkspaceLoading(true);
        const formData = new FormData();
        formData.append('file', file);
        formData.append('workspace_id', activeTaskId);
        try {
            const response = await fetch('http://localhost:8766/upload', { method: 'POST', body: formData });
            if (!response.ok) throw new Error((await response.json()).error || 'File upload failed');
            await fetchWorkspaceFiles(activeTaskId);
        } catch (error) { console.error('File upload error:', error); setWorkspaceError(`Upload failed: ${error.message}`); }
        finally { setWorkspaceLoading(false); if(fileInputRef.current) fileInputRef.current.value = ""; }
    }, [activeTaskId, fetchWorkspaceFiles]);

    useEffect(() => {
        const fetchModels = async () => {
            try {
                const response = await fetch('http://localhost:8766/api/models');
                if (!response.ok) throw new Error('Failed to fetch model configuration.');
                const config = await response.json();
                if (config.available_models && config.available_models.length > 0) { setAvailableModels(config.available_models); setSelectedModels(config.default_models); runModelsRef.current = config.default_models; }
                else { console.error("No available models returned from the backend."); }
            } catch (error) { console.error("Failed to fetch models:", error); }
        };
        fetchModels();
    }, []);

    useEffect(() => {
        function connect() {
            setConnectionStatus("Connecting...");
            const socket = new WebSocket("ws://localhost:8765");
            ws.current = socket;
            socket.onopen = () => setConnectionStatus("Connected");
            socket.onclose = () => { setConnectionStatus("Disconnected"); setTimeout(connect, 5000); };
            socket.onerror = (err) => { console.error("WebSocket error:", err); socket.close(); };
            socket.onmessage = (event) => {
                const newEvent = JSON.parse(event.data);
                
                setTasks(currentTasks => {
                    const taskIndex = currentTasks.findIndex(t => t.id === newEvent.task_id);
                    if (taskIndex === -1) return currentTasks; 

                    const currentTask = currentTasks[taskIndex];
                    let newHistory = [...currentTask.history];
                    let runContainerIndex = newHistory.findIndex(item => item.type === 'run_container');
                    let runContainer = runContainerIndex !== -1 ? {...newHistory[runContainerIndex]} : { type: 'run_container', children: [] };

                    if (newEvent.type === 'direct_answer') {
                        setIsThinking(false);
                        runContainer.children.push({ type: 'direct_answer', content: newEvent.data });
                    } else if (newEvent.type === 'final_answer') {
                        setIsThinking(false);
                        runContainer.children.push({ type: 'final_answer', content: newEvent.data });
                    } else if (newEvent.type === 'agent_event') {
                        const { name, event: chainEvent, data } = newEvent;
                        const inputData = data.input || {};
                        const outputData = data.output || {};

                        let architectPlanIndex = runContainer.children.findIndex(item => item.type === 'architect_plan');
                        let executionPlanIndex = runContainer.children.findIndex(item => item.type === 'execution_plan');

                        if (name === 'Chief_Architect' && chainEvent === 'on_chain_end') {
                            if (outputData.plan && Array.isArray(outputData.plan)) {
                                const newArchitectPlan = { type: 'architect_plan', steps: outputData.plan };
                                runContainer.children.push(newArchitectPlan);
                                const newExecutionPlan = { type: 'execution_plan', steps: outputData.plan.map(step => ({...step, status: 'pending'})) };
                                runContainer.children.push(newExecutionPlan);
                            }
                        } else if (executionPlanIndex !== -1) {
                            let executionPlan = { ...runContainer.children[executionPlanIndex] };
                            let newSteps = [...executionPlan.steps];
                            const stepIndex = inputData.current_step_index;

                            if (stepIndex !== undefined && newSteps[stepIndex]) {
                                if (name === 'Site_Foreman' && chainEvent === 'on_chain_start') {
                                    newSteps[stepIndex] = { ...newSteps[stepIndex], status: 'in-progress' };
                                } else if (name === 'Project_Supervisor' && chainEvent === 'on_chain_end') {
                                    newSteps[stepIndex] = { ...newSteps[stepIndex], status: 'completed', toolCall: inputData.current_tool_call, toolOutput: outputData.tool_output, evaluation: outputData.step_evaluation };
                                    if (activeTaskId === newEvent.task_id) {
                                      fetchWorkspaceFiles(activeTaskId);
                                    }
                                }
                                executionPlan.steps = newSteps;
                                runContainer.children[executionPlanIndex] = executionPlan;
                            }
                        }
                    }

                    if (runContainerIndex === -1) newHistory.push(runContainer);
                    else newHistory[runContainerIndex] = runContainer;
                    
                    const updatedTask = { ...currentTask, history: newHistory };
                    const newTasks = [...currentTasks];
                    newTasks[taskIndex] = updatedTask;
                    return newTasks;
                });
            };
        }
        connect();
        return () => { if (ws.current) { ws.current.onclose = null; ws.current.close(); } };
    }, [activeTaskId, fetchWorkspaceFiles]);

    const activeTask = tasks.find(t => t.id === activeTaskId);
    useEffect(() => { scrollToBottom(); }, [activeTask?.history]);

    const handleSendMessage = (e) => {
        e.preventDefault();
        const message = inputValue.trim();
        if (!message || !activeTask || connectionStatus !== 'Connected' || isThinking) return;

        setIsThinking(true);
        runModelsRef.current = selectedModels;
        
        const newPrompt = { type: 'prompt', content: message };
        setTasks(currentTasks => currentTasks.map(task => task.id === activeTaskId ? { ...task, history: [newPrompt] } : task));
        
        ws.current.send(JSON.stringify({ type: 'run_agent', prompt: message, llm_config: selectedModels, task_id: activeTaskId }));
        setInputValue("");
    };
    
    return (
        <div class="flex h-screen w-screen p-4 gap-4 bg-gray-900 text-gray-200" style={{fontFamily: "'Inter', sans-serif"}}>
            {!isLeftSidebarVisible && <ToggleButton onToggle={() => setIsLeftSidebarVisible(true)} side="left" />}
            {isLeftSidebarVisible && (
                <div class="h-full w-1/4 min-w-[300px] bg-gray-800/50 rounded-lg border border-gray-700/50 shadow-2xl flex flex-col">
                    <div class="flex justify-between items-center p-6 pb-4 border-b border-gray-700 flex-shrink-0">
                        <h2 class="text-xl font-bold text-white">Tasks</h2>
                        <div class="flex items-center gap-2">
                           <button onClick={createNewTask} class="p-1.5 rounded-md hover:bg-gray-700" title="New Task"><PlusCircleIcon class="h-5 w-5" /></button>
                           <button onClick={() => setIsLeftSidebarVisible(false)} class="p-1.5 rounded-md hover:bg-gray-700" title="Hide Sidebar"><ChevronsLeftIcon class="h-4 w-4" /></button>
                        </div>
                    </div>
                    <div class="flex flex-col flex-grow p-6 pt-4 min-h-0">
                        <div class="flex-grow overflow-y-auto pr-2">
                            {tasks.length > 0 ? ( <ul> {tasks.map(task => ( <TaskItem key={task.id} task={task} isActive={activeTaskId === task.id} onSelect={selectTask} onRename={handleRenameTask} onDelete={handleDeleteTask} /> ))} </ul> ) : ( <p class="text-gray-400 text-center mt-4">No tasks yet. Create one!</p> )}
                        </div>
                        <SettingsPanel models={availableModels} selectedModels={selectedModels} onModelChange={handleModelChange} />
                    </div>
                </div>
            )}
            
            <div class="flex-1 flex flex-col h-full bg-gray-800/50 rounded-lg border border-gray-700/50 shadow-2xl min-w-0">
                <div class="flex items-center justify-between p-6 border-b border-gray-700 flex-shrink-0">
                   <h1 class="text-2xl font-bold text-white">ResearchAgent</h1>
                   <div class="flex items-center gap-2">
                       <span class="relative flex h-3 w-3"> {connectionStatus === 'Connected' && <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>} <span class={`relative inline-flex rounded-full h-3 w-3 ${connectionStatus === 'Connected' ? 'bg-green-500' : 'bg-red-500'}`}></span> </span>
                       <span class="text-sm text-gray-400">{connectionStatus}</span>
                   </div>
                </div>
                <div class="flex-1 overflow-y-auto p-6">
                   {activeTask?.history.map((item, index) => {
                       switch (item.type) {
                           case 'prompt':
                               return <PromptCard key={index} content={item.content} />;
                           case 'run_container':
                                return (
                                    <div class="relative pl-6">
                                        <div class="absolute top-0 left-0 h-full w-0.5 bg-gray-700 -ml-px" />
                                        {item.children.map((child, childIndex) => {
                                            switch (child.type) {
                                                case 'architect_plan': return <div class="mb-4"><ArchitectCard key={childIndex} plan={child} /></div>;
                                                case 'execution_plan': return <div class="mb-4"><SiteForemanCard key={childIndex} plan={child} /></div>;
                                                case 'direct_answer': return <div class="mb-4"><DirectAnswerCard key={childIndex} answer={child.content} /></div>;
                                                case 'final_answer': return <div class="mt-4"><FinalAnswerCard key={childIndex} answer={child.content} /></div>;
                                                default: return null;
                                            }
                                        })}
                                    </div>
                                );
                           default:
                               return null;
                       }
                   })}

                   {isThinking && ( <div class="flex items-center gap-4 p-4"> <LoaderIcon class="h-5 w-5 text-yellow-400" /> <p class="text-gray-300 font-medium">Agent is thinking...</p> </div> )}
                   <div ref={messagesEndRef} />
                </div>
                <div class="p-6 border-t border-gray-700 flex-shrink-0">
                    <form onSubmit={handleSendMessage} class="flex gap-3">
                        <textarea value={inputValue} onInput={e => setInputValue(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) handleSendMessage(e); }} class="flex-1 p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:outline-none resize-none" placeholder={activeTaskId ? "Send a message..." : "Please select or create a task."} rows="2" disabled={!activeTaskId || isThinking} ></textarea>
                        <button type="submit" class="px-6 py-2 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:bg-gray-500 transition-colors" disabled={connectionStatus !== 'Connected' || isThinking || !activeTaskId}>Send</button>
                    </form>
                </div>
            </div>

            {!isRightSidebarVisible && <ToggleButton onToggle={() => setIsRightSidebarVisible(true)} side="right" />}
            {isRightSidebarVisible && (
                <div class="h-full w-1/4 min-w-[300px] bg-gray-800/50 rounded-lg border border-gray-700/50 shadow-2xl flex flex-col">
                    <div class="flex justify-between items-center p-6 pb-4 border-b border-gray-700"> <h2 class="text-xl font-bold text-white">Agent Workspace</h2> <button onClick={() => setIsRightSidebarVisible(false)} class="p-1.5 rounded-md hover:bg-gray-700" title="Hide Workspace"><ChevronsRightIcon class="h-4 w-4" /></button> </div>
                    <div class="flex flex-col flex-grow min-h-0 px-6 pb-6 pt-4">
                        {selectedFile ? (
                            <div class="flex flex-col h-full">
                                <div class="flex items-center justify-between gap-2 pb-2 mb-2 border-b border-gray-700 flex-shrink-0">
                                    <div class="flex items-center gap-2 min-w-0"> <button onClick={() => setSelectedFile(null)} class="p-1.5 rounded-md hover:bg-gray-700 flex-shrink-0"><ArrowLeftIcon class="h-4 w-4" /></button> <span class="font-mono text-sm text-white truncate">{selectedFile}</span> </div>
                                    <CopyButton textToCopy={fileContent} />
                                </div>
                                <div class="flex-grow bg-gray-900/50 rounded-md overflow-hidden"> <pre class="h-full w-full overflow-auto p-4 text-sm text-gray-300 font-mono"> {isFileLoading ? 'Loading...' : <code>{fileContent}</code>} </pre> </div>
                            </div>
                        ) : (
                             <div class="flex flex-col flex-grow min-h-0">
                                <div class="flex justify-between items-center mb-2 flex-shrink-0">
                                    <div class="text-xs text-gray-500 truncate" title={activeTaskId || 'No active workspace'}>{activeTaskId ? `Workspace: ${activeTaskId}` : 'No active workspace'}</div>
                                    <input type="file" ref={fileInputRef} onChange={handleFileUpload} class="hidden" />
                                    <button onClick={() => fileInputRef.current?.click()} disabled={!activeTaskId || workspaceLoading} class="p-1.5 rounded-md hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed" title="Upload File"> <UploadCloudIcon class="h-4 w-4" /> </button>
                                </div>
                                 <div class="flex-grow bg-gray-900/50 rounded-md p-4 text-sm text-gray-400 font-mono overflow-y-auto">
                                    {workspaceLoading ? <p>Uploading/Refreshing...</p> : workspaceError ? <p class="text-red-400">Error: {workspaceError}</p> : workspaceFiles.length === 0 ? <p>// Workspace is empty.</p> : ( <ul> {workspaceFiles.map(file => ( <li key={file} onClick={() => fetchFileContent(file)} class="flex items-center gap-2 mb-1 hover:text-white cursor-pointer"> <FileIcon class="h-4 w-4 text-gray-500" />{file} </li> ))} </ul> )}
                                 </div>
                             </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
