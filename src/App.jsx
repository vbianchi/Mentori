import { h } from 'preact';
import { useState, useEffect, useRef, useCallback } from 'preact/hooks';
import { ArchitectIcon, ChevronsLeftIcon, ChevronsRightIcon, ChevronDownIcon, EditorIcon, ForemanIcon, LoaderIcon, PencilIcon, PlusCircleIcon, RouterIcon, SlidersIcon, SupervisorIcon, Trash2Icon, UserIcon, WorkerIcon, FileIcon, FolderIcon, ArrowLeftIcon, UploadCloudIcon, StopCircleIcon, ForgeIcon, BriefcaseIcon } from './components/Icons';
import { ArchitectCard, DirectAnswerCard, FinalAnswerCard, SiteForemanCard } from './components/AgentCards';
import { ToggleButton, CopyButton } from './components/Common';
import { ToolForge } from './components/ToolForge';
import { useTasks } from './hooks/useTasks';
import { useWorkspace } from './hooks/useWorkspace';
import { useSettings } from './hooks/useSettings';
import { useAgent } from './hooks/useAgent';

// --- File Previewer Component ---
const FilePreviewer = ({ currentPath, file, isLoading, content, rawFileUrl }) => {
    // ... (no changes in this component)
    if (isLoading) {
        return <div class="flex items-center justify-center h-full"><LoaderIcon class="h-6 w-6" /></div>;
    }
    if (!file) {
        return <div class="flex items-center justify-center h-full text-gray-500">Select a file to preview</div>;
    }

    const extension = file.name.split('.').pop().toLowerCase();

    if (['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'].includes(extension)) {
        return <img src={rawFileUrl} alt={file.name} class="max-w-full max-h-full object-contain mx-auto" />;
    }

    if (extension === 'md' && window.marked) {
        const parsedHtml = window.marked.parse(content, { breaks: true, gfm: true });
        return <div class="prose prose-sm prose-invert max-w-none p-4" dangerouslySetInnerHTML={{ __html: parsedHtml }}></div>;
    }
    
    if (['csv', 'tsv'].includes(extension)) {
        const delimiter = extension === 'tsv' ? '\t' : ',';
        const rows = content.split('\n').map(row => row.split(delimiter));
        if (rows.length === 0) return <p>Empty {extension.toUpperCase()} file.</p>;
        
        const header = rows[0];
        const body = rows.slice(1);

        return (
             <div class="overflow-auto h-full">
                <table class="w-full text-left text-sm text-gray-300">
                    <thead class="bg-gray-700/50 sticky top-0">
                        <tr>
                            {header.map((col, i) => <th key={i} class="p-2 border-b border-gray-600 font-semibold">{col}</th>)}
                        </tr>
                    </thead>
                    <tbody>
                        {body.map((row, i) => (
                            <tr key={i} class="border-b border-gray-800 last:border-b-0 hover:bg-gray-700/20">
                                {row.map((cell, j) => <td key={j} class="p-2 truncate" title={cell}>{cell}</td>)}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        );
    }
    
    return (
        <pre class="h-full w-full text-sm text-gray-300 font-mono">
            <code>{content}</code>
        </pre>
    );
};


// --- UI Components ---

const PromptCard = ({ content }) => (
    <div class="mt-8 p-4 rounded-lg shadow-md bg-blue-900/50 border border-gray-700/50">
        <h3 class="font-bold text-sm text-gray-300 mb-2 capitalize flex items-center gap-2"><UserIcon class="h-5 w-5" /> You</h3>
        <p class="text-white whitespace-pre-wrap font-medium">{content}</p>
    </div>
);

const TaskItem = ({ task, isActive, isRunning, onSelect, onRename, onDelete }) => {
    const [isEditing, setIsEditing] = useState(false);
    const [editText, setEditText] = useState(task.name);
    const inputRef = useRef(null);

    const handleStartEditing = (e) => { e.stopPropagation(); setIsEditing(true); setEditText(task.name); };
    const handleSave = () => { if (editText.trim()) { onRename(task.id, editText.trim()); } setIsEditing(false); };
    const handleKeyDown = (e) => { if (e.key === 'Enter') handleSave(); else if (e.key === 'Escape') { setIsEditing(false); setEditText(task.name); } };
    useEffect(() => { if (isEditing) { inputRef.current?.focus(); inputRef.current?.select(); } }, [isEditing]);
    
    return (
        <div onClick={() => onSelect(task.id)} class={`group flex justify-between items-center p-3 mb-2 rounded-lg cursor-pointer transition-colors ${isActive ? 'bg-blue-600/50' : 'hover:bg-gray-700/50'}`}>
            <div class="flex items-center gap-2 truncate">
                {isRunning && <LoaderIcon class="h-4 w-4 text-yellow-400 flex-shrink-0" />}
                {isEditing ? ( <input ref={inputRef} type="text" value={editText} onInput={(e) => setEditText(e.target.value)} onBlur={handleSave} onKeyDown={handleKeyDown} onClick={(e) => e.stopPropagation()} class="w-full bg-transparent text-white outline-none"/> ) : ( <p class="font-medium text-white truncate">{task.name}</p> )}
            </div>
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

const ToolboxPanel = ({ tools, enabledTools, onToggleTool }) => {
    const [isExpanded, setIsExpanded] = useState(true);

    return (
        <div class="border-t border-gray-700 pt-4 mt-4">
            <div class="flex items-center justify-between cursor-pointer" onClick={() => setIsExpanded(!isExpanded)}>
                <div class="flex items-center gap-2">
                    <BriefcaseIcon class="h-5 w-5 text-gray-400" />
                    <h3 class="text-lg font-semibold text-gray-200">Active Toolbox</h3>
                </div>
                <ChevronDownIcon class={`h-5 w-5 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
            </div>
            {isExpanded && (
                <div class="mt-4 pl-2 space-y-2 max-h-48 overflow-y-auto pr-2">
                    {tools.map(tool => (
                        <div key={tool.name} class="flex items-center justify-between" title={tool.description}>
                            <span class="text-sm text-gray-300 truncate">{tool.name}</span>
                            <label class="relative inline-flex items-center cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={enabledTools[tool.name] ?? true}
                                    onChange={() => onToggleTool(tool.name)}
                                    class="sr-only peer"
                                />
                                <div class="w-9 h-5 bg-gray-600 rounded-full peer peer-focus:ring-2 peer-focus:ring-blue-500 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
                            </label>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

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
        <div class="border-t border-gray-700 pt-4 mt-6">
             <div class="flex items-center justify-between cursor-pointer" onClick={() => setIsExpanded(!isExpanded)}>
                <div class="flex items-center gap-2"> <SlidersIcon class="h-5 w-5 text-gray-400" /> <h3 class="text-lg font-semibold text-gray-200">Agent Models</h3> </div>
                <ChevronDownIcon class={`h-5 w-5 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
             </div>
             {isExpanded && ( <div class="mt-4 pl-2"> {agentRoles.map(role => ( <div key={role.key}> <ModelSelector label={role.label} roleKey={role.key} icon={role.icon} models={models} selectedModel={selectedModels[role.key]} onModelChange={onModelChange}/> <p class="text-xs text-gray-500 -mt-2 mb-4 pl-7">{role.desc}</p> </div> ))} </div> )}
        </div>
    )
};

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
    const { tasks, setTasks, activeTaskId, selectTask: setActiveTaskId, renameTask } = useTasks();
    const workspace = useWorkspace(activeTaskId);
    const settings = useSettings();

    const [inputValue, setInputValue] = useState("");
    const [isLeftSidebarVisible, setIsLeftSidebarVisible] = useState(true);
    const [isRightSidebarVisible, setIsRightSidebarVisible] = useState(true);
    const [activeView, setActiveView] = useState('tasks');
    const [isAwaitingApproval, setIsAwaitingApproval] = useState(false);
    
    const messagesEndRef = useRef(null);

    // --- REFACTORED: Central message handler for the useAgent hook ---
    const handleIncomingMessage = useCallback((newEvent) => {
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
                
                if (!runContainer && !['agent_started', 'agent_stopped', 'agent_resumed'].includes(newEvent.type)) {
                    runContainer = { type: 'run_container', children: [], isComplete: false };
                    newHistory.push(runContainer);
                }
                
                const eventType = newEvent.type;

                if (eventType === 'plan_approval_request') {
                    setIsAwaitingApproval(true);
                    runContainer.children.push({ type: 'architect_plan', steps: newEvent.plan, isAwaitingApproval: true });
                } else if (eventType === 'direct_answer' || eventType === 'final_answer') {
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
                                if (activeTaskId === newEvent.task_id) { 
                                    workspace.fetchFiles(workspace.currentPath);
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

        if (newEvent.type === 'final_answer' && newEvent.refresh_workspace) {
            if (activeTaskId === newEvent.task_id) {
                workspace.fetchFiles(workspace.currentPath);
            }
        }
    }, [activeTaskId, workspace.currentPath]);

    // --- REFACTORED: Initialize useAgent hook ---
    const agent = useAgent(handleIncomingMessage);

    useEffect(() => {
        if (activeTaskId) {
            workspace.setCurrentPath(activeTaskId);
        }
    }, [activeTaskId]);
    
    const selectTask = (taskId) => {
        if (taskId !== activeTaskId) {
            setActiveTaskId(taskId);
            setIsAwaitingApproval(false);
            workspace.resetWorkspaceViews();
            workspace.setCurrentPath(taskId);
            setActiveView('tasks'); 
        }
    };
    
    const createNewTask = () => {
        const newTaskId = `task_${Date.now()}`;
        agent.createTask(newTaskId); // Inform backend
        const newTask = { id: newTaskId, name: `New Task ${tasks.length + 1}`, history: [] };
        setTasks(prevTasks => [...prevTasks, newTask]);
        selectTask(newTaskId);
    };

    const handleDeleteTask = (taskIdToDelete) => {
        agent.deleteTask(taskIdToDelete); // Inform backend
        const currentTasks = tasks;
        const remainingTasks = currentTasks.filter(task => task.id !== taskIdToDelete);
        
        if (activeTaskId === taskIdToDelete) {
            if (remainingTasks.length > 0) {
                const deletedIndex = currentTasks.findIndex(task => task.id === taskIdToDelete);
                const newActiveIndex = Math.max(0, deletedIndex - 1);
                selectTask(remainingTasks[newActiveIndex].id);
            } else {
                setActiveTaskId(null);
                workspace.resetWorkspaceViews();
                workspace.setCurrentPath('');
            }
        }
        setTasks(remainingTasks);
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        if (workspace.currentPath && activeView === 'tasks') {
            workspace.fetchFiles(workspace.currentPath);
        }
    }, [workspace.currentPath, activeView]);
    
    const handleApprovalAction = (feedback, plan = null) => {
        setIsAwaitingApproval(false);
        const payload = {
            task_id: activeTaskId,
            feedback: feedback,
            enabled_tools: Object.keys(settings.enabledTools).filter(key => settings.enabledTools[key]),
        };
        if (plan) {
            payload.plan = plan;
        }
        agent.resumeAgent(payload); // Use agent hook
    };

    const handleModifyAndApprove = (modifiedPlan) => {
        // Optimistically update the UI with the modified plan
        setTasks(currentTasks => currentTasks.map(task => {
            if (task.id === activeTaskId) {
                const newHistory = [...task.history];
                const runContainer = newHistory[newHistory.length-1];
                if (runContainer?.type === 'run_container') {
                    const architectPlan = runContainer.children.find(c => c.type === 'architect_plan');
                    if (architectPlan) architectPlan.steps = modifiedPlan;
                }
                return {...task, history: newHistory};
            }
            return task;
        }));
        handleApprovalAction('approve', modifiedPlan);
    };
    
    const handleReject = () => {
        handleApprovalAction('reject');
    }

    const activeTask = tasks.find(t => t.id === activeTaskId);
    useEffect(() => { scrollToBottom(); }, [activeTask?.history, isAwaitingApproval]);

    const handleSendMessage = (e) => {
        e.preventDefault();
        const message = inputValue.trim();
        if (!message || !activeTask || agent.connectionStatus !== 'Connected' || agent.runningTasks[activeTaskId] || isAwaitingApproval) return;

        // Optimistically update UI with the new prompt
        const newPrompt = { type: 'prompt', content: message };
        const newRunContainer = { type: 'run_container', children: [], isComplete: false };
        setTasks(currentTasks => currentTasks.map(task => 
            task.id === activeTaskId ? { ...task, history: [...task.history, newPrompt, newRunContainer] } : task
        ));
        
        // Send the command to the agent
        agent.runAgent({ 
            prompt: message, 
            llm_config: settings.selectedModels, 
            task_id: activeTaskId,
            enabled_tools: Object.keys(settings.enabledTools).filter(key => settings.enabledTools[key]),
        });
        setInputValue("");
    };

    const handleStopAgent = () => {
        agent.stopAgent(activeTaskId);
    };
    
    return (
        <div class="flex h-screen w-screen p-4 gap-4 bg-gray-900 text-gray-200" style={{fontFamily: "'Inter', sans-serif"}}>
            {!isLeftSidebarVisible && <ToggleButton isVisible={isLeftSidebarVisible} onToggle={() => setIsLeftSidebarVisible(true)} side="left" />}
            {isLeftSidebarVisible && (
                <div class="h-full w-1/4 min-w-[300px] bg-gray-800/50 rounded-lg border border-gray-700/50 shadow-2xl flex flex-col">
                    <div class="flex justify-between items-center p-6 pb-4 border-b border-gray-700 flex-shrink-0">
                        <h2 class="text-xl font-bold text-white">
                            {activeView === 'tasks' ? 'Tasks' : 'Tool Forge'}
                        </h2>
                        <div class="flex items-center gap-2">
                           {activeView === 'tasks' ? (
                               <button onClick={() => setActiveView('forge')} class="p-1.5 rounded-md hover:bg-gray-700" title="Open Tool Forge">
                                   <ForgeIcon class="h-5 w-5" />
                               </button>
                           ) : (
                                <button onClick={() => setActiveView('tasks')} class="p-1.5 rounded-md hover:bg-gray-700" title="Back to Tasks">
                                   <ChevronsRightIcon class="h-5 w-5" />
                                </button>
                           )}
                           <button onClick={createNewTask} class="p-1.5 rounded-md hover:bg-gray-700" title="New Task"><PlusCircleIcon class="h-5 w-5" /></button>
                           <button onClick={() => setIsLeftSidebarVisible(false)} class="p-1.5 rounded-md hover:bg-gray-700" title="Hide Sidebar"><ChevronsLeftIcon class="h-4 w-4" /></button>
                        </div>
                    </div>
                    
                    {activeView === 'tasks' ? (
                        <div class="flex flex-col flex-grow p-6 pt-4 min-h-0">
                            <div class="flex-grow overflow-y-auto pr-2">
                                {tasks.length > 0 ? ( <ul> {tasks.map(task => ( <TaskItem key={task.id} task={task} isActive={activeTaskId === task.id} isRunning={!!agent.runningTasks[task.id]} onSelect={selectTask} onRename={renameTask} onDelete={handleDeleteTask} /> ))} </ul> ) : ( <p class="text-gray-400 text-center mt-4">No tasks yet. Create one!</p> )}
                            </div>
                            <ToolboxPanel tools={settings.availableTools} enabledTools={settings.enabledTools} onToggleTool={settings.handleToggleTool} />
                            <SettingsPanel models={settings.availableModels} selectedModels={settings.selectedModels} onModelChange={settings.handleModelChange} />
                        </div>
                    ) : (
                        <div class="flex flex-col flex-grow p-6 pt-4 min-h-0">
                           <div class="flex-grow overflow-y-auto pr-2">
                                <p class="text-gray-400 text-sm">Manage and view custom tools here.</p>
                           </div>
                           <SettingsPanel models={settings.availableModels} selectedModels={settings.selectedModels} onModelChange={settings.handleModelChange} />
                        </div>
                    )}
                </div>
            )}
            
            {activeView === 'tasks' ? (
                <>
                    <div class="flex-1 flex flex-col h-full bg-gray-800/50 rounded-lg border border-gray-700/50 shadow-2xl min-w-0">
                        <div class="flex items-center justify-between p-6 border-b border-gray-700 flex-shrink-0">
                           <h1 class="text-2xl font-bold text-white">ResearchAgent</h1>
                           <div class="flex items-center gap-2">
                               <span class="relative flex h-3 w-3"> {agent.connectionStatus === 'Connected' && <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>} <span class={`relative inline-flex rounded-full h-3 w-3 ${agent.connectionStatus === 'Connected' ? 'bg-green-500' : 'bg-red-500'}`}></span> </span>
                               <span class="text-sm text-gray-400">{agent.connectionStatus}</span>
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
                                                                        availableTools={settings.availableTools}
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

                           {agent.runningTasks[activeTaskId] && !isAwaitingApproval && ( <div class="flex items-center gap-4 p-4"> <LoaderIcon class="h-5 w-5 text-yellow-400" /> <p class="text-gray-300 font-medium">Agent is running...</p> </div> )}
                           <div ref={messagesEndRef} />
                        </div>
                        <div class="p-6 border-t border-gray-700 flex-shrink-0">
                            <form onSubmit={handleSendMessage} class="flex gap-3">
                                <textarea value={inputValue} onInput={e => setInputValue(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) handleSendMessage(e); }} class="flex-1 p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:outline-none resize-none" placeholder={activeTaskId ? (isAwaitingApproval ? "Approve, modify, or reject the plan above." : (agent.runningTasks[activeTaskId] ? "Agent is running..." : "Send a message...")) : "Please select or create a task."} rows="2" disabled={!activeTaskId || agent.runningTasks[activeTaskId] || isAwaitingApproval} ></textarea>
                                {agent.runningTasks[activeTaskId] && !isAwaitingApproval ? (
                                     <button type="button" onClick={handleStopAgent} class="px-4 py-2 bg-red-600 text-white font-semibold rounded-lg hover:bg-red-700 disabled:bg-gray-500 transition-colors flex items-center gap-2">
                                        <StopCircleIcon class="h-5 w-5"/>
                                        Stop
                                    </button>
                                ) : (
                                    <button type="submit" class="px-6 py-2 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:bg-gray-500 transition-colors" disabled={agent.connectionStatus !== 'Connected' || agent.runningTasks[activeTaskId] || !activeTaskId || isAwaitingApproval}>Send</button>
                                )}
                            </form>
                        </div>
                    </div>

                    {!isRightSidebarVisible && <ToggleButton isVisible={isRightSidebarVisible} onToggle={() => setIsRightSidebarVisible(true)} side="right" />}
                    {isRightSidebarVisible && (
                        <div class="h-full w-1/4 min-w-[300px] bg-gray-800/50 rounded-lg border border-gray-700/50 shadow-2xl flex flex-col relative"
                            onDragEnter={workspace.handleDragEnter} onDragLeave={workspace.handleDragLeave} onDragOver={workspace.handleDragOver} onDrop={workspace.handleDrop} >
                            <div class="flex justify-between items-center p-6 pb-4 border-b border-gray-700"> <h2 class="text-xl font-bold text-white">Agent Workspace</h2> <button onClick={() => setIsRightSidebarVisible(false)} class="p-1.5 rounded-md hover:bg-gray-700" title="Hide Workspace"><ChevronsRightIcon class="h-4 w-4" /></button> </div>
                            <div class="flex flex-col flex-grow min-h-0 px-6 pb-6 pt-4">
                                {workspace.selectedFile ? (
                                    <div class="flex flex-col h-full">
                                        <div class="flex items-center justify-between gap-2 pb-2 mb-2 border-b border-gray-700 flex-shrink-0">
                                            <div class="flex items-center gap-2 min-w-0"> <button onClick={() => workspace.setSelectedFile(null)} class="p-1.5 rounded-md hover:bg-gray-700 flex-shrink-0"><ArrowLeftIcon class="h-4 w-4" /></button> <span class="font-mono text-sm text-white truncate">{workspace.selectedFile.name}</span> </div>
                                            <CopyButton textToCopy={workspace.fileContent} />
                                        </div>
                                        <div class="flex-grow bg-gray-900/50 rounded-md overflow-auto flex items-center justify-center">
                                            <FilePreviewer file={workspace.selectedFile} isLoading={workspace.isFileLoading} content={workspace.fileContent} rawFileUrl={`http://localhost:8766/api/workspace/raw?path=${workspace.currentPath}/${workspace.selectedFile.name}`} />
                                        </div>
                                    </div>
                                ) : (
                                     <div class="flex flex-col flex-grow min-h-0">
                                         <div class="flex justify-between items-center mb-2 flex-shrink-0">
                                            <Breadcrumbs path={workspace.currentPath} onNavigate={workspace.handleBreadcrumbNav} />
                                            <div class="flex items-center">
                                                <button onClick={workspace.createFolder} disabled={!workspace.currentPath || workspace.loading} class="p-1.5 rounded-md hover:bg-gray-700 disabled:opacity-50" title="New Folder"> <PlusCircleIcon class="h-4 w-4" /> </button>
                                                <input type="file" ref={workspace.fileInputRef} onChange={(e) => workspace.uploadFile(e.target.files[0])} class="hidden" />
                                                <button onClick={() => workspace.fileInputRef.current?.click()} disabled={!workspace.currentPath || workspace.loading} class="p-1.5 rounded-md hover:bg-gray-700 disabled:opacity-50" title="Upload File"> <UploadCloudIcon class="h-4 w-4" /> </button>
                                            </div>
                                         </div>
                                         <div class="flex-grow bg-gray-900/50 rounded-md p-4 text-sm text-gray-400 font-mono overflow-y-auto">
                                            {workspace.loading ? <div class="flex items-center gap-2"><LoaderIcon class="h-4 w-4"/><span>Loading...</span></div> : 
                                             workspace.error ? <p class="text-red-400">Error: {workspace.error}</p> : 
                                             workspace.items.length === 0 ? <p>// Directory is empty.</p> : ( 
                                             <ul> 
                                                {workspace.items.map(item => ( 
                                                    <li key={item.name} class="group flex justify-between items-center mb-1 hover:bg-gray-700/50 rounded-md -ml-2 -mr-2 pr-2">
                                                        <div onClick={() => workspace.handleNavigation(item)} title={item.name} class="flex items-center gap-2 cursor-pointer truncate flex-grow p-2"> 
                                                            {item.type === 'directory' ? <FolderIcon class="h-4 w-4 text-blue-400 flex-shrink-0" /> : <FileIcon class="h-4 w-4 text-gray-500 flex-shrink-0" />}
                                                            <span>{item.name}</span>
                                                        </div>
                                                        <div class="flex items-center opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                                                            <button onClick={(e) => { e.stopPropagation(); workspace.renameItem(item); }} class="p-1 text-gray-500 hover:text-white" title={`Rename ${item.type}`}> <PencilIcon class="h-4 w-4" /> </button>
                                                            <button onClick={(e) => { e.stopPropagation(); workspace.deleteItem(item); }} class="p-1 text-gray-500 hover:text-red-400" title={`Delete ${item.type}`}> <Trash2Icon class="h-4 w-4" /> </button>
                                                        </div>
                                                    </li> 
                                                ))} 
                                             </ul> 
                                            )}
                                         </div>
                                     </div>
                                )}
                            </div>
                            {workspace.isDragOver && (
                                <div class="absolute inset-0 bg-blue-500/20 border-2 border-dashed border-blue-400 rounded-lg flex items-center justify-center pointer-events-none">
                                    <div class="text-center"> <UploadCloudIcon class="h-10 w-10 text-blue-300 mx-auto" /> <p class="mt-2 font-semibold text-white">Drop files to upload</p> </div>
                                </div>
                            )}
                        </div>
                    )}
                </>
            ) : (
                <div class="flex-1 flex flex-col h-full bg-gray-800/50 rounded-lg border border-gray-700/50 shadow-2xl min-w-0">
                    <ToolForge />
                </div>
            )}
        </div>
    );
}
