// js/ui_modules/task_ui.js

/**
 * Manages the UI for the task list.
 * - Renders the list of tasks.
 * - Handles interactions like selecting, creating, deleting, and renaming tasks.
 */

// Globals that this module will expect to be set by script.js or a state manager
// For now, these will be passed during initialization or accessed via a shared context.
// let tasks = []; // Reference to the main tasks array
// let currentTaskId = null; // ID of the currently active task

// Callbacks to be set by the main script
let onTaskSelectCallback = (taskId) => console.warn("onTaskSelectCallback not set in task_ui.js");
let onNewTaskCallback = () => console.warn("onNewTaskCallback not set in task_ui.js");
let onDeleteTaskCallback = (taskId, taskTitle) => console.warn("onDeleteTaskCallback not set in task_ui.js");
let onRenameTaskCallback = (taskId, currentTitle, newTitle) => console.warn("onRenameTaskCallback not set in task_ui.js");

// DOM Elements (will be passed during initialization)
let taskListUlElement;
let currentTaskTitleElement;
let uploadFileButtonElement; // To enable/disable based on task selection

/**
 * Initializes the Task UI module.
 * @param {object} elements - Object containing DOM elements { taskListUl, currentTaskTitleEl, uploadFileBtn }
 * @param {object} callbacks - Object containing callback functions { onTaskSelect, onNewTask, onDeleteTask, onRenameTask }
 */
function initTaskUI(elements, callbacks) {
    console.log("[TaskUI] Initializing...");
    taskListUlElement = elements.taskListUl;
    currentTaskTitleElement = elements.currentTaskTitleEl;
    uploadFileButtonElement = elements.uploadFileBtn;

    if (!taskListUlElement) console.error("[TaskUI] Task list UL element not provided for initialization!");
    if (!currentTaskTitleElement) console.error("[TaskUI] Current task title element not provided!");
    if (!uploadFileButtonElement) console.error("[TaskUI] Upload file button element not provided!");

    onTaskSelectCallback = callbacks.onTaskSelect;
    onNewTaskCallback = callbacks.onNewTask; // The main script will handle actual task creation and then re-render
    onDeleteTaskCallback = callbacks.onDeleteTask;
    onRenameTaskCallback = callbacks.onRenameTask;
    console.log("[TaskUI] Initialized with elements and callbacks.");
}

/**
 * Renders the list of tasks in the UI.
 * @param {Array<object>} tasksArray - The array of task objects.
 * @param {string|null} activeTaskId - The ID of the currently active task.
 */
function renderTaskList(tasksArray, activeTaskId) {
    if (!taskListUlElement) {
        console.error("[TaskUI] Cannot render task list: UL element not initialized.");
        return;
    }
    console.log("[TaskUI] Rendering task list. Tasks count:", tasksArray.length, "Active ID:", activeTaskId);
    taskListUlElement.innerHTML = ''; // Clear existing list

    if (tasksArray.length === 0) {
        taskListUlElement.innerHTML = '<li class="task-item-placeholder">No tasks yet.</li>';
    } else {
        tasksArray.forEach((task) => {
            const li = document.createElement('li');
            li.className = 'task-item';
            li.dataset.taskId = task.id;

            const titleSpan = document.createElement('span');
            titleSpan.className = 'task-title';
            const displayTitle = task.title.length > 25 ? task.title.substring(0, 22) + '...' : task.title;
            titleSpan.textContent = displayTitle;
            titleSpan.title = task.title; // Show full title on hover
            li.appendChild(titleSpan);

            const controlsDiv = document.createElement('div');
            controlsDiv.className = 'task-item-controls';

            const editBtn = document.createElement('button');
            editBtn.className = 'task-edit-btn';
            editBtn.textContent = '✏️';
            editBtn.title = `Rename Task: ${task.title}`;
            editBtn.dataset.taskId = task.id; // For easier access in handler
            editBtn.dataset.taskTitle = task.title; // Store current title
            editBtn.addEventListener('click', (event) => {
                event.stopPropagation(); // Prevent task selection
                handleEditTaskClick(task.id, task.title);
            });
            controlsDiv.appendChild(editBtn);

            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'task-delete-btn';
            deleteBtn.textContent = '🗑️';
            deleteBtn.title = `Delete Task: ${task.title}`;
            deleteBtn.dataset.taskId = task.id; // For easier access in handler
            deleteBtn.addEventListener('click', (event) => {
                event.stopPropagation(); // Prevent task selection
                handleDeleteTaskClick(task.id, task.title);
            });
            controlsDiv.appendChild(deleteBtn);

            li.appendChild(controlsDiv);

            li.addEventListener('click', () => {
                handleTaskItemClick(task.id);
            });

            if (task.id === activeTaskId) {
                li.classList.add('active');
            }
            taskListUlElement.appendChild(li);
        });
    }
    updateCurrentTaskTitleUI(tasksArray, activeTaskId);
    if (uploadFileButtonElement) {
        uploadFileButtonElement.disabled = !activeTaskId;
    }
    console.log("[TaskUI] Task list rendered.");
}

/**
 * Handles the click event on a task item.
 * @param {string} taskId - The ID of the clicked task.
 */
function handleTaskItemClick(taskId) {
    console.log(`[TaskUI] Task item clicked: ${taskId}`);
    onTaskSelectCallback(taskId); // Notify the main script
}

/**
 * Handles the click event for deleting a task.
 * @param {string} taskId - The ID of the task to delete.
 * @param {string} taskTitle - The title of the task to delete (for confirmation).
 */
function handleDeleteTaskClick(taskId, taskTitle) {
    console.log(`[TaskUI] Delete button clicked for task: ${taskId} (${taskTitle})`);
    if (confirm(`Are you sure you want to delete task "${taskTitle}"? This cannot be undone.`)) {
        onDeleteTaskCallback(taskId, taskTitle); // Notify the main script
    } else {
        console.log("[TaskUI] Deletion cancelled by user.");
    }
}

/**
 * Handles the click event for editing a task's title.
 * @param {string} taskId - The ID of the task to edit.
 * @param {string} currentTitle - The current title of the task.
 */
function handleEditTaskClick(taskId, currentTitle) {
    console.log(`[TaskUI] Edit button clicked for task: ${taskId} (${currentTitle})`);
    const newTitle = prompt(`Enter new name for task "${currentTitle}":`, currentTitle);

    if (newTitle === null) { // User pressed cancel
        console.log("[TaskUI] Rename cancelled by user.");
        return;
    }

    const trimmedTitle = newTitle.trim();
    if (!trimmedTitle) {
        alert("Task name cannot be empty.");
        console.log("[TaskUI] Rename aborted: empty title.");
        return;
    }

    if (trimmedTitle === currentTitle) {
        console.log("[TaskUI] Rename aborted: title unchanged.");
        return;
    }
    onRenameTaskCallback(taskId, currentTitle, trimmedTitle); // Notify the main script
}


/**
 * Updates the displayed title of the current task.
 * @param {Array<object>} tasksArray - The array of task objects.
 * @param {string|null} activeTaskId - The ID of the currently active task.
 */
function updateCurrentTaskTitleUI(tasksArray, activeTaskId) {
    if (!currentTaskTitleElement) {
        console.error("[TaskUI] Cannot update task title: element not initialized.");
        return;
    }
    const currentTask = tasksArray.find(task => task.id === activeTaskId);
    const title = currentTask ? currentTask.title : "No Task Selected";
    currentTaskTitleElement.textContent = title;
    console.log(`[TaskUI] Current task title updated to: "${title}"`);
}

// Note: The `handleNewTaskClick` from script.js is simple enough
// that it can remain in script.js as it directly calls `onNewTaskCallback`.
// The `newTaskButton` event listener will be set up in script.js.

