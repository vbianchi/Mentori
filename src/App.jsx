import { h } from 'preact';
import { useState, useEffect, useRef, useCallback } from 'preact/hooks';
import { ArchitectIcon, ChevronsLeftIcon, ChevronsRightIcon, ChevronDownIcon, EditorIcon, ForemanIcon, LoaderIcon, PencilIcon, PlusCircleIcon, RouterIcon, SlidersIcon, SupervisorIcon, Trash2Icon, UserIcon, WorkerIcon, FileIcon, FolderIcon, ArrowLeftIcon, UploadCloudIcon } from './components/Icons';
import { ArchitectCard, DirectAnswerCard, FinalAnswerCard, SiteForemanCard } from './components/AgentCards';
import { ToggleButton, CopyButton } from './components/Common';

// --- UI Components that are specific to App.jsx ---

const PromptCard = ({ content }) => (
    <div class="mt-8 p-4 rounded-lg shadow-md bg-blue-900/50 border border-gray-700/50">
        <h3 class="font-bold text-sm text-gray-300 mb-2 capitalize flex items-center gap-2"><UserIcon class="h-5 w-5" /> You</h3>
        <p class="text-white whitespace-pre-wrap font-medium">{content}</p>
    </div>
);

const TaskItem = ({ task, isActive, onSelect, onRename, onDelete }) => {
    const [isEditing, setIsEditing] = useState(false);
    const [editText, setEditText] = useState(task.name);
    const inputRef = useRef(null);

    const handleStartEditing = (e) => { e.stopPropagation(); setIsEditing(true); setEditText(task.name); };
    const handleSave = () => { if (editText.trim()) { onRename(task.id, editText.trim()); } setIsEditing(false); };
    const handleKeyDown = (e) => { if (e.key === 'Enter') handleSave(); else if (e.key === 'Escape') { setIsEditing(false); setEditText(task.name); } };
    useEffect(() => { if (isEditing) { inputRef.current?.focus(); inputRef.current?.select(); } }, [isEditing]);
    
    return (
        <div onClick={() => onSelect(task.id)} class={`group flex justify-between items-center p-3 mb-2 rounded-lg cursor-pointer transition-colors ${isActive ? 'bg-blue-600/50' : 'hover:bg-gray-700/50'}`}>
            {isEditing ? ( <input ref={inputRef} type="text" value={editText} onInput={(e) => setEditText(e.target.value)} onBlur={handleSave} onKeyDown={handleKeyDown} onClick={(e) => e.stopPropagation()} class="w-full bg-transparent text-white outline-none"/> ) : ( <p class="font-medium text-white truncate">{task.name}</p> )}
            {!isEditing && ( <div class="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity"> <button onClick={handleStartEditing} class="p-1 hover:text-white" title="Rename Task"><PencilIcon class="h-4 w-4" /></button> <button onClick={(e) => { e.stopPropagation(); onDelete(task.id); }} class="p-1 hover:text-red-400" title="Delete Task"><Trash2Icon class="h-4 w-4" /></button> </div> )}
        </div>
    );
};

const ModelSelector = ({ label, icon, onModelChange, models, selectedModel, roleKey }) => (
    <div class="mb-4 last:mb-0">
        <label class="block text-sm font-medium text-gray-400 mb-1 flex items-center gap-2">{icon}{label}</label>
        <div class="relative"> <select value={selectedModel} onChange={(e) => onModelChange(roleKey, e.target.value)} class="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:ring-2 focus:ring-blue-500 focus:outline-none appearance-none text-sm" disabled={!selectedModel || models.length === 0}> {models.map(model => <option key={model.id} value={model.id}>{model.name}</option>)} </select> <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-400"> <ChevronDownIcon class="h-4 w-4" /> </div> </div>
    </div>
);

const SettingsPanel = ({ models, selectedModels, onModelChange }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const agentRoles = [
        { key: 'ROUTER_LLM_ID', label: 'The Router', icon: <RouterIcon className="h-4 w-4"/>, desc: "Classifies tasks into 3 tracks." },
        { key: 'CHIEF_ARCHITECT_LLM_ID', label: 'The Chief Architect', icon: <ArchitectIcon className="h-4 w-4"/>, desc: "Creates complex, multi-step plans." },
        { key: 'SITE_FOREMAN_LLM_ID', label: 'The Site Foreman', icon: <ForemanIcon className="h-4 w-4"/>, desc: "Prepares tool calls for complex plans." },
        { key: 'PROJECT_SUPERVISOR_LLM_ID', label: 'The Project Supervisor', icon: <SupervisorIcon className="h-4 w-4"/>, desc: "Validates complex step outcomes." },
        { key: 'EDITOR_LLM_ID', label: 'The Editor', icon: <EditorIcon className="h-4 w-4"/>, desc: "Answers questions or summarizes results." },
    ];

    return (
        <div class="mt-auto border-t border-gray-700 pt-4">
             <div class="flex items-center justify-between cursor-pointer" onClick={() => setIsExpanded(!isExpanded)}>
                <div class="flex items-center gap-2"> <SlidersIcon class="h-5 w-5 text-gray-400" /> <h3 class="text-lg font-semibold text-gray-200">Agent Models</h3> </div>
                <ChevronDownIcon class={`h-5 w-5 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
             </div>
             {isExpanded && ( <div class="mt-4 pl-2"> {agentRoles.map(role => ( <div key={role.key}> <ModelSelector label={role.label} roleKey={role.key} icon={role.icon} models={models} selectedModel={selectedModels[role.key]} onModelChange={onModelChange}/> <p class="text-xs text-gray-500 -mt-2 mb-4 pl-7">{role.desc}</p> </div> ))} </div> )}
        </div>
    )
};

// --- NEW Component: Breadcrumbs for File Explorer ---
const Breadcrumbs = ({ path, onNavigate }) => {
    const parts = path.split('/').filter(Boolean);
    
    const handleCrumbClick = (index) => {
        const newPath = parts.slice(0, index + 1).join('/');
        onNavigate(newPath);
    };

    return (
        <div class="flex items-center gap-1.5 text-xs text-gray-500 truncate mb-2 flex-shrink-0">
            <span onClick={() => onNavigate(parts[0])} class="hover:text-white cursor-pointer">Workspace</span>
            {parts.slice(1).map((part, index) => (
                <div key={index} class="flex items-center gap-1.5">
                    <span>/</span>
                    <span onClick={() => handleCrumbClick(index + 1)} class="hover:text-white cursor-pointer">{part}</span>
                </div>
            ))}
        </div>
    );
};


// --- Main App Component ---
export function App() {
    const [tasks, setTasks] = useState([]);
    const [activeTaskId, setActiveTaskId] = useState(null);
    const [isThinking, setIsThinking] = useState(false);
    const [inputValue, setInputValue] = useState("");
    const [connectionStatus, setConnectionStatus] = useState("Disconnected");
    const [isLeftSidebarVisible, setIsLeftSidebarVisible] = useState(true);
    const [isRightSidebarVisible, setIsRightSidebarVisible] = useState(true);

    // --- NEW State for File Explorer ---
    const [workspaceItems, setWorkspaceItems] = useState([]);
    const [currentPath, setCurrentPath] = useState('');
    
    const [workspaceLoading, setWorkspaceLoading] = useState(false);
    const [workspaceError, setWorkspaceError] = useState(null);
    const [selectedFile, setSelectedFile] = useState(null);
    const [fileContent, setFileContent] = useState('');
    const [isFileLoading, setIsFileLoading] = useState(false);
    const [availableModels, setAvailableModels] = useState([]);
    const [selectedModels, setSelectedModels] = useState({});
    const [isAwaitingApproval, setIsAwaitingApproval] = useState(false);
    const [availableTools, setAvailableTools] = useState([]);

    const ws = useRef(null);
    const messagesEndRef = useRef(null);
    const fileInputRef = useRef(null);
    const runModelsRef = useRef({});
    const handlersRef = useRef();

    useEffect(() => {
        // --- MODIFIED: Store a reference to setCurrentPath for use in the websocket handler
        handlersRef.current = {
            fetchWorkspaceFiles,
            activeTaskId,
            setCurrentPath, // Add setCurrentPath to handlers
        };
    });

    useEffect(() => {
        const savedTasks = localStorage.getItem('research_agent_tasks');
        const savedActiveId = localStorage.getItem('research_agent_active_task_id');
        const loadedTasks = savedTasks ? JSON.parse(savedTasks) : [];
        setTasks(loadedTasks);
        if (savedActiveId && loadedTasks.some(t => t.id === savedActiveId)) {
            setActiveTaskId(savedActiveId);
            // --- NEW: Set initial path when active task is loaded
            setCurrentPath(savedActiveId);
        } else if (loadedTasks.length > 0) {
            setActiveTaskId(loadedTasks[0].id);
            // --- NEW: Set initial path for the first task
            setCurrentPath(loadedTasks[0].id);
        }
    }, []);

    useEffect(() => {
        if (tasks.length > 0) {
            localStorage.setItem('research_agent_tasks', JSON.stringify(tasks));
        } else {
            localStorage.removeItem('research_agent_tasks');
        }
    }, [tasks]);

    useEffect(() => {
        if (activeTaskId) {
            localStorage.setItem('research_agent_active_task_id', activeTaskId);
        } else {
            localStorage.removeItem('research_agent_active_task_id');
        }
    }, [activeTaskId]);
    
    const resetWorkspaceViews = () => {
        // --- MODIFIED: Now resets `workspaceItems` instead of `workspaceFiles` ---
        setWorkspaceItems([]);
        setWorkspaceError(null);
        setSelectedFile(null);
    };

    const selectTask = (taskId) => {
        if (taskId !== activeTaskId) {
            setActiveTaskId(taskId);
            setIsThinking(false);
            setIsAwaitingApproval(false);
            resetWorkspaceViews();
            // --- NEW: Set the path to the root of the new task ---
            setCurrentPath(taskId);
        }
    };
    
    const createNewTask = () => {
        const newTaskId = `task_${Date.now()}`;
        const newTask = { id: newTaskId, name: `New Task ${tasks.length + 1}`, history: [] };
        if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ type: 'task_create', task_id: newTaskId }));
            setTasks(prevTasks => [...prevTasks, newTask]);
            selectTask(newTaskId);
        } else {
            alert("Connection not ready. Please wait a moment and try again.");
        }
    };

    const handleRenameTask = (taskId, newName) => {
        setTasks(prevTasks => prevTasks.map(task => task.id === taskId ? { ...task, name: newName } : task));
    };

    const handleDeleteTask = (taskIdToDelete) => {
        if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ type: 'task_delete', task_id: taskIdToDelete }));
        } else {
            alert("Connection not ready. Please wait a moment and try again.");
            return;
        }
        
        const currentTasks = tasks;
        const remainingTasks = currentTasks.filter(task => task.id !== taskIdToDelete);
        
        if (activeTaskId === taskIdToDelete) {
            if (remainingTasks.length > 0) {
                const deletedIndex = currentTasks.findIndex(task => task.id === taskIdToDelete);
                const newActiveIndex = Math.max(0, deletedIndex - 1);
                selectTask(remainingTasks[newActiveIndex].id);
            } else {
                setActiveTaskId(null);
                resetWorkspaceViews();
                setCurrentPath(''); // Reset path if no tasks are left
            }
        }
        setTasks(remainingTasks);
    };

    const handleModelChange = (roleKey, modelId) => {
        setSelectedModels(prev => ({ ...prev, [roleKey]: modelId }));
    };
    
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };
    
    // --- REFACTORED: `fetchWorkspaceFiles` is now `fetchWorkspaceItems` ---
    const fetchWorkspaceFiles = useCallback(async (path) => {
        if (!path) return;
        setWorkspaceLoading(true);
        setWorkspaceError(null);
        try {
            // --- MODIFIED: Use the new API endpoint ---
            const response = await fetch(`http://localhost:8766/api/workspace/items?path=${path}`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to fetch items');
            }
            const data = await response.json();
            // Sort items: folders first, then by name
            const sortedItems = (data.items || []).sort((a, b) => {
                if (a.type === 'directory' && b.type !== 'directory') return -1;
                if (a.type !== 'directory' && b.type === 'directory') return 1;
                return a.name.localeCompare(b.name);
            });
            setWorkspaceItems(sortedItems);
        } catch (error) {
            console.error("Failed to fetch workspace items:", error);
            setWorkspaceError(error.message);
            setWorkspaceItems([]); // Clear items on error
        } finally {
            setWorkspaceLoading(false);
        }
    }, []);

    const fetchFileContent = useCallback(async (path, filename) => {
        if (!path || !filename) return;
        setIsFileLoading(true);
        setSelectedFile(filename);
        setFileContent('');
        try {
            // The path sent to file-content is the directory containing the file
            const dirPath = path.substring(0, path.lastIndexOf('/')) || path;
            const response = await fetch(`http://localhost:8766/file-content?path=${dirPath}&filename=${filename}`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to fetch file content');
            }
            const textContent = await response.text();
            setFileContent(textContent);
        } catch (error) {
            console.error("Failed to fetch file content:", error);
            setFileContent(`Error loading file: ${error.message}`);
        } finally {
            setIsFileLoading(false);
        }
    }, []);
    
    // --- NEW: Handler for navigating the file explorer ---
    const handleNavigation = (item) => {
        if (item.type === 'directory') {
            const newPath = `${currentPath}/${item.name}`;
            setCurrentPath(newPath);
        } else {
            fetchFileContent(currentPath, item.name);
        }
    };
    
    const handleBreadcrumbNav = (path) => {
        setCurrentPath(path);
        setSelectedFile(null); // Deselect file when navigating away
    };

    const handleFileUpload = useCallback(async (e) => {
        const file = e.target.files[0];
        if (!file || !currentPath) return;
        setWorkspaceLoading(true);
        const formData = new FormData();
        formData.append('file', file);
        // --- MODIFIED: Upload to the current path, not just task root ---
        formData.append('workspace_id', currentPath); 
        try {
            const response = await fetch('http://localhost:8766/upload', { method: 'POST', body: formData });
            if (!response.ok) throw new Error((await response.json()).error || 'File upload failed');
            await fetchWorkspaceFiles(currentPath); // Refresh current directory
        } catch (error) {
            console.error('File upload error:', error);
            setWorkspaceError(`Upload failed: ${error.message}`);
        } finally {
            setWorkspaceLoading(false);
            if(fileInputRef.current) fileInputRef.current.value = "";
        }
    }, [currentPath, fetchWorkspaceFiles]);

    useEffect(() => {
        const fetchConfig = async () => {
            try {
                const modelsResponse = await fetch('http://localhost:8766/api/models');
                if (!modelsResponse.ok) throw new Error('Failed to fetch model configuration.');
                const modelsConfig = await modelsResponse.json();
                if (modelsConfig.available_models && modelsConfig.available_models.length > 0) {
                    setAvailableModels(modelsConfig.available_models);
                    setSelectedModels(modelsConfig.default_models);
                    runModelsRef.current = modelsConfig.default_models;
                }
                
                const toolsResponse = await fetch('http://localhost:8766/api/tools');
                if (!toolsResponse.ok) throw new Error('Failed to fetch available tools.');
                const toolsConfig = await toolsResponse.json();
                setAvailableTools(toolsConfig.tools || []);

            } catch (error) {
                console.error("Failed to fetch startup config:", error);
            }
        };
        fetchConfig();
    }, []);

    // --- MODIFIED: Fetch items whenever the currentPath changes ---
    useEffect(() => {
        if (currentPath) {
            fetchWorkspaceFiles(currentPath);
        }
    }, [currentPath, fetchWorkspaceFiles]);
    
    const handleApprovalAction = (feedback, plan = null) => {
        if (ws.current?.readyState !== WebSocket.OPEN) {
            alert("Connection not ready.");
            return;
        }

        setIsAwaitingApproval(false);
        setIsThinking(true);
        
        if (feedback === 'approve' && plan) {
             setTasks(currentTasks => currentTasks.map(task => {
                if (task.id === activeTaskId) {
                    const newHistory = [...task.history];
                    const runContainer = newHistory[newHistory.length-1];
                    if (runContainer && runContainer.type === 'run_container') {
                        const architectPlan = runContainer.children.find(c => c.type === 'architect_plan');
                        if (architectPlan) {
                            architectPlan.steps = plan;
                        }
                    }
                    return {...task, history: newHistory};
                }
                return task;
             }));
        }
        
        const resumeMessage = {
            type: 'resume_agent',
            task_id: activeTaskId,
            feedback: feedback,
        };
        if (plan) {
            resumeMessage.plan = plan;
        }
        ws.current.send(JSON.stringify(resumeMessage));
    };

    const handleModifyAndApprove = (modifiedPlan) => handleApprovalAction('approve', modifiedPlan);
    const handleReject = () => handleApprovalAction('reject');

    useEffect(() => {
        function connect() {
            setConnectionStatus("Connecting...");
            const socket = new WebSocket("ws://localhost:8765");
            ws.current = socket;
            socket.onopen = () => setConnectionStatus("Connected");
            socket.onclose = () => { setConnectionStatus("Disconnected"); setIsAwaitingApproval(false); setTimeout(connect, 5000); };
            socket.onerror = (err) => { console.error("WebSocket error:", err); socket.close(); };

            socket.onmessage = (event) => {
                const newEvent = JSON.parse(event.data);
                
                // --- MODIFIED: Refresh logic to use the current path
                if (newEvent.type === 'final_answer' && newEvent.refresh_workspace) {
                    // Check if the update is for the currently viewed path
                    if (handlersRef.current.activeTaskId === newEvent.task_id) {
                         // We don't know which folder was modified, so we refresh the root
                        handlersRef.current.setCurrentPath(handlersRef.current.activeTaskId);
                    }
                }

                setTasks(currentTasks => {
                    try {
                        const taskIndex = currentTasks.findIndex(t => t.id === newEvent.task_id);
                        if (taskIndex === -1) return currentTasks;
                        
                        const newTasks = [...currentTasks];
                        const taskToUpdate = { ...newTasks[taskIndex] };
                        let newHistory = [...taskToUpdate.history];

                        let runContainer = newHistory.length > 0 && newHistory[newHistory.length - 1].type === 'run_container' 
                            ? newHistory[newHistory.length - 1]
                            : null;
                        
                        if (!runContainer) {
                            runContainer = { type: 'run_container', children: [], isComplete: false };
                            newHistory.push(runContainer);
                        }
                        
                        const eventType = newEvent.type;

                        if (eventType === 'plan_approval_request') {
                            setIsThinking(false);
                            setIsAwaitingApproval(true);
                            runContainer.children.push({ type: 'architect_plan', steps: newEvent.plan, isAwaitingApproval: true });
                        } else if (eventType === 'direct_answer' || eventType === 'final_answer') {
                            setIsThinking(false);
                            setIsAwaitingApproval(false);
                            runContainer.children.push({ type: eventType, content: newEvent.data });
                            runContainer.isComplete = true;
                        } else if (eventType === 'agent_event') {
                            const { name, event: chainEvent, data } = newEvent;
                            const inputData = data.input || {};
                            const outputData = data.output || {};

                            let architectPlan = runContainer.children.find(c => c.type === 'architect_plan');
                            
                            if (name === 'Site_Foreman' && chainEvent === 'on_chain_start' && architectPlan?.isAwaitingApproval) {
                                architectPlan.isAwaitingApproval = false;
                                if (!runContainer.children.some(c => c.type === 'execution_plan')) {
                                    runContainer.children.push({ type: 'execution_plan', steps: architectPlan.steps.map(step => ({...step, status: 'pending'})) });
                                }
                            }

                            let executionPlan = runContainer.children.find(c => c.type === 'execution_plan');
                            if (executionPlan) {
                                const stepIndex = inputData.current_step_index;
                                if (stepIndex !== undefined && executionPlan.steps[stepIndex]) {
                                    let stepToUpdate = { ...executionPlan.steps[stepIndex] };
                                    if (name === 'Site_Foreman' && chainEvent === 'on_chain_start') {
                                        stepToUpdate.status = 'in-progress';
                                    } else if (name === 'Project_Supervisor' && chainEvent === 'on_chain_end') {
                                        stepToUpdate.status = outputData.step_evaluation?.status === 'failure' ? 'failure' : 'completed';
                                        stepToUpdate.toolCall = inputData.current_tool_call;
                                        stepToUpdate.toolOutput = outputData.tool_output;
                                        stepToUpdate.evaluation = outputData.step_evaluation;
                                        // Refresh the current directory after a step completes
                                        if (handlersRef.current.activeTaskId === newEvent.task_id) { 
                                            handlersRef.current.fetchWorkspaceFiles(currentPath);
                                        }
                                    }
                                    executionPlan.steps[stepIndex] = stepToUpdate;
                                }
                            }
                        }

                        taskToUpdate.history = newHistory;
                        newTasks[taskIndex] = taskToUpdate;
                        return newTasks;
                    } catch (error) {
                        console.error("Error processing WebSocket message:", error, "Event:", newEvent);
                        return currentTasks;
                    }
                });
            };
        }
        connect();
        return () => { if (ws.current) { ws.current.onclose = null; ws.current.close(); } };
    }, [currentPath]); // Added currentPath to dependency array

    const activeTask = tasks.find(t => t.id === activeTaskId);
    useEffect(() => { scrollToBottom(); }, [activeTask?.history, isAwaitingApproval]);

    const handleSendMessage = (e) => {
        e.preventDefault();
        const message = inputValue.trim();
        if (!message || !activeTask || connectionStatus !== 'Connected' || isThinking || isAwaitingApproval) return;

        setIsThinking(true);
        runModelsRef.current = selectedModels;
        
        const newPrompt = { type: 'prompt', content: message };
        const newRunContainer = { type: 'run_container', children: [], isComplete: false };

        setTasks(currentTasks => currentTasks.map(task => {
            if (task.id === activeTaskId) {
                const newHistory = [...task.history, newPrompt, newRunContainer];
                return { ...task, history: newHistory };
            }
            return task;
        }));
        
        ws.current.send(JSON.stringify({ type: 'run_agent', prompt: message, llm_config: selectedModels, task_id: activeTaskId }));
        setInputValue("");
    };
    
    return (
        <div class="flex h-screen w-screen p-4 gap-4 bg-gray-900 text-gray-200" style={{fontFamily: "'Inter', sans-serif"}}>
            {!isLeftSidebarVisible && <ToggleButton isVisible={isLeftSidebarVisible} onToggle={() => setIsLeftSidebarVisible(true)} side="left" />}
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
                       if (item.type === 'prompt') {
                           return <PromptCard key={index} content={item.content} />;
                       }
                       if (item.type === 'run_container') {
                            return (
                                <div key={index} class="relative mt-6 pl-8">
                                    <div class="absolute top-5 left-4 h-[calc(100%-2.5rem)] w-0.5 bg-gray-700/50" />
                                    <div class="space-y-4">
                                    {item.children.map((child, childIndex) => {
                                        return (
                                            <div key={childIndex} class="relative">
                                                <div class={`absolute top-6 -left-4 h-0.5 ${child.type === 'execution_plan' ? 'w-8' : 'w-4'} bg-gray-700/50`} />
                                                {(() => {
                                                    switch (child.type) {
                                                        case 'architect_plan': 
                                                            return <ArchitectCard 
                                                                plan={child} 
                                                                isAwaitingApproval={child.isAwaitingApproval}
                                                                onModify={handleModifyAndApprove}
                                                                onReject={handleReject}
                                                                availableTools={availableTools}
                                                            />;
                                                        case 'execution_plan': return <SiteForemanCard plan={child} />;
                                                        case 'direct_answer': return <DirectAnswerCard answer={child.content} />;
                                                        case 'final_answer': return <FinalAnswerCard answer={child.content} />;
                                                        default: return null;
                                                    }
                                                })()}
                                            </div>
                                        );
                                    })}
                                    </div>
                                </div>
                            );
                       }
                       return null;
                   })}

                   {isThinking && ( <div class="flex items-center gap-4 p-4"> <LoaderIcon class="h-5 w-5 text-yellow-400" /> <p class="text-gray-300 font-medium">Agent is thinking...</p> </div> )}
                   <div ref={messagesEndRef} />
                </div>
                <div class="p-6 border-t border-gray-700 flex-shrink-0">
                    <form onSubmit={handleSendMessage} class="flex gap-3">
                        <textarea value={inputValue} onInput={e => setInputValue(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) handleSendMessage(e); }} class="flex-1 p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:outline-none resize-none" placeholder={activeTaskId ? (isAwaitingApproval ? "Approve, modify, or reject the plan above." : "Send a message...") : "Please select or create a task."} rows="2" disabled={!activeTaskId || isThinking || isAwaitingApproval} ></textarea>
                        <button type="submit" class="px-6 py-2 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:bg-gray-500 transition-colors" disabled={connectionStatus !== 'Connected' || isThinking || !activeTaskId || isAwaitingApproval}>Send</button>
                    </form>
                </div>
            </div>

            {!isRightSidebarVisible && <ToggleButton isVisible={isRightSidebarVisible} onToggle={() => setIsRightSidebarVisible(true)} side="right" />}
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
                                <div class="flex-grow bg-gray-900/50 rounded-md overflow-auto p-4">
                                    <pre class="h-full w-full text-sm text-gray-300 font-mono">
                                        {isFileLoading ? 'Loading...' : <code>{fileContent}</code>}
                                    </pre>
                                </div>
                            </div>
                        ) : (
                             <div class="flex flex-col flex-grow min-h-0">
                                 {/* --- NEW: Breadcrumbs and Upload --- */}
                                 <div class="flex justify-between items-center mb-2 flex-shrink-0">
                                    <Breadcrumbs path={currentPath} onNavigate={handleBreadcrumbNav} />
                                    <input type="file" ref={fileInputRef} onChange={handleFileUpload} class="hidden" />
                                    <button onClick={() => fileInputRef.current?.click()} disabled={!currentPath || workspaceLoading} class="p-1.5 rounded-md hover:bg-gray-700 disabled:opacity-50" title="Upload File"> <UploadCloudIcon class="h-4 w-4" /> </button>
                                 </div>
                                 {/* --- MODIFIED: Workspace Rendering Logic --- */}
                                 <div class="flex-grow bg-gray-900/50 rounded-md p-4 text-sm text-gray-400 font-mono overflow-y-auto">
                                    {workspaceLoading ? <div class="flex items-center gap-2"><LoaderIcon class="h-4 w-4"/><span>Loading...</span></div> : 
                                     workspaceError ? <p class="text-red-400">Error: {workspaceError}</p> : 
                                     workspaceItems.length === 0 ? <p>// Directory is empty.</p> : ( 
                                     <ul> 
                                        {workspaceItems.map(item => ( 
                                            <li key={item.name} onClick={() => handleNavigation(item)} title={item.name} class="flex items-center gap-2 mb-1 hover:text-white cursor-pointer truncate"> 
                                                {item.type === 'directory' ? <FolderIcon class="h-4 w-4 text-blue-400 flex-shrink-0" /> : <FileIcon class="h-4 w-4 text-gray-500 flex-shrink-0" />}
                                                <span>{item.name}</span>
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
