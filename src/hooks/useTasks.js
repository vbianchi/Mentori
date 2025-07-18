import { useState, useEffect, useCallback } from 'preact/hooks';

// --- NEW: Use the window's hostname to determine the backend API address ---
const API_BASE_URL = `http://${window.location.hostname}:8766`;

/**
 * Custom hook for managing task state, now backed by a persistent database via a REST API.
 * All localStorage logic has been removed.
 */
export const useTasks = () => {
    const [tasks, setTasks] = useState([]);
    const [activeTaskId, setActiveTaskId] = useState(null);

    // Effect to load all tasks from the database on initial component mount.
    useEffect(() => {
        const fetchTasks = async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/api/tasks`);
                if (!response.ok) {
                    throw new Error('Failed to fetch tasks from the server.');
                }
                const loadedTasks = await response.json();
                
                // Initialize history for each task, to be loaded on demand later.
                const tasksWithHistory = loadedTasks.map(task => ({ ...task, history: [] }));
                setTasks(tasksWithHistory);

                // Determine which task should be active.
                const savedActiveId = localStorage.getItem('research_agent_active_task_id');
                if (savedActiveId && loadedTasks.some(t => t.id === savedActiveId)) {
                    setActiveTaskId(savedActiveId);
                } else if (loadedTasks.length > 0) {
                    setActiveTaskId(loadedTasks[0].id);
                }

            } catch (error) {
                console.error("Error loading tasks:", error);
                // In case of an error, start with an empty list.
                setTasks([]);
            }
        };
        fetchTasks();
    }, []);

    // Effect to save only the active task ID to localStorage whenever it changes.
    // The task list itself is no longer saved here.
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
            
            // Update the local state only after the server confirms success.
            setTasks(prevTasks => prevTasks.map(task =>
                task.id === taskId ? { ...task, name: newName } : task
            ));
        } catch (error) {
            console.error("Error renaming task:", error);
            // Optionally, show an error to the user here.
        }
    };

    // The selectTask function remains the same, it only manages local state.
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
