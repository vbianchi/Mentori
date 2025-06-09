import { h } from 'preact';
import { useState, useEffect, useRef, useCallback } from 'preact/hooks';

// --- SVG Icons ---
const ChevronsLeftIcon = (props) => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}>
        <path d="m11 17-5-5 5-5" /><path d="m18 17-5-5 5-5" />
    </svg>
);

const ChevronsRightIcon = (props) => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}>
        <path d="m6 17 5-5-5-5" /><path d="m13 17 5-5-5-5" />
    </svg>
);

const FileIcon = (props) => (
     <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}>
        <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
        <polyline points="14 2 14 8 20 8" />
    </svg>
);

const ArrowLeftIcon = (props) => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}>
        <path d="m12 19-7-7 7-7"/><path d="M19 12H5"/>
    </svg>
);

const UploadCloudIcon = (props) => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}>
        <path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="M12 12v9"/><path d="m16 16-4-4-4 4"/>
    </svg>
);

const ClipboardIcon = (props) => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}>
        <rect width="8" height="4" x="8" y="2" rx="1" ry="1" />
        <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
    </svg>
);

const ClipboardCheckIcon = (props) => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {...props}>
        <rect width="8" height="4" x="8" y="2" rx="1" ry="1" />
        <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
        <path d="m9 14 2 2 4-4" />
    </svg>
);


// --- UI Components ---
const CopyButton = ({ textToCopy }) => {
    const [copied, setCopied] = useState(false);
    const handleCopy = () => {
        const textArea = document.createElement("textarea");
        textArea.value = textToCopy;
        textArea.style.position = "fixed";
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {
            document.execCommand('copy');
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy text: ', err);
        }
        document.body.removeChild(textArea);
    };

    return (
        <button onClick={handleCopy} class="absolute top-2 right-2 p-1.5 bg-gray-800/70 rounded-md hover:bg-gray-700">
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

const EventCard = ({ event }) => {
    let title = "Unknown Event", color = "bg-gray-700/50", content, isCopyable = false, textToCopy = '';
    try {
        if (event.type === 'user_prompt') {
            title = 'You'; color = 'bg-blue-900/50'; content = <p class="text-white whitespace-pre-wrap">{event.data}</p>;
        } else if (event.type === 'agent_event') {
            title = `${event.name} (${event.event.replace('on_chain_', '')})`;
            color = event.event.includes('start') ? 'bg-yellow-900/40' : 'bg-green-900/40';
            textToCopy = JSON.stringify(event.data, null, 2); isCopyable = true;
            content = <pre class="text-xs text-green-300 overflow-x-auto p-2 bg-black/20 rounded-md"><code>{textToCopy}</code></pre>;
        } else if (event.type === 'error') {
            title = 'Error'; color = 'bg-red-900/60'; textToCopy = event.data; isCopyable = true;
            content = <p class="text-red-300 font-mono">{textToCopy}</p>;
        } else {
             title = event.type || "Raw Message"; textToCopy = typeof event.data === 'object' ? JSON.stringify(event.data, null, 2) : event.data; isCopyable = true;
             content = <pre class="text-xs text-gray-400"><code>{textToCopy}</code></pre>;
        }
    } catch (e) {
        title = "Rendering Error"; color = "bg-red-900/60"; content = <p class="text-red-300">Could not display event: {e.message}</p>;
    }
    return (
        <div class={`relative p-4 rounded-lg shadow-md ${color} border border-gray-700/50 mb-4`}>
            {isCopyable && <CopyButton textToCopy={textToCopy} />}
            <h3 class="font-bold text-sm text-gray-300 mb-2 capitalize">{title}</h3>
            {content}
        </div>
    );
};

// --- Main App Component ---
export function App() {
    const [events, setEvents] = useState([]);
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

    const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: "auto" });

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

    const handleFileUpload = async (e) => {
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
    };

    useEffect(() => {
        function connect() {
            setConnectionStatus("Connecting...");
            ws.current = new WebSocket("ws://localhost:8765");
            ws.current.onopen = () => setConnectionStatus("Connected");
            ws.current.onclose = () => { setConnectionStatus("Disconnected"); setTimeout(connect, 3000); };
            ws.current.onerror = () => ws.current.close();
            ws.current.onmessage = (event) => {
                try { setEvents(prev => [...prev, JSON.parse(event.data)]); } catch (error) { setEvents(prev => [...prev, { type: "raw", data: event.data }]); }
            };
        }
        connect();
        return () => { if (ws.current) { ws.current.onclose = null; ws.current.close(); }};
    }, []);

    useEffect(() => {
        scrollToBottom();
        const lastEvent = events[events.length - 1];
        if (lastEvent?.name === 'prepare_inputs' && lastEvent.event === 'on_chain_end') {
            const newPath = lastEvent.data?.output?.workspace_path;
            if (newPath && newPath !== workspacePath) {
                setWorkspacePath(newPath);
                setSelectedFile(null);
                fetchWorkspaceFiles(newPath);
            }
        } else if (lastEvent?.name === 'executor_node' && lastEvent.event === 'on_chain_end') {
            if (!lastEvent.data?.output?.tool_output?.toLowerCase().includes("error") && workspacePath) {
                setTimeout(() => fetchWorkspaceFiles(workspacePath), 100);
            }
        }
    }, [events, workspacePath, fetchWorkspaceFiles]);

    const handleSendMessage = (e) => {
        e.preventDefault();
        const message = inputValue.trim();
        if (message && ws.current?.readyState === WebSocket.OPEN) {
            setEvents(prev => [...prev, { type: 'user_prompt', data: message }]);
            setWorkspacePath(null); setWorkspaceFiles([]); setWorkspaceError(null); setSelectedFile(null);
            ws.current.send(message);
            setInputValue("");
        }
    };
    
    return (
        <div class="flex h-screen w-screen p-4 gap-4">
            
            <ToggleButton isVisible={isLeftSidebarVisible} onToggle={() => setIsLeftSidebarVisible(true)} side="left" />
            
            {isLeftSidebarVisible && (
                <div class="h-full w-1/4 min-w-[300px] bg-gray-800/50 rounded-lg border border-gray-700/50 shadow-2xl flex flex-col transition-all duration-300 ease-in-out">
                    <div class="flex justify-between items-center p-6 pb-4 border-b border-gray-700 flex-shrink-0">
                        <h2 class="text-xl font-bold text-white">Tasks</h2>
                        <button onClick={() => setIsLeftSidebarVisible(false)} class="p-1.5 rounded-md hover:bg-gray-700" title="Hide Sidebar">
                            <ChevronsLeftIcon class="h-4 w-4" />
                        </button>
                    </div>
                    <div class="flex-1 text-gray-400 p-6 pt-4 min-h-0">
                        <p>// Task list will go here.</p>
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
                   {events.map((event, index) => <EventCard key={index} event={event} />)}
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

            <ToggleButton isVisible={isRightSidebarVisible} onToggle={() => setIsRightSidebarVisible(true)} side="right" />
            
            {isRightSidebarVisible && (
                <div class="h-full w-1/4 min-w-[300px] bg-gray-800/50 rounded-lg border border-gray-700/50 shadow-2xl flex flex-col transition-all duration-300 ease-in-out">
                    <div class="flex justify-between items-center p-6 pb-4 border-b border-gray-700">
                        <h2 class="text-xl font-bold text-white">Agent Workspace</h2>
                         <button onClick={() => setIsRightSidebarVisible(false)} class="p-1.5 rounded-md hover:bg-gray-700" title="Hide Workspace">
                            <ChevronsRightIcon class="h-4 w-4" />
                        </button>
                    </div>
                    <div class="flex flex-col flex-grow min-h-0 px-6 pb-6 pt-4">
                        {selectedFile ? (
                            <div class="flex flex-col h-full">
                                <div class="relative flex items-center justify-between gap-2 pb-2 mb-2 border-b border-gray-700 flex-shrink-0">
                                    <div class="flex items-center gap-2 min-w-0">
                                        <button onClick={() => setSelectedFile(null)} class="p-1 rounded-md hover:bg-gray-700 flex-shrink-0"><ArrowLeftIcon class="h-4 w-4" /></button>
                                        <span class="font-mono text-sm text-white truncate">{selectedFile}</span>
                                    </div>
                                    <CopyButton textToCopy={fileContent} />
                                </div>
                                <div class="flex-grow bg-gray-900/50 rounded-md overflow-hidden">
                                    <pre class="h-full w-full overflow-auto p-4 text-sm text-gray-300 font-mono whitespace-pre-wrap break-words">
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

