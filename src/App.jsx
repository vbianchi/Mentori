import { h } from 'preact';
import { useState, useEffect, useRef } from 'preact/hooks';

// --- UI Components ---
const EventCard = ({ event }) => {
    let title = "Unknown Event";
    let color = "bg-gray-700/50";
    let content;

    try {
        if (event.type === 'user_prompt') {
            title = 'You';
            color = 'bg-blue-900/50';
            content = <p class="text-white whitespace-pre-wrap">{event.data}</p>;
        } else if (event.type === 'agent_event') {
            title = `${event.name} (${event.event.replace('on_chain_', '')})`;
            color = event.event.includes('start') ? 'bg-yellow-900/40' : 'bg-green-900/40';
            content = <pre class="text-xs text-green-300 overflow-x-auto p-2 bg-black/20 rounded-md"><code>{JSON.stringify(event.data, null, 2)}</code></pre>;
        } else if (event.type === 'error') {
            title = 'Error';
            color = 'bg-red-900/60';
            content = <p class="text-red-300 font-mono">{event.data}</p>;
        } else {
             title = event.type || "Raw Message";
             content = <pre class="text-xs text-gray-400"><code>{typeof event.data === 'object' ? JSON.stringify(event.data, null, 2) : event.data}</code></pre>;
        }
    } catch (e) {
        title = "Rendering Error";
        color = "bg-red-900/60";
        content = <p class="text-red-300">Could not display event: {e.message}</p>;
    }

    return (
        <div class={`p-4 rounded-lg shadow-md ${color} border border-gray-700/50 mb-4`}>
            <h3 class="font-bold text-sm text-gray-300 mb-2 capitalize">{title}</h3>
            {content}
        </div>
    );
};

const WorkspacePanel = ({ files, workspacePath, isLoading, error, onRefresh }) => {
    return (
        <div class="w-1/3 h-full bg-gray-800/50 rounded-lg border border-gray-700/50 p-6 shadow-2xl flex flex-col">
            <div class="flex justify-between items-center mb-4 border-b border-gray-700 pb-4">
                <h2 class="text-xl font-bold text-white">Agent Workspace</h2>
                <button onClick={onRefresh} class="p-1.5 rounded-md hover:bg-gray-700" title="Refresh Workspace">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                        <path fill-rule="evenodd" d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2z"/>
                        <path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466"/>
                    </svg>
                </button>
            </div>
            <div class="text-xs text-gray-500 mb-2 truncate" title={workspacePath || 'No active workspace'}>
                {workspacePath ? `Path: ...${workspacePath.slice(-36)}` : 'No active workspace'}
            </div>
            <div class="flex-1 bg-gray-900/50 rounded-md p-4 text-sm text-gray-400 font-mono overflow-y-auto">
                {isLoading && <p>Loading files...</p>}
                {error && <p class="text-red-400">Error: {error}</p>}
                {!isLoading && !error && files.length === 0 && <p>// Workspace is empty.</p>}
                {!isLoading && !error && files.length > 0 && (
                    <ul>
                        {files.map(file => (
                            <li key={file} class="flex items-center gap-2 mb-1">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                                {file}
                            </li>
                        ))}
                    </ul>
                )}
            </div>
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

    const ws = useRef(null);
    const scrollRef = useRef(null);

    const fetchWorkspaceFiles = async (path) => {
        if (!path) return;
        setWorkspaceLoading(true);
        setWorkspaceError(null);
        try {
            const justTheId = path.split('/').pop();
            const response = await fetch(`http://localhost:8766/files?path=${justTheId}`);
            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error || `HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            setWorkspaceFiles(data.files || []);
        } catch (error) {
            console.error("Failed to fetch workspace files:", error);
            setWorkspaceError(error.message);
        } finally {
            setWorkspaceLoading(false);
        }
    };

    // Effect to manage WebSocket connection - ONLY RUNS ONCE
    useEffect(() => {
        if (ws.current) return;
        setConnectionStatus("Connecting...");
        ws.current = new WebSocket("ws://localhost:8765");

        ws.current.onopen = () => setConnectionStatus("Connected");
        ws.current.onclose = () => setConnectionStatus("Disconnected");
        ws.current.onerror = (err) => {
            console.error("WebSocket error:", err);
            setConnectionStatus("Error");
        };

        ws.current.onmessage = (event) => {
            let newEvent;
            try {
                newEvent = JSON.parse(event.data);
                setEvents(prev => [...prev, newEvent]);
            } catch (error) {
                setEvents(prev => [...prev, { type: "raw", data: event.data }]);
            }
        };

        return () => ws.current.close();
    }, []); // <-- FIX: Empty dependency array ensures this runs only once

    // Effect to update workspace and scroll event log
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
        
        // Check the last event for workspace updates
        const lastEvent = events[events.length - 1];
        if (lastEvent?.type === 'agent_event' && lastEvent.data?.output?.workspace_path) {
            const newPath = lastEvent.data.output.workspace_path;
            if (newPath !== workspacePath) {
                setWorkspacePath(newPath);
                fetchWorkspaceFiles(newPath);
            }
        }
        // Also re-fetch after a tool runs successfully
        if(lastEvent?.type === 'agent_event' && lastEvent.event === 'on_chain_end' && lastEvent.name === 'executor_node'){
             if(workspacePath && !lastEvent.data.output?.tool_output?.includes("Error")) {
                fetchWorkspaceFiles(workspacePath);
             }
        }

    }, [events]); // This effect now runs whenever the events list changes

    const handleSendMessage = (e) => {
        e.preventDefault();
        const message = inputValue.trim();
        if (message && ws.current?.readyState === WebSocket.OPEN) {
            setEvents([{ type: 'user_prompt', data: message }]);
            setWorkspacePath(null);
            setWorkspaceFiles([]);
            setWorkspaceError(null);
            ws.current.send(message);
            setInputValue("");
        }
    };

    return (
        <div class="flex h-full p-4 gap-4">
            <div class="flex flex-col flex-1 h-full bg-gray-800/50 rounded-lg border border-gray-700/50 p-6 shadow-2xl">
                <div class="flex items-center justify-between mb-4 border-b border-gray-700 pb-4">
                     <h1 class="text-2xl font-bold text-white">ResearchAgent</h1>
                     <div class="flex items-center gap-2">
                        <span class="relative flex h-3 w-3">
                          {connectionStatus === 'Connected' && <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>}
                          <span class={`relative inline-flex rounded-full h-3 w-3 ${connectionStatus === 'Connected' ? 'bg-green-500' : 'bg-red-500'}`}></span>
                        </span>
                        <span class="text-sm text-gray-400">{connectionStatus}</span>
                     </div>
                </div>
                <div ref={scrollRef} class="flex-1 overflow-y-auto pr-2">
                   {events.map((event, index) => <EventCard key={index} event={event} />)}
                </div>
                <form onSubmit={handleSendMessage} class="mt-4 flex gap-3 border-t border-gray-700 pt-4">
                    <textarea value={inputValue} onInput={e => setInputValue(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) handleSendMessage(e); }}
                        class="flex-1 p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:outline-none resize-none"
                        placeholder="Send a message to the agent..." rows="2"
                    ></textarea>
                    <button type="submit" class="px-6 py-2 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:bg-gray-500 transition-colors" disabled={connectionStatus !== 'Connected'}>Send</button>
                </form>
            </div>
            <WorkspacePanel 
                files={workspaceFiles} 
                workspacePath={workspacePath} 
                isLoading={workspaceLoading}
                error={workspaceError}
                onRefresh={() => fetchWorkspaceFiles(workspacePath)}
            />
        </div>
    );
}

