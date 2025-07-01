// src/hooks/useAgent.js
import { useState, useEffect, useRef } from 'preact/hooks';

/**
 * Custom hook to manage the WebSocket connection and all agent communication.
 * @param {Function} onMessage - A callback function to process incoming messages from the agent.
 */
export const useAgent = (onMessage) => {
    const ws = useRef(null);
    const [connectionStatus, setConnectionStatus] = useState("Disconnected");
    const [runningTasks, setRunningTasks] = useState({});

    useEffect(() => {
        function connect() {
            setConnectionStatus("Connecting...");
            const socket = new WebSocket("ws://localhost:8765");
            ws.current = socket;

            socket.onopen = () => setConnectionStatus("Connected");

            socket.onclose = () => {
                setConnectionStatus("Disconnected");
                setRunningTasks({});
                setTimeout(connect, 5000);
            };

            socket.onerror = (err) => {
                console.error("WebSocket error:", err);
                socket.close();
            };

            socket.onmessage = (event) => {
                const newEvent = JSON.parse(event.data);
                
                // --- ADDED: Debug logging ---
                console.log('Received WebSocket event:', newEvent);

                setRunningTasks(prev => {
                    const newTasks = { ...prev };
                    const { type, task_id, name, event: chainEvent } = newEvent;

                    if (type === 'agent_started' || type === 'agent_resumed') {
                        newTasks[task_id] = "Thinking...";
                    } else if (type === 'agent_event' && chainEvent === 'on_chain_start') {
                        newTasks[task_id] = name;
                    } else if (['final_answer', 'agent_stopped', 'plan_approval_request', 'board_approval_request', 'final_plan_approval_request'].includes(type)) {
                        delete newTasks[task_id];
                    }
                    return newTasks;
                });
                
                if (onMessage) {
                    onMessage(newEvent);
                }
            };
        }

        connect();

        return () => {
            if (ws.current) {
                ws.current.onclose = null;
                ws.current.close();
            }
        };
    }, [onMessage]);

    const runAgent = (payload) => {
        if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ type: 'run_agent', ...payload }));
        } else {
            alert("Connection not ready. Please wait a moment and try again.");
        }
    };

    const resumeAgent = (payload) => {
        if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ type: 'resume_agent', ...payload }));
        } else {
            alert("Connection not ready.");
        }
    };
    
    const stopAgent = (taskId) => {
        if (ws.current?.readyState === WebSocket.OPEN && runningTasks[taskId]) {
            ws.current.send(JSON.stringify({ type: 'stop_agent', task_id: taskId }));
        }
    };

    const createTask = (taskId) => {
         if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ type: 'task_create', task_id: taskId }));
        }
    }

    const deleteTask = (taskId) => {
         if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ type: 'task_delete', task_id: taskId }));
        }
    }

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
