import { useState, useEffect, useRef } from 'react';
import { Save, FileCode, Folder, Upload, FolderPlus, FilePlus, Search, X, Copy, Image, FileText, Download, Code, ClipboardCheck, BookOpen, Eye, EyeOff } from 'lucide-react';
import clsx from 'clsx';
import config from '../../config';
import FileTree from '../ui/FileTree';
import Breadcrumb from '../ui/Breadcrumb';
import Toast from '../ui/Toast';
import { useToast } from '../../hooks/useToast';
import { copyToClipboard } from '../../utils/clipboard';
import './ArtifactPanel.css';
import './FileExplorer.css';
import MemoryPanel from './MemoryPanel';
import NotebookViewer from './NotebookViewer';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeHighlight from 'rehype-highlight';
import rehypeKatex from 'rehype-katex';
import 'highlight.js/styles/atom-one-dark.css';

/**
 * Copy Button Helper for Code Blocks
 */
const CodeCopyButton = ({ text, className }) => {
    const [copied, setCopied] = useState(false);

    const handleCopy = async (e) => {
        e.stopPropagation();
        try {
            await copyToClipboard(text);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    };

    return (
        <button
            className={clsx("p-1 text-muted hover:text-white transition-colors rounded hover:bg-white/10", className)}
            onClick={handleCopy}
            title={copied ? "Copied!" : "Copy Code"}
        >
            {copied ? <ClipboardCheck size={14} className="text-green-500 font-bold" /> : <Copy size={14} />}
        </button>
    );
};

/**
 * Custom Code Block Renderer
 */
const PreBlock = ({ children, ...props }) => {
    if (!children || !children.props) return <pre {...props}>{children}</pre>;

    const codeProps = children.props;
    const className = codeProps.className || "";
    const language = className.replace("language-", "") || "text";
    const content = String(codeProps.children || '').replace(/\n$/, "");

    return (
        <div className="code-block-wrapper my-4 rounded-lg border border-white/10 overflow-hidden bg-slate-950">
            <div className="code-header flex items-center justify-between px-3 py-2 bg-white/5 border-b border-white/5">
                <span className="text-xs font-mono text-muted uppercase tracking-wider">{language}</span>
                <CodeCopyButton text={content} />
            </div>
            <div className="code-body overflow-x-auto p-3">
                <pre {...props} className="!m-0 !bg-transparent !border-0 !shadow-none !p-0">
                    {children}
                </pre>
            </div>
        </div>
    );
};

export default function ArtifactPanel({
    activeFile = { name: 'untitled.txt', content: '', language: 'text', path: '' },
    taskId,
    activeTaskDisplayId = null,
    onFileLoad,
    triggerRefresh = 0, // External refresh trigger
    // Notebook viewer props
    isCoderMode = false,
    notebookData = null, // { name, cells, activeCellId }
    availableNotebooks = [],
    onSelectNotebook = null,
    onRefreshNotebooks = null,
    onCloseNotebook = null,
    onExecuteCell = null,
    onUpdateCell = null,
    onRunAllCells = null,
    isRunningAllCells = false,
}) {
    const [content, setContent] = useState(activeFile.content);
    const [isDirty, setIsDirty] = useState(false);
    const [activeTab, setActiveTab] = useState('workspace'); // 'workspace' | 'editor' | 'memory' | 'notebook'
    const [showMarkdown, setShowMarkdown] = useState(true);

    // Auto-switch to notebook tab when entering coder mode (only on mode change)
    useEffect(() => {
        if (isCoderMode) {
            console.log('[ArtifactPanel] Switching to notebook tab (coder mode)');
            setActiveTab('notebook');
        }
    }, [isCoderMode]);

    // File Explorer State
    const [refreshKey, setRefreshKey] = useState(0);
    const [isDragOver, setIsDragOver] = useState(false);
    const [uploading, setUploading] = useState(false);
    const fileInputRef = useRef(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [currentPath, setCurrentPath] = useState('');
    const [selectedPath, setSelectedPath] = useState('');
    const [taskFolders, setTaskFolders] = useState([]);
    const [showHiddenFiles, setShowHiddenFiles] = useState(false);

    // Inline rename state
    const [isRenamingFile, setIsRenamingFile] = useState(false);
    const [renameValue, setRenameValue] = useState('');

    // Preview state for images/PDFs
    const [previewUrl, setPreviewUrl] = useState(null);
    const [previewType, setPreviewType] = useState(null); // 'image' | 'pdf' | null

    // Toast notifications
    const { toasts, success, error, removeToast } = useToast();

    useEffect(() => {
        setContent(activeFile.content || '');
        setIsDirty(false);
        setSelectedPath(activeFile.path || '');
    }, [activeFile]);

    // Refresh file system when triggerRefresh changes (external trigger)
    useEffect(() => {
        if (triggerRefresh > 0) {
            setRefreshKey(prev => prev + 1);
            // Also refresh task folders list
            fetchTaskFolders();
        }
    }, [triggerRefresh]);

    // Fetch task folders to prevent deletion
    const fetchTaskFolders = async () => {
        try {
            const token = localStorage.getItem("mentori_token");
            const res = await fetch(`${config.API_BASE_URL}/tasks`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) {
                const tasks = await res.json();
                // Extract task IDs to build folder paths like "task_123"
                const folders = tasks.map(task => `task_${task.display_id}`);
                setTaskFolders(folders);
            }
        } catch (e) {
            console.error("Failed to fetch tasks:", e);
        }
    };

    useEffect(() => {
        fetchTaskFolders();
    }, []);

    const handleContentChange = (e) => {
        setContent(e.target.value);
        setIsDirty(true);
    };

    const handleSave = async () => {
        if (!activeFile.path) {
            error('No file selected to save');
            return;
        }

        try {
            const token = localStorage.getItem("mentori_token");
            const effectiveTaskId = taskId || 'default';
            const res = await fetch(`${config.API_BASE_URL}/tasks/${effectiveTaskId}/files/update`, {
                method: "PUT",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    path: activeFile.path,
                    content: content
                })
            });

            if (res.ok) {
                setIsDirty(false);
                success(`Saved ${activeFile.name}`);
                // Refresh file tree to update metadata
                setRefreshKey(prev => prev + 1);
                // Update the activeFile content to match saved content
                onFileLoad && onFileLoad({
                    ...activeFile,
                    content: content
                });
            } else {
                const responseData = await res.json();
                error(`Save failed: ${responseData.detail || 'Unknown error'}`);
            }
        } catch (e) {
            error(`Save error: ${e.message}`);
        }
    };

    const handleKeyDown = (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            handleSave();
        }
    };

    // --- File Operations ---

    const apiCall = async (endpoint, method, body) => {
        const token = localStorage.getItem("mentori_token");
        try {
            const effectiveTaskId = taskId || 'default';
            const res = await fetch(`${config.API_BASE_URL}/tasks/${effectiveTaskId}/files/${endpoint}`, {
                method,
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(body)
            });
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Request failed");
            }
            return await res.json();
        } catch (e) {
            error(e.message);
            throw e;
        }
    };

    const handleFileSelect = async (node) => {
        const ext = node.name.split('.').pop().toLowerCase();
        const imageExts = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp', 'ico'];
        const pdfExts = ['pdf'];
        const isImage = imageExts.includes(ext);
        const isPdf = pdfExts.includes(ext);

        // Clean up previous preview URL to prevent memory leaks
        if (previewUrl) {
            URL.revokeObjectURL(previewUrl);
            setPreviewUrl(null);
            setPreviewType(null);
        }

        try {
            const token = localStorage.getItem("mentori_token");
            const effectiveTaskId = taskId || 'default';
            const cacheBuster = `&_t=${Date.now()}`;
            const url = `${config.API_BASE_URL}/tasks/${effectiveTaskId}/files/content?path=${encodeURIComponent(node.path)}${cacheBuster}`;

            if (isImage || isPdf) {
                // Fetch as blob for binary files
                const res = await fetch(url, {
                    headers: {
                        "Authorization": `Bearer ${token}`,
                        "Cache-Control": "no-cache, no-store, must-revalidate"
                    }
                });

                if (res.ok) {
                    const blob = await res.blob();
                    const objectUrl = URL.createObjectURL(blob);
                    setPreviewUrl(objectUrl);
                    setPreviewType(isImage ? 'image' : 'pdf');

                    onFileLoad && onFileLoad({
                        name: node.name,
                        content: '', // No text content for binary files
                        language: isImage ? 'image' : 'pdf',
                        path: node.path
                    });

                    setActiveTab('editor');
                    setSelectedPath(node.path);

                    const folderPath = node.path.includes('/')
                        ? node.path.substring(0, node.path.lastIndexOf('/'))
                        : '';
                    setCurrentPath(folderPath);
                } else {
                    error("Failed to load file");
                }
            } else {
                // Fetch as text for text files
                const res = await fetch(url, {
                    headers: {
                        "Authorization": `Bearer ${token}`,
                        "Cache-Control": "no-cache, no-store, must-revalidate",
                        "Pragma": "no-cache"
                    }
                });

                if (res.ok) {
                    const text = await res.text();
                    let lang = 'text';
                    if (['py'].includes(ext)) lang = 'python';
                    if (['js', 'jsx'].includes(ext)) lang = 'javascript';
                    if (['ts', 'tsx'].includes(ext)) lang = 'typescript';
                    if (['html'].includes(ext)) lang = 'html';
                    if (['css'].includes(ext)) lang = 'css';
                    if (['json'].includes(ext)) lang = 'json';
                    if (['md'].includes(ext)) lang = 'markdown';

                    onFileLoad && onFileLoad({
                        name: node.name,
                        content: text,
                        language: lang,
                        path: node.path
                    });

                    setActiveTab('editor');
                    setSelectedPath(node.path);

                    const folderPath = node.path.includes('/')
                        ? node.path.substring(0, node.path.lastIndexOf('/'))
                        : '';
                    setCurrentPath(folderPath);
                } else {
                    error("Failed to load file");
                }
            }
        } catch (e) {
            error(`Load error: ${e.message}`);
        }
    };

    // Get the default upload path for active task
    const getTaskFilesPath = () => {
        return activeTaskDisplayId ? `task_${activeTaskDisplayId}/files` : '';
    };

    const uploadFile = async (file, targetPath = null) => {
        setUploading(true);

        // Default to active task's files/ folder if no path specified
        const uploadPath = targetPath !== null ? targetPath : getTaskFilesPath();

        const formData = new FormData();
        formData.append("file", file);
        if (uploadPath) {
            formData.append("path", uploadPath);
        }

        try {
            const token = localStorage.getItem("mentori_token");
            const effectiveTaskId = taskId || 'default';
            const res = await fetch(`${config.API_BASE_URL}/tasks/${effectiveTaskId}/files`, {
                method: "POST",
                headers: { "Authorization": `Bearer ${token}` },
                body: formData
            });

            if (res.ok) {
                success(`Uploaded ${file.name}`);
                setRefreshKey(prev => prev + 1);

                // Navigate to the upload folder and switch to workspace view
                if (uploadPath) {
                    setCurrentPath(uploadPath);
                    setActiveTab('workspace');
                }
            } else {
                const err = await res.json();
                error(`Upload failed: ${err.detail || 'Unknown error'}`);
            }
        } catch (e) {
            error(`Upload error: ${e.message}`);
        } finally {
            setUploading(false);
            setIsDragOver(false);
        }
    };

    const handleDelete = async (node) => {
        // Direct delete without confirmation for faster workflow
        try {
            const token = localStorage.getItem("mentori_token");
            const effectiveTaskId = taskId || 'default';
            const res = await fetch(`${config.API_BASE_URL}/tasks/${effectiveTaskId}/files/delete?path=${encodeURIComponent(node.path)}`, {
                method: "DELETE",
                headers: { "Authorization": `Bearer ${token}` }
            });

            if (res.ok) {
                success(`Deleted ${node.name}`);
                setRefreshKey(k => k + 1);

                // Clear editor if deleted file was selected
                if (node.path === activeFile.path) {
                    onFileLoad && onFileLoad({ name: 'untitled.txt', content: '', language: 'text', path: '' });
                }
            } else {
                error("Delete failed");
            }
        } catch (e) {
            error("Delete error");
        }
    };

    const handleCreateFolder = async () => {
        const name = prompt("New Folder Name:");
        if (!name) return;

        // If we have a current path, use it. Otherwise, default to task's files folder
        let basePath = currentPath;
        if (!basePath && activeTaskDisplayId) {
            // Default to task's files/ folder when no path is selected
            basePath = `task_${activeTaskDisplayId}/files`;
        }

        const path = basePath ? `${basePath}/${name}` : name;

        try {
            await apiCall("create_folder", "POST", { path });
            success(`Created folder ${name}`);
            setRefreshKey(k => k + 1);
        } catch (e) {
            // Error already shown by apiCall
        }
    };

    const handleCreateFile = async () => {
        const name = prompt("New File Name (e.g., script.py):");
        if (!name) return;

        // If we have a current path, use it. Otherwise, default to task's files folder
        let basePath = currentPath;
        if (!basePath && activeTaskDisplayId) {
            // Default to task's files/ folder when no path is selected
            basePath = `task_${activeTaskDisplayId}/files`;
        }

        const path = basePath ? `${basePath}/${name}` : name;

        try {
            await apiCall("create_file", "POST", { path, content: "" });
            success(`Created file ${name}`);
            setRefreshKey(k => k + 1);
        } catch (e) {
            // Error already shown by apiCall
        }
    };

    const handleRename = async (node) => {
        const newName = prompt("Rename to:", node.name);
        if (!newName || newName === node.name) return;

        try {
            await apiCall("rename", "POST", { path: node.path, new_name: newName });
            success(`Renamed to ${newName}`);
            setRefreshKey(k => k + 1);
        } catch (e) {
            // Error already shown by apiCall
        }
    };

    const handleCopy = async (node) => {
        const destination = prompt("Copy to folder path (leave empty for root):", "");
        if (destination === null) return; // User cancelled

        try {
            await apiCall("copy", "POST", {
                source_path: node.path,
                destination_path: destination || "."
            });
            success(`Copied ${node.name}`);
            setRefreshKey(k => k + 1);
        } catch (e) {
            // Error already shown by apiCall
        }
    };

    const handleMoveItem = async (sourceNode, targetNode) => {
        if (targetNode.type !== 'folder') return;

        try {
            await apiCall("move", "POST", {
                source_path: sourceNode.path,
                destination_path: targetNode.path
            });
            success(`Moved ${sourceNode.name} to ${targetNode.name}`);
            setRefreshKey(k => k + 1);
        } catch (e) {
            // Error already shown by apiCall
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragOver(false);

        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            // Upload all dropped files to active task's files/ folder
            const files = Array.from(e.dataTransfer.files);
            console.log(`Dropping ${files.length} file(s) to task files folder`, files.map(f => f.name));
            files.forEach(file => {
                uploadFile(file); // Uses default task files path
            });
        } else {
            console.warn('No files in dataTransfer');
        }
    };

    const handleDragOver = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragOver(true);
        e.dataTransfer.dropEffect = 'copy';
    };

    const handleDragLeave = (e) => {
        e.preventDefault();
        // Only hide overlay if leaving the container itself
        if (e.target === e.currentTarget) {
            setIsDragOver(false);
        }
    };

    const handleCopyContent = async () => {
        try {
            await copyToClipboard(content);
            success("Copied to clipboard");
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    };

    // Create a new file in the active task's files/ folder
    const handleCreateNewFileInTaskFolder = async () => {
        const name = prompt("New File Name (e.g., notes.txt):");
        if (!name) return;

        // Build path: task_<displayId>/files/<filename>
        const basePath = activeTaskDisplayId
            ? `task_${activeTaskDisplayId}/files`
            : '';
        const path = basePath ? `${basePath}/${name}` : name;

        try {
            await apiCall("create_file", "POST", { path, content: "" });
            success(`Created ${name}`);
            setRefreshKey(k => k + 1);

            // Open the newly created file in the editor
            onFileLoad && onFileLoad({
                name: name,
                content: '',
                language: 'text',
                path: path
            });
            setSelectedPath(path);
            setCurrentPath(basePath);
        } catch (e) {
            // Error already shown by apiCall
        }
    };

    // Inline rename handlers
    const startRename = () => {
        if (!activeFile.path) return;
        setIsRenamingFile(true);
        setRenameValue(activeFile.name);
    };

    const handleInlineRename = async () => {
        if (!isRenamingFile || !renameValue || renameValue === activeFile.name) {
            setIsRenamingFile(false);
            return;
        }

        try {
            await apiCall("rename", "POST", { path: activeFile.path, new_name: renameValue });
            success(`Renamed to ${renameValue}`);
            setRefreshKey(k => k + 1);

            // Update the active file with new name and path
            const folderPath = activeFile.path.includes('/')
                ? activeFile.path.substring(0, activeFile.path.lastIndexOf('/'))
                : '';
            const newPath = folderPath ? `${folderPath}/${renameValue}` : renameValue;

            onFileLoad && onFileLoad({
                ...activeFile,
                name: renameValue,
                path: newPath
            });

            setIsRenamingFile(false);
        } catch (e) {
            setIsRenamingFile(false);
            setRenameValue(activeFile.name);
        }
    };

    const handleCreateNotebook = async (name, kernel = 'python3') => {
        if (!taskId) return;
        try {
            const token = localStorage.getItem("mentori_token");
            const res = await fetch(`${config.API_BASE_URL}/tasks/${taskId}/notebooks`, {
                method: "POST",
                headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" },
                body: JSON.stringify({ name, kernel }),
            });
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || "Failed to create notebook");
            }
            // Refresh the list then auto-open the new notebook
            onRefreshNotebooks?.();
            await onSelectNotebook?.(name);
        } catch (e) {
            addToast(e.message || "Failed to create notebook", "error");
        }
    };

    const handleAddCell = async (notebookName, cellType = 'code', position = null) => {
        if (!taskId || !notebookName) return null;
        try {
            const token = localStorage.getItem("mentori_token");
            const body = { source: '', cell_type: cellType };
            if (position !== null && position !== undefined) body.position = position;
            const res = await fetch(
                `${config.API_BASE_URL}/tasks/${taskId}/notebooks/${notebookName}/cells`,
                {
                    method: "POST",
                    headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" },
                    body: JSON.stringify(body),
                }
            );
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || "Failed to add cell");
            }
            const data = await res.json();
            // Reload the notebook content (cells), not just the notebook list
            await onSelectNotebook?.(notebookName);
            return data.cell_id;
        } catch (e) {
            addToast(e.message || "Failed to add cell", "error");
            return null;
        }
    };

    const handleDeleteCell = async (notebookName, cellId) => {
        if (!taskId || !notebookName || !cellId) return;
        try {
            const token = localStorage.getItem("mentori_token");
            const res = await fetch(
                `${config.API_BASE_URL}/tasks/${taskId}/notebooks/${notebookName}/cells/${cellId}`,
                {
                    method: "DELETE",
                    headers: { "Authorization": `Bearer ${token}` },
                }
            );
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || "Failed to delete cell");
            }
            // Reload the notebook content to reflect the deleted cell
            await onSelectNotebook?.(notebookName);
        } catch (e) {
            addToast(e.message || "Failed to delete cell", "error");
        }
    };

    const handleKernelAction = async (notebookName, action) => {
        if (!taskId || !notebookName) return;
        try {
            const token = localStorage.getItem("mentori_token");
            const res = await fetch(
                `${config.API_BASE_URL}/tasks/${taskId}/notebooks/${notebookName}/kernel/${action}`,
                { method: "POST", headers: { "Authorization": `Bearer ${token}` } }
            );
            const data = await res.json().catch(() => ({}));
            if (!res.ok) throw new Error(data.detail || `Kernel ${action} failed`);
            addToast(
                action === 'restart'
                    ? 'Kernel restarted — all variables cleared'
                    : 'Kernel interrupted',
                'info'
            );
        } catch (e) {
            addToast(e.message || `Kernel ${action} failed`, "error");
        }
    };

    return (
        <div className="artifact-panel">
            <Toast toasts={toasts} onRemove={removeToast} />

            {/* Header with Tabs */}
            <div className="artifact-header-container">
                <div className="artifact-header-row">
                    <div className="tabs">
                        <button
                            className={clsx('tab-btn', { active: activeTab === 'workspace' })}
                            onClick={() => setActiveTab('workspace')}
                        >
                            <Folder size={14} /> File System
                        </button>
                        <button
                            className={clsx('tab-btn', { active: activeTab === 'editor' })}
                            onClick={() => setActiveTab('editor')}
                        >
                            <FileCode size={14} /> Editor
                        </button>
                        <button
                            className={clsx('tab-btn', { active: activeTab === 'memory' })}
                            onClick={() => setActiveTab('memory')}
                        >
                            <BookOpen size={14} /> Memory
                        </button>
                        <button
                            className={clsx('tab-btn', { active: activeTab === 'notebook' })}
                            onClick={() => setActiveTab('notebook')}
                        >
                            <Code size={14} /> Notebook
                        </button>
                    </div>

                    <div className="header-actions">
                        {/* Dirty indicator moved to filename row */}
                        {activeTab === 'editor' && (
                            <>
                                {/* Actions moved to filename row */}
                            </>
                        )}
                    </div>
                </div>

                {/* Breadcrumb removed — file tree provides navigation */}

                {/* Filename Display for Editor */}
                {/* Filename Display & Actions for Editor */}
                {activeTab === 'editor' && (
                    <div className="filename-bubble flex justify-between items-center pr-2">
                        {/* Left: Filename / Rename Input */}
                        {/* Left: Filename / Rename Input */}
                        <div className="flex-1 flex items-center min-w-0 mr-4 gap-3">
                            {isRenamingFile ? (
                                <input
                                    type="text"
                                    className="rename-input w-full"
                                    value={renameValue}
                                    onChange={(e) => setRenameValue(e.target.value)}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter') {
                                            handleInlineRename();
                                        } else if (e.key === 'Escape') {
                                            setIsRenamingFile(false);
                                            setRenameValue(activeFile.name);
                                        }
                                    }}
                                    onBlur={handleInlineRename}
                                    autoFocus
                                />
                            ) : (
                                <span
                                    className="text-muted text-xs font-mono cursor-pointer hover:text-accent-secondary truncate"
                                    onClick={startRename}
                                    title="Click to rename"
                                >
                                    {activeFile.name}
                                </span>
                            )}
                        </div>

                        {/* Right: Actions (Markdown, Copy, Save) */}
                        <div className="flex items-center gap-1 ml-2">
                            <button
                                className="action-icon-btn"
                                onClick={() => setShowMarkdown(!showMarkdown)}
                                title={showMarkdown ? "Disable Markdown Preview" : "Enable Markdown Preview"}
                            >
                                {showMarkdown ? <FileText size={16} /> : <Code size={16} />}
                            </button>
                            <button
                                className="action-icon-btn"
                                onClick={handleCopyContent}
                                title="Copy Content"
                            >
                                <Copy size={16} />
                            </button>
                            <button
                                className={clsx("action-icon-btn", { "highlight": isDirty })}
                                onClick={handleSave}
                                title="Save (Ctrl+S)"
                                disabled={!activeFile.path}
                            >
                                <Save size={16} />
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Content Area */}
            <div className="artifact-content relative h-full">
                {activeTab === 'notebook' ? (
                    <NotebookViewer
                        notebookName={notebookData?.name || 'Untitled'}
                        cells={notebookData?.cells || []}
                        activeCellId={notebookData?.activeCellId}
                        isLoading={false}
                        isEmpty={!notebookData}
                        notebooks={availableNotebooks}
                        kernelName={notebookData?.kernel || 'python3'}
                        onSelectNotebook={onSelectNotebook}
                        onRefresh={onRefreshNotebooks}
                        onCloseNotebook={notebookData ? onCloseNotebook : null}
                        onCreateNotebook={handleCreateNotebook}
                        onStopKernel={notebookData ? (nb) => handleKernelAction(nb, 'stop') : null}
                        onRestartKernel={notebookData ? (nb) => handleKernelAction(nb, 'restart') : null}
                        onAddCell={handleAddCell}
                        onDeleteCell={handleDeleteCell}
                        onExecuteCell={onExecuteCell}
                        onUpdateCell={onUpdateCell}
                        onRunAll={onRunAllCells}
                        isRunningAll={isRunningAllCells}
                    />
                ) : activeTab === 'memory' ? (
                    <MemoryPanel
                        taskId={taskId}
                        onRefresh={() => setRefreshKey(prev => prev + 1)}
                    />
                ) : activeTab === 'workspace' ? (
                    <div className="file-explorer-root">
                        {/* Toolbar */}
                        <div className="file-toolbar">
                            <div className="file-toolbar-left">
                                <div className="file-search-container">
                                    <Search size={14} className="file-search-icon" />
                                    <input
                                        type="text"
                                        className="file-search-input"
                                        placeholder="Search files..."
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                    />
                                    {searchQuery && (
                                        <button
                                            className="file-search-clear"
                                            onClick={() => setSearchQuery('')}
                                        >
                                            <X size={12} />
                                        </button>
                                    )}
                                </div>
                            </div>

                            <div className="file-toolbar-actions">
                                <button
                                    className="file-action-btn"
                                    onClick={handleCreateFile}
                                    title="New File"
                                >
                                    <FilePlus size={14} />
                                </button>
                                <button
                                    className="file-action-btn"
                                    onClick={handleCreateFolder}
                                    title="New Folder"
                                >
                                    <FolderPlus size={14} />
                                </button>
                                <button
                                    className="file-action-btn"
                                    onClick={() => fileInputRef.current?.click()}
                                    title="Upload File"
                                >
                                    <Upload size={14} />
                                </button>
                                <button
                                    className={clsx("file-action-btn", { active: showHiddenFiles })}
                                    onClick={() => setShowHiddenFiles(!showHiddenFiles)}
                                    title={showHiddenFiles ? "Hide Hidden Files" : "Show Hidden Files"}
                                >
                                    {showHiddenFiles ? <Eye size={14} /> : <EyeOff size={14} />}
                                </button>
                            </div>
                        </div>

                        {/* File Tree */}
                        <div
                            className={clsx("file-tree-wrapper", {
                                "bg-white/5 border-2 border-dashed border-accent-secondary": isDragOver
                            })}
                            onDrop={handleDrop}
                            onDragOver={handleDragOver}
                            onDragLeave={handleDragLeave}
                        >
                            {isDragOver && (
                                <div className="drop-overlay">
                                    <Upload size={48} className="drop-overlay-icon" />
                                    <span className="drop-overlay-text">Drop Files to Upload</span>
                                </div>
                            )}

                            {uploading && (
                                <div className="absolute top-0 left-0 right-0 h-1 bg-accent-secondary/20 overflow-hidden z-20">
                                    <div className="h-full bg-accent-secondary animate-pulse w-full"></div>
                                </div>
                            )}

                            <FileTree
                                taskId={taskId || 'default'}
                                onFileSelect={handleFileSelect}
                                refreshKey={refreshKey}
                                onMoveItem={handleMoveItem}
                                selectedPath={selectedPath}
                                searchQuery={searchQuery}
                                onRename={handleRename}
                                onDelete={handleDelete}
                                onCopy={handleCopy}
                                taskFolders={taskFolders}
                                activeTaskFolder={activeTaskDisplayId ? `task_${activeTaskDisplayId}` : null}
                                showHiddenFiles={showHiddenFiles}
                            />
                        </div>

                        <input
                            type="file"
                            ref={fileInputRef}
                            className="hidden"
                            multiple
                            onChange={(e) => {
                                if (e.target.files && e.target.files.length > 0) {
                                    // Upload all selected files to active task's files/ folder
                                    Array.from(e.target.files).forEach(file => {
                                        uploadFile(file); // Uses default task files path
                                    });
                                    // Reset input so same files can be selected again
                                    e.target.value = '';
                                }
                            }}
                        />
                    </div>
                ) : previewType === 'image' && previewUrl ? (
                    // Image Viewer
                    <div className="media-viewer">
                        <div className="media-viewer-content">
                            <img
                                src={previewUrl}
                                alt={activeFile.name}
                                className="preview-image"
                            />
                        </div>
                        <div className="media-viewer-toolbar">
                            <span className="media-info">
                                <Image size={14} />
                                {activeFile.name}
                            </span>
                            <a
                                href={previewUrl}
                                download={activeFile.name}
                                className="media-download-btn"
                            >
                                <Download size={14} />
                                Download
                            </a>
                        </div>
                    </div>
                ) : previewType === 'pdf' && previewUrl ? (
                    // PDF Viewer
                    <div className="media-viewer">
                        <iframe
                            src={previewUrl}
                            className="pdf-viewer"
                            title={activeFile.name}
                        />
                        <div className="media-viewer-toolbar">
                            <span className="media-info">
                                <FileText size={14} />
                                {activeFile.name}
                            </span>
                            <a
                                href={previewUrl}
                                download={activeFile.name}
                                className="media-download-btn"
                            >
                                <Download size={14} />
                                Download
                            </a>
                        </div>
                    </div>
                ) : (
                    // Text Editor OR Markdown Preview
                    activeTab === 'editor' && showMarkdown && activeFile.name.toLowerCase().endsWith('.md') ? (
                        <div
                            className="code-editor markdown-preview p-6 h-full text-text-primary cursor-text"
                            onDoubleClick={() => setShowMarkdown(false)}
                            title="Double-click to edit"
                        >
                            <div className="markdown-content max-w-4xl mx-auto">
                                <ReactMarkdown
                                    remarkPlugins={[remarkGfm, remarkMath]}
                                    rehypePlugins={[rehypeHighlight, rehypeKatex]}
                                    components={{
                                        pre: PreBlock
                                    }}
                                >
                                    {content}
                                </ReactMarkdown>
                            </div>
                        </div>
                    ) : (
                        <textarea
                            className="code-editor scroll-thin"
                            value={content || ""}
                            onChange={handleContentChange}
                            onKeyDown={handleKeyDown}
                            spellCheck="false"
                            placeholder={activeFile.path ? "" : "Select a file to edit..."}
                            autoFocus
                        />
                    )
                )}
            </div>
        </div>
    );
}
