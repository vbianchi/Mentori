import { useState, useEffect } from 'preact/hooks';

/**
 * Custom hook for managing task state and persistence in localStorage.
 */
export const useTasks = () => {
    // State management for tasks and the active task ID
    const [tasks, setTasks] = useState([]); // 
    const [activeTaskId, setActiveTaskId] = useState(null); // 

    // Effect to load tasks from localStorage on initial render
    useEffect(() => {
        const savedTasks = localStorage.getItem('research_agent_tasks'); // 
        const savedActiveId = localStorage.getItem('research_agent_active_task_id'); // 
        const loadedTasks = savedTasks ? JSON.parse(savedTasks) : []; // 
        setTasks(loadedTasks); // 

        if (savedActiveId && loadedTasks.some(t => t.id === savedActiveId)) {
            setActiveTaskId(savedActiveId); // 
        } else if (loadedTasks.length > 0) {
            setActiveTaskId(loadedTasks[0].id); // 
        }
    }, []);

    // Effect to save the full task list to localStorage whenever it changes
    useEffect(() => {
        if (tasks.length > 0) {
            localStorage.setItem('research_agent_tasks', JSON.stringify(tasks)); // 
        } else {
            localStorage.removeItem('research_agent_tasks'); // 
        }
    }, [tasks]);

    // Effect to save the active task ID to localStorage whenever it changes
    useEffect(() => {
        if (activeTaskId) {
            localStorage.setItem('research_agent_active_task_id', activeTaskId); // 
        } else {
            localStorage.removeItem('research_agent_active_task_id'); // 
        }
    }, [activeTaskId]);

    /**
     * Renames a task given its ID and a new name.
     * @param {string} taskId - The ID of the task to rename.
     * @param {string} newName - The new name for the task.
     */
    const renameTask = (taskId, newName) => {
        setTasks(prevTasks => prevTasks.map(task =>
            task.id === taskId ? { ...task, name: newName } : task
        )); // 
    };

    // Return the state values and handler functions to be used by components
    return {
        tasks,
        setTasks,
        activeTaskId,
        selectTask: setActiveTaskId,
        renameTask,
    };
};