// src/hooks/useAgent.js
import { useState, useEffect, useRef } from 'preact/hooks';

/**
 * Custom hook to manage the WebSocket connection and all agent communication.
 * @param {Function} onMessage - A callback function to process incoming messages from the agent.
 * @param {Array} tasks - The full list of tasks from the useTasks hook.
 * @param {string} activeTaskId - The ID of the currently active task.
 */
export const useAgent = (onMessage, tasks, activeTaskId) => {
    const ws = useRef(null);
    const [connectionStatus, setConnectionStatus] = useState("Disconnected");
    const [runningTasks, setRunningTasks] = useState({});

    useEffect(() => {
        function connect() {
            setConnectionStatus("Connecting...");
            
            // This uses the dynamic hostname for robust networking.
            const backendHost = window.location.hostname;
            const wsUrl = `ws://${backendHost}:8765`;
            console.log(`Attempting to connect WebSocket to: ${wsUrl}`);
            
            const socket = new WebSocket(wsUrl);
            ws.current = socket;

            socket.onopen = () => {
                console.log("WebSocket connection established.");
                setConnectionStatus("Connected");
            }

            socket.onclose = () => {
                console.warn("WebSocket connection closed. Attempting to reconnect in 5 seconds...");
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
                console.log('Received WebSocket event:', newEvent);

                setRunningTasks(prev => {
                    const newTasks = { ...prev };
                    const { type, task_id, name, event: chainEvent } = newEvent;

                    if (type === 'agent_started' || type === 'agent_resumed') {
                        newTasks[task_id] = "Thinking...";
                    } else if (type === 'agent_event' && chainEvent === 'on_chain_start') {
                        newTasks[task_id] = name;
                    } else if (['final_answer', 'agent_stopped', 'plan_approval_request', 'board_approval_request', 'final_plan_approval_request', 'user_guidance_approval_request'].includes(type)) {
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

    useEffect(() => {
        if (!activeTaskId || !tasks || tasks.length === 0) return;
        const activeTask = tasks.find(t => t.id === activeTaskId);
        if (!activeTask || !activeTask.history || activeTask.history.length === 0) return;
        
        const lastHistoryItem = activeTask.history[activeTask.history.length - 1];
        if (lastHistoryItem?.type === 'run_container' && lastHistoryItem.children.length > 0) {
            const lastChild = lastHistoryItem.children[lastHistoryItem.children.length - 1];
            if (lastChild.type === 'execution_step') {
                if (ws.current?.readyState === WebSocket.OPEN) {
                    console.log(`ACKing step for task ${activeTaskId}.`);
                    ws.current.send(JSON.stringify({ type: 'ack', task_id: activeTaskId }));
                }
            }
        }
    }, [tasks, activeTaskId]);

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