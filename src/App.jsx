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


// --- Main App Component ---
export function App() {
    const [events, setEvents] = useState([]);
    const [inputValue, setInputValue] = useState("");
    const [connectionStatus, setConnectionStatus] = useState("Disconnected");
    const ws = useRef(null);
    const scrollRef = useRef(null);

    // Effect to manage WebSocket connection
    useEffect(() => {
        if (ws.current) return; // Prevent multiple connections

        setConnectionStatus("Connecting...");
        ws.current = new WebSocket("ws://localhost:8765");

        ws.current.onopen = () => setConnectionStatus("Connected");
        ws.current.onclose = () => setConnectionStatus("Disconnected");
        ws.current.onerror = (err) => {
            console.error("WebSocket error:", err);
            setConnectionStatus("Error");
        };

        ws.current.onmessage = (event) => {
            try {
                const newEvent = JSON.parse(event.data);
                setEvents(prev => [...prev, newEvent]);
            } catch (error) {
                setEvents(prev => [...prev, { type: "raw", data: event.data }]);
            }
        };

        // Cleanup on component unmount
        return () => ws.current.close();
    }, []);

    // Effect to scroll to bottom on new event
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [events]);

    const handleSendMessage = (e) => {
        e.preventDefault();
        const message = inputValue.trim();
        if (message && ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(message);
            setEvents(prev => [...prev, { type: 'user_prompt', data: message }]);
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
                    <textarea
                        value={inputValue}
                        onInput={e => setInputValue(e.target.value)}
                        onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) handleSendMessage(e); }}
                        class="flex-1 p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:outline-none resize-none"
                        placeholder="Send a message to the agent..."
                        rows="2"
                    ></textarea>
                    <button type="submit" class="px-6 py-2 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:bg-gray-500 transition-colors" disabled={connectionStatus !== 'Connected'}>
                        Send
                    </button>
                </form>
            </div>
            <div class="w-1/3 h-full bg-gray-800/50 rounded-lg border border-gray-700/50 p-6 shadow-2xl flex flex-col">
                <h2 class="text-xl font-bold text-white mb-4 border-b border-gray-700 pb-4">Agent Workspace</h2>
                <div class="flex-1 bg-gray-900/50 rounded-md p-4 text-sm text-gray-400 font-mono">
                    <p>// The agent's file system will be displayed here.</p>
                </div>
            </div>
        </div>
    );
}
