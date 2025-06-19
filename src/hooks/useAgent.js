import { useState, useEffect, useRef } from 'preact/hooks';

/**
 * Custom hook to manage the WebSocket connection and all agent communication.
 * @param {Function} onMessage - A callback function to process incoming messages from the agent.
 */
export const useAgent = (onMessage) => {
    // State for the WebSocket connection and its status
    const ws = useRef(null);
    const [connectionStatus, setConnectionStatus] = useState("Disconnected");
    
    // State to track which tasks have a running agent process
    const [runningTasks, setRunningTasks] = useState({});

    // This effect establishes and manages the WebSocket lifecycle.
    useEffect(() => {
        function connect() {
            setConnectionStatus("Connecting...");
            const socket = new WebSocket("ws://localhost:8765");
            ws.current = socket;

            socket.onopen = () => setConnectionStatus("Connected");

            socket.onclose = () => {
                setConnectionStatus("Disconnected");
                setRunningTasks({}); // Clear running tasks on disconnect
                // Attempt to reconnect after a delay
                setTimeout(connect, 5000);
            };

            socket.onerror = (err) => {
                console.error("WebSocket error:", err);
                socket.close(); // This will trigger the onclose event and reconnection logic
            };

            // Central message handler: receives a message and passes it to the callback from App.jsx
            socket.onmessage = (event) => {
                const newEvent = JSON.parse(event.data);

                // Update the running status based on agent events
                if (newEvent.type === 'agent_started' || newEvent.type === 'agent_resumed') {
                    setRunningTasks(prev => ({ ...prev, [newEvent.task_id]: true }));
                } else if (newEvent.type === 'final_answer' || newEvent.type === 'agent_stopped' || newEvent.type === 'plan_approval_request') {
                    // Stop the spinner on final answer, stop, or when requiring approval
                    setRunningTasks(prev => {
                        const newTasks = { ...prev };
                        delete newTasks[newEvent.task_id];
                        return newTasks;
                    });
                }
                
                // Pass the event up to the main component's logic handler
                if (onMessage) {
                    onMessage(newEvent);
                }
            };
        }

        connect();

        // Cleanup function to close the WebSocket connection when the component unmounts
        return () => {
            if (ws.current) {
                ws.current.onclose = null; // Prevent reconnection attempts on manual close
                ws.current.close();
            }
        };
    }, [onMessage]); // Re-run effect if the onMessage handler changes

    /**
     * Sends a command to the backend to run the agent for a given task.
     * @param {object} payload - The data to send, including task_id, prompt, etc.
     */
    const runAgent = (payload) => {
        if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ type: 'run_agent', ...payload }));
        } else {
            alert("Connection not ready. Please wait a moment and try again.");
        }
    };

    /**
     * Sends a command to the backend to resume a paused agent execution.
     * @param {object} payload - The data to send, including task_id, feedback, etc.
     */
    const resumeAgent = (payload) => {
        if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ type: 'resume_agent', ...payload }));
        } else {
            alert("Connection not ready.");
        }
    };
    
    /**
     * Sends a command to the backend to stop a running agent.
     * @param {string} taskId - The ID of the task whose agent should be stopped.
     */
    const stopAgent = (taskId) => {
        if (ws.current?.readyState === WebSocket.OPEN && runningTasks[taskId]) {
            ws.current.send(JSON.stringify({ type: 'stop_agent', task_id: taskId }));
        }
    };

    /**
     * Sends a command to the backend to create the resources for a new task.
     * @param {string} taskId - The ID of the new task.
     */
    const createTask = (taskId) => {
         if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ type: 'task_create', task_id: taskId }));
        }
    }

    /**
     * Sends a command to the backend to delete all resources for a task.
     * @param {string} taskId - The ID of the task to delete.
     */
    const deleteTask = (taskId) => {
         if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ type: 'task_delete', task_id: taskId }));
        }
    }

    // Expose the connection state and the sender functions
    return {
        connectionStatus,
        runningTasks,
        runAgent,
        resumeAgent,
        stopAgent,
        createTask,
        deleteTask,
    };
};
