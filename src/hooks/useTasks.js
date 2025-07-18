import { useState, useEffect, useCallback } from 'preact/hooks';

// --- Use the window's hostname to determine the backend API address ---
const API_BASE_URL = `http://${window.location.hostname}:8766`;

/**
 * Custom hook for managing task state, now with correct initial history loading.
 */
export const useTasks = () => {
    const [tasks, setTasks] = useState([]);
    const [activeTaskId, setActiveTaskId] = useState(null);

    // --- THIS IS THE FIX ---
    // This effect is now responsible for loading the initial task list AND the
    // history for the initially active task.
    useEffect(() => {
        const fetchInitialData = async () => {
            try {
                // Step 1: Fetch the list of all tasks
                const tasksResponse = await fetch(`${API_BASE_URL}/api/tasks`);
                if (!tasksResponse.ok) throw new Error('Failed to fetch tasks.');
                const loadedTasks = await tasksResponse.json();

                if (loadedTasks.length === 0) {
                    setTasks([]);
                    setActiveTaskId(null);
                    return;
                }

                // Step 2: Determine the initial active task ID
                const savedActiveId = localStorage.getItem('research_agent_active_task_id');
                const initialActiveId = savedActiveId && loadedTasks.some(t => t.id === savedActiveId)
                    ? savedActiveId
                    : loadedTasks[0].id;
                
                setActiveTaskId(initialActiveId);

                // Step 3: Fetch the history for ONLY the active task
                let activeTaskHistory = [];
                if (initialActiveId) {
                    const historyResponse = await fetch(`${API_BASE_URL}/api/tasks/${initialActiveId}/history`);
                    if (historyResponse.ok) {
                        activeTaskHistory = await historyResponse.json();
                    } else {
                        console.error(`Failed to fetch history for task ${initialActiveId}`);
                    }
                }

                // Step 4: Initialize the tasks state, injecting the history into the active task
                const tasksWithHistory = loadedTasks.map(task => ({
                    ...task,
                    history: task.id === initialActiveId ? activeTaskHistory : []
                }));
                
                setTasks(tasksWithHistory);

            } catch (error) {
                console.error("Error loading initial data:", error);
                setTasks([]);
            }
        };
        fetchInitialData();
    }, []);

    // Effect to save only the active task ID to localStorage whenever it changes.
    useEffect(() => {
        if (activeTaskId) {
            localStorage.setItem('research_agent_active_task_id', activeTaskId);
        } else {
            localStorage.removeItem('research_agent_active_task_id');
        }
    }, [activeTaskId]);

    /**
     * Renames a task by sending a PUT request to the backend API.
     * @param {string} taskId - The ID of the task to rename.
     * @param {string} newName - The new name for the task.
     */
    const renameTask = async (taskId, newName) => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/tasks/${taskId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: newName }),
            });
            if (!response.ok) throw new Error('Failed to rename task on the server.');
            
            setTasks(prevTasks => prevTasks.map(task =>
                task.id === taskId ? { ...task, name: newName } : task
            ));
        } catch (error) {
            console.error("Error renaming task:", error);
        }
    };

    // The selectTask function is now passed into App.jsx to be used there
    const selectTask = (taskId) => {
        setActiveTaskId(taskId);
    };

    return {
        tasks,
        setTasks,
        activeTaskId,
        selectTask,
        renameTask,
    };
};
