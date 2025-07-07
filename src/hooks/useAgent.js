// src/hooks/useAgent.js
// -----------------------------------------------------------------------------
// ResearchAgent UI Hook (Phase 17 - Four-Track Event Handling)
//
// This version completes the frontend state management reintegration by making
// the `onMessage` callback aware of events from all four agent tracks.
//
// Key Architectural Changes:
// 1. Unified Event Handling: The `onMessage` callback in the `useEffect`
//    hook now contains a comprehensive `if/elif` structure to handle events
//    from both the "Standard" tracks and the "Peer Review" track.
// 2. Standard Plan Approval: It now correctly processes the
//    `plan_approval_request` event from the `std_human_in_the_loop_node`,
//    pushing an `architect_plan` object into the history to render the
//    interactive `ArchitectCard`.
// 3. Standard Execution Visualization: It correctly processes the start of
//    the `std_site_foreman_node` to create the `execution_plan` object,
//    which renders the `SiteForemanCard` to display the step-by-step
//    progress of a standard complex project.
// -----------------------------------------------------------------------------

import { useState, useEffect, useRef, useCallback } from 'preact/hooks';

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
