import { h } from 'preact';
import { useState, useEffect, useRef, useCallback } from 'preact/hooks';
import { ArchitectIcon, ChevronsLeftIcon, ChevronsRightIcon, ChevronDownIcon, EditorIcon, ForemanIcon, LoaderIcon, PencilIcon, PlusCircleIcon, RouterIcon, SlidersIcon, SupervisorIcon, Trash2Icon, UserIcon, WorkerIcon, FileIcon, FolderIcon, ArrowLeftIcon, UploadCloudIcon, StopCircleIcon, BriefcaseIcon, SendToChatIcon, FileTextIcon } from './components/Icons';
import { ArchitectCard, DirectAnswerCard, FinalAnswerCard, SiteForemanCard } from './components/AgentCards';
import { ToggleButton, CopyButton } from './components/Common';
import { useTasks } from './hooks/useTasks';
import { useWorkspace } from './hooks/useWorkspace';
import { useSettings } from './hooks/useSettings';
import { useAgent } from './hooks/useAgent';

// --- Re-styled & Improved Components ---

const InlineEditor = ({ item, onConfirm, onCancel }) => {
    const [name, setName] = useState(item.name || '');
    const inputRef = useRef(null);

    useEffect(() => {
        inputRef.current?.focus();
        inputRef.current?.select();
    }, []);

    const handleConfirm = () => {
        onConfirm(item.name, name, item.type, item.isNew);
    };
    
    const handleKeyDown = (e) => {
        if (e.key === 'Enter') handleConfirm();
        else if (e.key === 'Escape') onCancel(item.name, item.type, item.isNew);
    };

    return (
        <li class="group flex justify-between items-center mb-1 bg-blue-900/30 rounded-md -ml-2 -mr-2 pr-2">
            <div class="flex items-center gap-2 flex-grow p-2">
                {item.type === 'folder' ? <FolderIcon class="h-4 w-4 text-blue-400 flex-shrink-0" /> : <FileIcon class="h-4 w-4 text-gray-500 flex-shrink-0" />}
                <input
                    ref={inputRef}
                    type="text"
                    value={name}
                    onInput={(e) => setName(e.target.value)}
                    onBlur={handleConfirm}
                    onKeyDown={handleKeyDown}
                    class="w-full bg-transparent text-foreground outline-none text-sm"
                />
            </div>
        </li>
    );
};


const FilePreviewer = ({ currentPath, file, isLoading, content, rawFileUrl }) => {
    if (isLoading) {
        return <div class="flex items-center justify-center h-full"><LoaderIcon class="h-8 w-8 text-primary" /></div>;
    }
    if (!file) {
        return <div class="flex items-center justify-center h-full text-muted-foreground">Select a file to preview</div>;
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
        if (rows.length === 0) return <p class="text-muted-foreground">Empty {extension.toUpperCase()} file.</p>;
        
        const header = rows[0];
        const body = rows.slice(1);

        return (
             <div class="overflow-auto h-full">
                <table class="w-full text-left text-sm text-foreground">
                    <thead class="bg-secondary/50 sticky top-0">
                        <tr>
                            {header.map((col, i) => <th key={i} class="p-2 border-b border-border font-semibold">{col}</th>)}
                        </tr>
                    </thead>
                    <tbody>
                        {body.map((row, i) => (
                            <tr key={i} class="border-b border-input last:border-b-0 hover:bg-secondary/20">
                                {row.map((cell, j) => <td key={j} class="p-2 truncate" title={cell}>{cell}</td>)}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        );
    }
    
    return (
        <pre class="h-full w-full text-sm text-muted-foreground font-mono">
            <code>{content}</code>
        </pre>
    );
};

const PromptCard = ({ content }) => (
    <div class="mt-8 p-4 rounded-lg shadow-md bg-blue-900/30 border border-blue-800/50">
        <h3 class="font-bold text-sm text-foreground mb-2 capitalize flex items-center gap-2"><UserIcon class="h-5 w-5" /> You</h3>
        <p class="text-foreground/90 whitespace-pre-wrap font-medium">{content}</p>
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
        <div onClick={() => onSelect(task.id)} class={`group flex justify-between items-center p-3 mb-2 rounded-lg cursor-pointer transition-colors ${isActive ? 'bg-primary/20 border-primary/50' : 'hover:bg-secondary/50 border-transparent'} border`}>
            <div class="flex items-center gap-2 truncate">
                {isRunning && <LoaderIcon class="h-4 w-4 text-primary flex-shrink-0" />}
                {isEditing ? ( <input ref={inputRef} type="text" value={editText} onInput={(e) => setEditText(e.target.value)} onBlur={handleSave} onKeyDown={handleKeyDown} onClick={(e) => e.stopPropagation()} class="w-full bg-transparent text-foreground outline-none"/> ) : ( <p class="font-medium text-foreground truncate">{task.name}</p> )}
            </div>
            {!isEditing && ( <div class="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity"> <button onClick={handleStartEditing} class="p-1 hover:text-foreground" title="Rename Task"><PencilIcon class="h-4 w-4" /></button> <button onClick={(e) => { e.stopPropagation(); onDelete(task.id); }} class="p-1 hover:text-red-400" title="Delete Task"><Trash2Icon class="h-4 w-4" /></button> </div> )}
        </div>
    );
};

const ModelSelectorRow = ({ label, icon, onModelChange, models, selectedModel, roleKey, description }) => (
    <div class="flex items-center justify-between py-3 border-b border-border/50">
        <div class="flex items-center gap-3">
            {icon}
            <div>
                <p class="font-semibold text-sm text-foreground">{label}</p>
                <p class="text-xs text-muted-foreground">{description}</p>
            </div>
        </div>
        <div class="relative w-48">
             <select value={selectedModel} onChange={(e) => onModelChange(roleKey, e.target.value)} class="w-full p-2 bg-secondary border border-border rounded-md text-foreground focus:ring-2 focus:ring-primary focus:outline-none appearance-none text-sm" disabled={!selectedModel || models.length === 0}>
                {models.map(model => <option key={model.id} value={model.id}>{model.name}</option>)}
            </select>
            <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-muted-foreground">
                <ChevronDownIcon class="h-4 w-4" />
            </div>
        </div>
    </div>
);

const ToolToggleRow = ({ tool, isEnabled, onToggle }) => (
     <div class="flex items-start justify-between py-3 border-b border-border/50">
        <div class="flex-1 min-w-0 pr-4">
            <p class="font-semibold text-sm text-foreground">{tool.name}</p>
            <p class="text-xs text-muted-foreground whitespace-normal break-words">{tool.description}</p>
        </div>
        <label class="relative inline-flex items-center cursor-pointer mt-1">
            <input type="checkbox" checked={isEnabled} onChange={onToggle} class="sr-only peer" />
            <div class="w-9 h-5 bg-input rounded-full peer peer-focus:ring-2 peer-focus:ring-primary peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary"></div>
        </label>
    </div>
);

const SettingsSection = ({ title, icon, children }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    return (
        <div class="border-t border-border pt-4 mt-4">
            <div class="flex items-center justify-between cursor-pointer" onClick={() => setIsExpanded(!isExpanded)}>
                <div class="flex items-center gap-3">
                    {icon}
                    <h3 class="text-lg font-semibold text-foreground">{title}</h3>
                </div>
                <ChevronDownIcon class={`h-5 w-5 text-muted-foreground transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
            </div>
            {isExpanded && <div class="mt-2 pl-1">{children}</div>}
        </div>
    );
};

const Breadcrumbs = ({ path, onNavigate }) => {
    const parts = path.split('/').filter(Boolean);
    const handleCrumbClick = (index) => onNavigate(parts.slice(0, index + 1).join('/'));
    return (
        <div class="flex items-center gap-1.5 text-sm text-muted-foreground truncate mb-2 flex-shrink-0">
            <span onClick={() => onNavigate(parts[0])} class="hover:text-foreground cursor-pointer">Workspace</span>
            {parts.slice(1).map((part, index) => (
                <div key={index} class="flex items-center gap-1.5">
                    <span>/</span>
                    <span onClick={() => handleCrumbClick(index + 1)} class="hover:text-foreground cursor-pointer">{part}</span>
                </div>
            ))}
        </div>
    );
};


export function App() {
    const { tasks, setTasks, activeTaskId, selectTask: setActiveTaskId, renameTask } = useTasks();
    const workspace = useWorkspace(activeTaskId);
    const settings = useSettings();
    const agent = useAgent(useCallback((event) => {
        setTasks(currentTasks => {
            try {
                const taskIndex = currentTasks.findIndex(t => t.id === event.task_id);
                if (taskIndex === -1) return currentTasks;
                
                const newTasks = [...currentTasks];
                const taskToUpdate = { ...newTasks[taskIndex] };
                let newHistory = [...taskToUpdate.history];

                let runContainer = newHistory.length > 0 && newHistory[newHistory.length - 1].type === 'run_container' ? newHistory[newHistory.length - 1] : null;
                if (!runContainer && !['agent_started', 'agent_stopped', 'agent_resumed'].includes(event.type)) {
                    runContainer = { type: 'run_container', children: [], isComplete: false };
                    newHistory.push(runContainer);
                }
                
                const eventType = event.type;
                if (eventType === 'plan_approval_request') {
                    setIsAwaitingApproval(true);
                    runContainer.children.push({ type: 'architect_plan', steps: event.plan, isAwaitingApproval: true });
                } else if (eventType === 'direct_answer' || eventType === 'final_answer') {
                    setIsAwaitingApproval(false);
                    runContainer.children.push({ type: eventType, content: event.data });
                    runContainer.isComplete = true;
                } else if (eventType === 'agent_event') {
                    const { name, event: chainEvent, data } = event;
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
                            if (name === 'Site_Foreman' && chainEvent === 'on_chain_start') stepToUpdate.status = 'in-progress';
                            else if (name === 'Project_Supervisor' && chainEvent === 'on_chain_end') {
                                stepToUpdate.status = outputData.step_evaluation?.status === 'failure' ? 'failure' : 'completed';
                                stepToUpdate.toolCall = inputData.current_tool_call;
                                stepToUpdate.toolOutput = outputData.tool_output;
                                stepToUpdate.evaluation = outputData.step_evaluation;
                                if (activeTaskId === event.task_id) workspace.fetchFiles(workspace.currentPath);
                            }
                            executionPlan.steps[stepIndex] = stepToUpdate;
                        }
                    }
                }
                taskToUpdate.history = newHistory;
                newTasks[taskIndex] = taskToUpdate;
                return newTasks;
            } catch (error) {
                console.error("Error processing WebSocket message:", error, "Event:", event);
                return currentTasks;
            }
        });
        if (event.type === 'final_answer' && event.refresh_workspace && activeTaskId === event.task_id) {
            workspace.fetchFiles(workspace.currentPath);
        }
    }, [activeTaskId, workspace.currentPath]));

    const [inputValue, setInputValue] = useState("");
    const [isLeftSidebarVisible, setIsLeftSidebarVisible] = useState(true);
    const [isRightSidebarVisible, setIsRightSidebarVisible] = useState(true);
    const [isAwaitingApproval, setIsAwaitingApproval] = useState(false);
    
    const messagesEndRef = useRef(null);
    const promptInputRef = useRef(null);
    const agentRoles = [
        { key: 'ROUTER_LLM_ID', label: 'The Router', icon: <RouterIcon className="h-5 w-5 text-muted-foreground"/>, description: "Classifies tasks into 3 tracks." },
        { key: 'CHIEF_ARCHITECT_LLM_ID', label: 'The Chief Architect', icon: <ArchitectIcon className="h-5 w-5 text-muted-foreground"/>, description: "Creates complex, multi-step plans." },
        { key: 'SITE_FOREMAN_LLM_ID', label: 'The Site Foreman', icon: <ForemanIcon className="h-5 w-5 text-muted-foreground"/>, description: "Prepares tool calls for plans." },
        { key: 'PROJECT_SUPERVISOR_LLM_ID', label: 'The Project Supervisor', icon: <SupervisorIcon className="h-5 w-5 text-muted-foreground"/>, description: "Validates complex step outcomes." },
        { key: 'EDITOR_LLM_ID', label: 'The Editor', icon: <EditorIcon className="h-5 w-5 text-muted-foreground"/>, description: "Answers questions, summarizes." },
    ];

    useEffect(() => { if (activeTaskId) workspace.setCurrentPath(activeTaskId) }, [activeTaskId]);
    useEffect(() => { if (workspace.currentPath) workspace.fetchFiles(workspace.currentPath) }, [workspace.currentPath]);
    useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }) }, [tasks.find(t=>t.id===activeTaskId)?.history, isAwaitingApproval]);

    const selectTask = (taskId) => {
        if (taskId !== activeTaskId) {
            setActiveTaskId(taskId);
            setIsAwaitingApproval(false);
            workspace.resetWorkspaceViews();
        }
    };
    
    const createNewTask = () => {
        const newTaskId = `task_${Date.now()}`;
        agent.createTask(newTaskId);
        setTasks(prevTasks => [...prevTasks, { id: newTaskId, name: `New Task ${tasks.length + 1}`, history: [] }]);
        selectTask(newTaskId);
    };

    const handleDeleteTask = (taskIdToDelete) => {
        agent.deleteTask(taskIdToDelete);
        const currentTasks = tasks;
        const remainingTasks = currentTasks.filter(task => task.id !== taskIdToDelete);
        if (activeTaskId === taskIdToDelete) {
            if (remainingTasks.length > 0) {
                const deletedIndex = currentTasks.findIndex(task => task.id === taskIdToDelete);
                selectTask(remainingTasks[Math.max(0, deletedIndex - 1)].id);
            } else {
                setActiveTaskId(null);
                workspace.resetWorkspaceViews();
                workspace.setCurrentPath('');
            }
        }
        setTasks(remainingTasks);
    };
    
    const handleApprovalAction = (feedback, plan = null) => {
        setIsAwaitingApproval(false);
        agent.resumeAgent({ task_id: activeTaskId, feedback, plan, enabled_tools: Object.keys(settings.enabledTools).filter(key => settings.enabledTools[key]) });
    };

    const handleModifyAndApprove = (modifiedPlan) => {
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
    
    const handleSendMessage = (e) => {
        e.preventDefault();
        const message = inputValue.trim();
        if (!message || !activeTaskId || agent.connectionStatus !== 'Connected' || agent.runningTasks[activeTaskId] || isAwaitingApproval) return;
        setTasks(currentTasks => currentTasks.map(task => task.id === activeTaskId ? { ...task, history: [...task.history, { type: 'prompt', content: message }, { type: 'run_container', children: [], isComplete: false }] } : task));
        agent.runAgent({ prompt: message, llm_config: settings.selectedModels, task_id: activeTaskId, enabled_tools: Object.keys(settings.enabledTools).filter(key => settings.enabledTools[key]) });
        setInputValue("");
    };

    const handleSendToChat = (filename) => {
        setInputValue(prev => `${prev}${prev ? ' ' : ''}'${filename}' `);
        promptInputRef.current?.focus();
    };

    return (
        <div class="flex h-screen w-screen p-2 sm:p-4 gap-4 bg-background text-foreground">
            {/* --- MODIFIED: Wrapper for correct toggle button positioning --- */}
            <div class="absolute top-4 left-4 z-20">
              {!isLeftSidebarVisible && <ToggleButton onToggle={() => setIsLeftSidebarVisible(true)} side="left" />}
            </div>
            <div class="absolute top-4 right-4 z-20">
               {!isRightSidebarVisible && <ToggleButton onToggle={() => setIsRightSidebarVisible(true)} side="right" />}
            </div>
            
            <div class={`h-full bg-card/50 rounded-lg border border-border shadow-2xl flex flex-col transition-all duration-300 ease-in-out ${isLeftSidebarVisible ? 'w-full max-w-xs sm:max-w-sm md:max-w-md lg:max-w-lg' : 'w-0 p-0 border-0'}`} style={{ overflow: isLeftSidebarVisible ? 'visible' : 'hidden' }}>
                <div class={`flex justify-between items-center p-4 border-b border-border flex-shrink-0 transition-opacity duration-200 ${isLeftSidebarVisible ? 'opacity-100' : 'opacity-0'}`}>
                    <h2 class="text-xl font-bold text-foreground">Tasks</h2>
                    <div class="flex items-center gap-2">
                        <button onClick={createNewTask} class="p-1.5 rounded-md text-muted-foreground hover:bg-secondary hover:text-foreground" title="New Task"><PlusCircleIcon class="h-5 w-5" /></button>
                        <button onClick={() => setIsLeftSidebarVisible(false)} class="p-1.5 rounded-md text-muted-foreground hover:bg-secondary hover:text-foreground" title="Hide Sidebar"><ChevronsLeftIcon class="h-4 w-4" /></button>
                    </div>
                </div>
                <div class={`flex flex-col flex-grow p-4 min-h-0 transition-opacity duration-200 ${isLeftSidebarVisible ? 'opacity-100' : 'opacity-0'}`}>
                    <div class="flex-shrink-0">
                        {tasks.length > 0 ? ( <ul> {tasks.map(task => ( <TaskItem key={task.id} task={task} isActive={activeTaskId === task.id} isRunning={!!agent.runningTasks[task.id]} onSelect={selectTask} onRename={renameTask} onDelete={handleDeleteTask} /> ))} </ul> ) : ( <p class="text-muted-foreground text-center mt-4">No tasks yet.</p> )}
                    </div>
                    <div class="flex-grow min-h-0 overflow-y-auto mt-2 -mr-4 pr-4">
                        <SettingsSection title="Active Toolbox" icon={<BriefcaseIcon className="h-5 w-5 text-muted-foreground" />}>
                            {settings.availableTools.map(tool => <ToolToggleRow key={tool.name} tool={tool} isEnabled={settings.enabledTools[tool.name] ?? true} onToggle={() => settings.handleToggleTool(tool.name)} />)}
                        </SettingsSection>
                        <SettingsSection title="Agent Models" icon={<SlidersIcon className="h-5 w-5 text-muted-foreground" />}>
                            {agentRoles.map(role => <ModelSelectorRow key={role.key} label={role.label} icon={role.icon} models={settings.availableModels} selectedModel={settings.selectedModels[role.key]} onModelChange={settings.handleModelChange} roleKey={role.key} description={role.description} />)}
                        </SettingsSection>
                    </div>
                </div>
            </div>
            
            <div class="flex-1 flex flex-col h-full bg-card/50 rounded-lg border border-border shadow-2xl min-w-0">
                <div class="flex items-center justify-between p-4 border-b border-border flex-shrink-0">
                   <div>
                       <h1 class="text-2xl font-bold text-foreground">ResearchAgent</h1>
                       <p class="text-xs text-muted-foreground">by Valerio Bianchi & Gemini 2.5 Pro</p>
                   </div>
                   <div class="flex items-center gap-2">
                       <span class="relative flex h-3 w-3"> {agent.connectionStatus === 'Connected' && <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>} <span class={`relative inline-flex rounded-full h-3 w-3 ${agent.connectionStatus === 'Connected' ? 'bg-green-500' : 'bg-red-500'}`}></span> </span>
                       <span class="text-sm text-muted-foreground">{agent.connectionStatus}</span>
                   </div>
                </div>
                <div class="flex-1 overflow-y-auto p-6">
                   {tasks.find(t=>t.id===activeTaskId)?.history.map((item, index) => {
                       if (item.type === 'prompt') return <PromptCard key={index} content={item.content} />;
                       if (item.type === 'run_container') {
                            return (
                                <div key={index} class="relative mt-6 pl-8">
                                    <div class="absolute top-5 left-4 h-[calc(100%-2.5rem)] w-px bg-border" />
                                    <div class="space-y-4">
                                    {item.children.map((child, childIndex) => (
                                        <div key={childIndex} class="relative">
                                            <div class={`absolute top-6 -left-4 h-px ${child.type === 'execution_plan' ? 'w-8' : 'w-4'} bg-border`} />
                                            {(() => {
                                                switch (child.type) {
                                                    case 'architect_plan': return <ArchitectCard plan={child} isAwaitingApproval={child.isAwaitingApproval} onModify={handleModifyAndApprove} onReject={() => handleApprovalAction('reject')} availableTools={settings.availableTools}/>;
                                                    case 'execution_plan': return <SiteForemanCard plan={child} />;
                                                    case 'direct_answer': return <DirectAnswerCard answer={child.content} />;
                                                    case 'final_answer': return <FinalAnswerCard answer={child.content} />;
                                                    default: return null;
                                                }
                                            })()}
                                        </div>
                                    ))}
                                    </div>
                                </div>
                            );
                       }
                       return null;
                   })}
                   {agent.runningTasks[activeTaskId] && !isAwaitingApproval && ( <div class="flex items-center gap-4 p-4"> <LoaderIcon class="h-5 w-5 text-primary" /> <p class="text-muted-foreground font-medium">Agent is running...</p> </div> )}
                   <div ref={messagesEndRef} />
                </div>
                <div class="p-6 border-t border-border flex-shrink-0">
                    <form onSubmit={handleSendMessage} class="flex gap-3">
                        <textarea ref={promptInputRef} value={inputValue} onInput={e => setInputValue(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) handleSendMessage(e); }} class="flex-1 p-3 bg-input border border-border rounded-lg text-foreground focus:ring-2 focus:ring-primary focus:outline-none resize-none" placeholder={activeTaskId ? (isAwaitingApproval ? "Approve, modify, or reject the plan above." : (agent.runningTasks[activeTaskId] ? "Agent is running..." : "Send a message...")) : "Please select or create a task."} rows="2" disabled={!activeTaskId || agent.runningTasks[activeTaskId] || isAwaitingApproval} ></textarea>
                        {agent.runningTasks[activeTaskId] && !isAwaitingApproval ? (
                            <button type="button" onClick={() => agent.stopAgent(activeTaskId)} class="px-4 py-2 bg-red-600 text-white font-semibold rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors flex items-center gap-2"><StopCircleIcon class="h-5 w-5"/>Stop</button>
                        ) : (
                            <button type="submit" class="px-6 py-2 bg-primary text-primary-foreground font-semibold rounded-lg hover:bg-primary/90 disabled:bg-secondary disabled:text-muted-foreground transition-colors" disabled={agent.connectionStatus !== 'Connected' || agent.runningTasks[activeTaskId] || !activeTaskId || isAwaitingApproval}>Send</button>
                        )}
                    </form>
                </div>
            </div>

            <div class={`h-full bg-card/50 rounded-lg border border-border shadow-2xl flex flex-col transition-all duration-300 ease-in-out ${isRightSidebarVisible ? 'w-full max-w-xs sm:max-w-sm md:max-w-md lg:max-w-lg' : 'w-0 p-0 border-0'}`} style={{ overflow: isRightSidebarVisible ? 'visible' : 'hidden' }}>
                <div class={`flex justify-between items-center p-4 border-b border-border transition-opacity duration-200 ${isRightSidebarVisible ? 'opacity-100' : 'opacity-0'}`}> <h2 class="text-xl font-bold text-foreground">Workspace</h2> <button onClick={() => setIsRightSidebarVisible(false)} class="p-1.5 rounded-md text-muted-foreground hover:bg-secondary hover:text-foreground" title="Hide Workspace"><ChevronsRightIcon class="h-4 w-4" /></button> </div>
                <div class={`flex flex-col flex-grow min-h-0 px-4 pb-4 pt-4 transition-opacity duration-200 ${isRightSidebarVisible ? 'opacity-100' : 'opacity-0'}`}>
                    {workspace.selectedFile ? (
                        <div class="flex flex-col h-full">
                            <div class="flex items-center justify-between gap-2 pb-2 mb-2 border-b border-border flex-shrink-0">
                                <div class="flex items-center gap-2 min-w-0"> <button onClick={() => workspace.setSelectedFile(null)} class="p-1.5 rounded-md text-muted-foreground hover:bg-secondary hover:text-foreground flex-shrink-0"><ArrowLeftIcon class="h-4 w-4" /></button> <span class="font-mono text-sm text-foreground truncate">{workspace.selectedFile.name}</span> </div>
                                <CopyButton textToCopy={workspace.fileContent} />
                            </div>
                            <div class="flex-grow bg-background/50 rounded-md overflow-auto flex items-center justify-center">
                                <FilePreviewer file={workspace.selectedFile} isLoading={workspace.isFileLoading} content={workspace.fileContent} rawFileUrl={`http://localhost:8766/api/workspace/raw?path=${workspace.currentPath}/${workspace.selectedFile.name}`} />
                            </div>
                        </div>
                    ) : (
                         <div class="flex flex-col flex-grow min-h-0">
                             <div class="flex justify-between items-center mb-2 flex-shrink-0">
                                <Breadcrumbs path={workspace.currentPath} onNavigate={workspace.handleBreadcrumbNav} />
                                <div class="flex items-center">
                                    <button onClick={() => workspace.startInlineCreate('folder')} disabled={!workspace.currentPath || workspace.loading} class="p-1.5 rounded-md text-muted-foreground hover:bg-secondary hover:text-foreground disabled:opacity-50" title="New Folder"> <FolderIcon class="h-4 w-4" /> </button>
                                    <button onClick={() => workspace.startInlineCreate('file')} disabled={!workspace.currentPath || workspace.loading} class="p-1.5 rounded-md text-muted-foreground hover:bg-secondary hover:text-foreground disabled:opacity-50" title="New File"> <FileTextIcon class="h-4 w-4" /> </button>
                                    <input type="file" ref={workspace.fileInputRef} onChange={(e) => workspace.uploadFiles(e.target.files)} class="hidden" multiple />
                                    <button onClick={() => workspace.fileInputRef.current?.click()} disabled={!workspace.currentPath || workspace.loading} class="p-1.5 rounded-md text-muted-foreground hover:bg-secondary hover:text-foreground disabled:opacity-50" title="Upload File"> <UploadCloudIcon class="h-4 w-4" /> </button>
                                </div>
                             </div>
                             <div class="flex-grow bg-background/50 rounded-md p-2 text-sm text-muted-foreground font-mono overflow-y-auto">
                                {workspace.loading ? <div class="flex items-center gap-2"><LoaderIcon class="h-4 w-4 text-primary"/><span>Loading...</span></div> : 
                                 workspace.error ? <p class="text-red-400">Error: {workspace.error}</p> : 
                                 workspace.items.length === 0 ? <p>// Directory is empty.</p> : ( 
                                 <ul> 
                                    {workspace.items.map(item => {
                                        if (item.isEditing) return <InlineEditor key={item.name} item={item} onConfirm={workspace.handleConfirmName} onCancel={workspace.handleConfirmName} />;
                                        if (item.isLoading) return <li class="flex items-center gap-2 p-2 -ml-2 -mr-2 text-muted-foreground"><LoaderIcon class="h-4 w-4 flex-shrink-0 text-primary"/> <span>Uploading {item.name}...</span></li>;
                                        return (
                                            <li key={item.name} class="group flex justify-between items-center mb-1 hover:bg-secondary/50 rounded-md -ml-2 -mr-2 pr-2">
                                                <div onClick={() => workspace.handleNavigation(item)} title={item.name} class="flex items-center gap-2 cursor-pointer truncate flex-grow p-2"> 
                                                    {item.type === 'directory' ? <FolderIcon class="h-4 w-4 text-primary flex-shrink-0" /> : <FileIcon class="h-4 w-4 text-muted-foreground flex-shrink-0" />}
                                                    <span class="text-foreground">{item.name}</span>
                                                </div>
                                                <div class="flex items-center opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                                                    <button onClick={(e) => { e.stopPropagation(); handleSendToChat(item.name); }} class="p-1 text-muted-foreground hover:text-foreground" title="Send name to chat"> <SendToChatIcon class="h-4 w-4" /> </button>
                                                    <button onClick={(e) => { e.stopPropagation(); workspace.startInlineRename(item); }} class="p-1 text-muted-foreground hover:text-foreground" title={`Rename ${item.type}`}> <PencilIcon class="h-4 w-4" /> </button>
                                                    <button onClick={(e) => { e.stopPropagation(); workspace.deleteItem(item); }} class="p-1 text-muted-foreground hover:text-red-400" title={`Delete ${item.type}`}> <Trash2Icon class="h-4 w-4" /> </button>
                                                </div>
                                            </li> 
                                        );
                                    })} 
                                 </ul> 
                                )}
                             </div>
                         </div>
                    )}
                </div>
                {workspace.isDragOver && (
                    <div class="absolute inset-0 bg-primary/20 border-2 border-dashed border-primary rounded-lg flex items-center justify-center pointer-events-none">
                        <div class="text-center"> <UploadCloudIcon class="h-10 w-10 text-primary/80 mx-auto" /> <p class="mt-2 font-semibold text-foreground">Drop files to upload</p> </div>
                    </div>
                )}
            </div>
        </div>
    );
}
