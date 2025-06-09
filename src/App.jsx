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
const ZapIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg> );
const LoaderIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="animate-spin" {...props}><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg> );
const CircleDotIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="1"/></svg> );
const ChevronDownIcon = (props) => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}><path d="m6 9 6 6 6-6"/></svg> );


// --- UI Components ---
const CopyButton = ({ textToCopy, className = '' }) => {
    const [copied, setCopied] = useState(false);
    const handleCopy = (e) => {
        e.stopPropagation(); // Prevent card from collapsing when copy is clicked
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
            case 'pending':
            default:
                return <CircleDotIcon class="h-5 w-5 text-gray-500" />;
        }
    };

    return (
        <div class="bg-gray-800/50 rounded-lg border border-gray-700/50 mb-4 transition-all">
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

// --- Main App Component ---
export function App() {
    const [prompt, setPrompt] = useState("");
    const [planSteps, setPlanSteps] = useState([]);
    const [isThinking, setIsThinking] = useState(false);
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
            setWorkspaceFiles((await response.json()).files || []);
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
        function connect() {
            setConnectionStatus("Connecting...");
            ws.current = new WebSocket("ws://localhost:8765");
            ws.current.onopen = () => setConnectionStatus("Connected");
            ws.current.onclose = () => { setConnectionStatus("Disconnected"); setTimeout(connect, 3000); };
            ws.current.onerror = () => ws.current.close();
            ws.current.onmessage = (event) => {
                const newEvent = JSON.parse(event.data);

                setPlanSteps(prevSteps => {
                    const data = newEvent.data?.output || {};
                    const inputData = newEvent.data?.input || {};
                    
                    if (newEvent.name === 'structured_planner_node' && newEvent.event.includes('end')) {
                        setIsThinking(false);
                        const plan = data.plan || [];
                        return plan.map(step => ({ ...step, status: 'pending' }));
                    }

                    if (newEvent.name === 'controller_node' && newEvent.event.includes('start')) {
                        const stepIndex = inputData.current_step_index;
                        if (prevSteps[stepIndex]) {
                            const newSteps = [...prevSteps];
                            newSteps[stepIndex] = { ...newSteps[stepIndex], status: 'in-progress' };
                            return newSteps;
                        }
                    }

                    if (newEvent.name === 'executor_node' && newEvent.event.includes('end')) {
                        const stepIndex = inputData.current_step_index;
                         if (prevSteps[stepIndex]) {
                            const newSteps = [...prevSteps];
                            newSteps[stepIndex] = { 
                                ...newSteps[stepIndex], 
                                status: 'completed',
                                toolCall: inputData.current_tool_call,
                                toolOutput: data.tool_output,
                            };
                            return newSteps;
                        }
                    }
                    
                    return prevSteps;
                });
            };
        }
        connect();
        return () => { if (ws.current) { ws.current.onclose = null; ws.current.close(); }};
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [planSteps]);

    useEffect(() => {
        const lastStep = planSteps[planSteps.length - 1];
        if (lastStep && lastStep.status === 'completed' && workspacePath) {
             setTimeout(() => fetchWorkspaceFiles(workspacePath), 100);
        }
    }, [planSteps, workspacePath, fetchWorkspaceFiles]);


    const handleSendMessage = (e) => {
        e.preventDefault();
        const message = inputValue.trim();
        if (message && ws.current?.readyState === WebSocket.OPEN) {
            setPrompt(message);
            setPlanSteps([]);
            setIsThinking(true);
            setWorkspacePath(null); setWorkspaceFiles([]); setWorkspaceError(null); setSelectedFile(null);
            ws.current.send(message);
            setInputValue("");
        }
    };
    
    return (
        <div class="flex h-screen w-screen p-4 gap-4">
            {!isLeftSidebarVisible && <ToggleButton onToggle={() => setIsLeftSidebarVisible(true)} side="left" />}
            {isLeftSidebarVisible && (
                <div class="h-full w-1/4 min-w-[300px] bg-gray-800/50 rounded-lg border border-gray-700/50 shadow-2xl flex flex-col">
                    <div class="flex justify-between items-center p-6 pb-4 border-b border-gray-700 flex-shrink-0">
                        <h2 class="text-xl font-bold text-white">Tasks</h2>
                        <button onClick={() => setIsLeftSidebarVisible(false)} class="p-1.5 rounded-md hover:bg-gray-700" title="Hide Sidebar"><ChevronsLeftIcon class="h-4 w-4" /></button>
                    </div>
                    <div class="flex-1 text-gray-400 p-6 pt-4 min-h-0"><p>// Task list will go here.</p></div>
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
                    <div class="mt-4">
                        {planSteps.map((step, index) => <StepCard key={index} step={step} />)}
                    </div>
                   <div ref={messagesEndRef} />
                </div>
                <div class="p-6 border-t border-gray-700 flex-shrink-0">
                    <form onSubmit={handleSendMessage} class="flex gap-3">
                        <textarea value={inputValue} onInput={e => setInputValue(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) handleSendMessage(e); }}
                            class="flex-1 p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:outline-none resize-none"
                            placeholder="Send a message to the agent..." rows="2"
                        ></textarea>
                        <button type="submit" class="px-6 py-2 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:bg-gray-500 transition-colors" disabled={connectionStatus !== 'Connected'}>Send</button>
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
