import { useState, useEffect, useRef } from 'preact/hooks';

/**
 * Custom hook to manage the WebSocket connection and all agent communication.
 * @param {Function} onMessage - A callback function to process incoming messages from the agent.
 */
export const useAgent = (onMessage) => {
    // State for the WebSocket connection and its status
    const ws = useRef(null);
    const [connectionStatus, setConnectionStatus] = useState("Disconnected");
    
    // --- MODIFIED: State now tracks the specific active node for each task ---
    // Instead of { [taskId]: true }, it will be { [taskId]: "Node Name" }
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
                setTimeout(connect, 5000); // Attempt to reconnect
            };

            socket.onerror = (err) => {
                console.error("WebSocket error:", err);
                socket.close();
            };

            socket.onmessage = (event) => {
                const newEvent = JSON.parse(event.data);

                // --- MODIFIED: Update running status with specific node names ---
                setRunningTasks(prev => {
                    const newTasks = { ...prev };
                    const { type, task_id, name, event: chainEvent } = newEvent;

                    if (type === 'agent_started' || type === 'agent_resumed') {
                        newTasks[task_id] = "Thinking..."; // Set initial generic status
                    } else if (type === 'agent_event' && chainEvent === 'on_chain_start') {
                        newTasks[task_id] = name; // Update with specific node name
                    } else if (type === 'final_answer' || type === 'agent_stopped' || type === 'plan_approval_request') {
                        delete newTasks[task_id]; // Clear status on completion/pause
                    }
                    return newTasks;
                });
                
                // Pass the event up to the main component's logic handler
                if (onMessage) {
                    onMessage(newEvent);
                }
            };
        }

        connect();

        // Cleanup function to close the WebSocket connection
        return () => {
            if (ws.current) {
                ws.current.onclose = null; // Prevent reconnection attempts
                ws.current.close();
            }
        };
    }, [onMessage]);

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
