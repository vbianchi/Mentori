import { useState, useEffect } from 'react';
import {
    Folder, FolderOpen, File, FileCode, FileImage, FileText, FileJson,
    FileSpreadsheet, ChevronRight, FolderX, Database, Edit2, Trash2, Copy, ArrowUpRight
} from 'lucide-react';
import clsx from 'clsx';
import config from '../../config';
import '../panels/FileExplorer.css';

/**
 * Get appropriate icon for file type
 */
const getFileIcon = (node, isOpen = false) => {
    if (node.type === 'folder') {
        const IconComponent = isOpen ? FolderOpen : Folder;
        return <IconComponent size={14} className="file-icon folder" />;
    }

    const ext = node.extension?.toLowerCase();
    const iconMap = {
        '.py': { Icon: FileCode, className: 'python' },
        '.js': { Icon: FileCode, className: 'javascript' },
        '.jsx': { Icon: FileCode, className: 'javascript' },
        '.ts': { Icon: FileCode, className: 'typescript' },
        '.tsx': { Icon: FileCode, className: 'typescript' },
        '.json': { Icon: FileJson, className: 'json' },
        '.csv': { Icon: FileSpreadsheet, className: 'csv' },
        '.xlsx': { Icon: FileSpreadsheet, className: 'csv' },
        '.md': { Icon: FileText, className: 'markdown' },
        '.txt': { Icon: FileText, className: 'markdown' },
        '.png': { Icon: FileImage, className: 'image' },
        '.jpg': { Icon: FileImage, className: 'image' },
        '.jpeg': { Icon: FileImage, className: 'image' },
        '.gif': { Icon: FileImage, className: 'image' },
        '.svg': { Icon: FileImage, className: 'image' },
        '.sql': { Icon: Database, className: 'database' },
        '.db': { Icon: Database, className: 'database' },
    };

    const config = iconMap[ext] || { Icon: File, className: 'generic' };
    const { Icon, className } = config;

    return <Icon size={14} className={`file-icon ${className}`} />;
};

/**
 * Format file size for display
 */
const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
};

/**
 * Format modified date for display
 */
const formatModifiedDate = (dateString) => {
    if (!dateString) return '';

    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString();
};

/**
 * Recursive Tree Item Component
 */
export const FileTreeItem = ({
    node,
    depth = 0,
    onFileClick,
    onMoveItem,
    selectedPath,
    searchQuery,
    onRename,
    onDelete,
    onCopy,
    taskFolders = [], // Array of task folder paths that can't be deleted
    activeTaskFolder = null, // The currently active task folder to highlight
    showHiddenFiles = false, // Whether to show hidden files (starting with .)
    expandedPaths, // Set of expanded paths (lifted state)
    onToggle // Function to toggle path (lifted state state)
}) => {
    // Use centralized state if available, fall back to local
    const isControlled = expandedPaths !== undefined;
    const [localIsOpen, setLocalIsOpen] = useState(false);
    const [isDragOver, setIsDragOver] = useState(false);
    const [isDragging, setIsDragging] = useState(false);

    const isFolder = node.type === 'folder';
    const isSelected = selectedPath === node.path;
    const isTaskFolder = taskFolders.includes(node.path);
    const isActiveTaskFolder = activeTaskFolder && node.path === activeTaskFolder;

    const isOpen = isControlled ? expandedPaths.has(node.path) : localIsOpen;

    const handleClick = (e) => {
        e.stopPropagation();
        if (isFolder) {
            if (isControlled) {
                onToggle(node.path);
            } else {
                setLocalIsOpen(!localIsOpen);
            }
        } else {
            onFileClick && onFileClick(node);
        }
    };

    // Drag & Drop handlers
    const handleDragStart = (e) => {
        e.dataTransfer.setData("application/mentori-file", JSON.stringify(node));
        e.dataTransfer.effectAllowed = "move";
        setIsDragging(true);
        e.stopPropagation();
    };

    const handleDragEnd = () => {
        setIsDragging(false);
    };

    const handleDragOver = (e) => {
        e.preventDefault();
        if (isFolder && !isDragging) {
            setIsDragOver(true);
            // Check if external files or internal move
            if (e.dataTransfer.types.includes('Files')) {
                // External files - allow copy and let bubble up
                e.dataTransfer.dropEffect = "copy";
            } else {
                // Internal move - stop propagation
                e.stopPropagation();
                e.dataTransfer.dropEffect = "move";
            }
        }
    };

    const handleDragLeave = (e) => {
        e.preventDefault();
        // Only stop propagation for internal moves
        if (!e.dataTransfer.types.includes('Files')) {
            e.stopPropagation();
        }
        setIsDragOver(false);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setIsDragOver(false);

        // Check if external files are being dropped
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            // External files - let the event bubble up to parent handler
            console.log('External files detected in FileTreeItem, letting bubble up');
            return;
        }

        // Internal move operation
        e.stopPropagation();
        const data = e.dataTransfer.getData("application/mentori-file");
        if (!data) return;

        try {
            const sourceNode = JSON.parse(data);
            if (sourceNode.path !== node.path && isFolder) {
                onMoveItem && onMoveItem(sourceNode, node);
            }
        } catch (err) {
            console.error("Drop Parse Error", err);
        }
    };

    // Auto-expand folders when searching
    useEffect(() => {
        if (searchQuery && isFolder && node.children) {
            const hasMatch = node.children.some(child =>
                child.name.toLowerCase().includes(searchQuery.toLowerCase())
            );
            if (hasMatch && !isOpen) {
                // Determine how to open based on mode
                if (expandedPaths && onToggle) {
                    // Only toggle if not already open (checked above)
                    onToggle(node.path);
                } else {
                    setLocalIsOpen(true);
                }
            }
        }
    }, [searchQuery, isFolder, node.children, isOpen, expandedPaths, onToggle]);

    return (
        <div>
            <div
                className={clsx('file-tree-item', {
                    'selected': isSelected,
                    'drag-over': isDragOver,
                    'dragging': isDragging,
                    'folder': isFolder,
                    'active-task': isActiveTaskFolder
                })}
                data-depth={depth}
                onClick={handleClick}
                draggable
                onDragStart={handleDragStart}
                onDragEnd={handleDragEnd}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
            >
                {isFolder ? (
                    <div
                        className={clsx('file-expand-icon', { expanded: isOpen })}
                        onClick={(e) => {
                            e.stopPropagation();
                            if (isControlled) {
                                onToggle(node.path);
                            } else {
                                setLocalIsOpen(!localIsOpen);
                            }
                        }}
                    >
                        <ChevronRight size={14} />
                    </div>
                ) : (
                    <span style={{ width: '14px' }} /> // Spacer for files
                )}

                {getFileIcon(node, isOpen)}

                <div className="file-item-content">
                    <span className="file-item-name">{node.name}</span>

                    {!isFolder && (
                        <div className="file-item-meta">
                            {node.size !== undefined && (
                                <span className="file-size">{formatFileSize(node.size)}</span>
                            )}
                            {node.modified && (
                                <span className="file-modified">{formatModifiedDate(node.modified)}</span>
                            )}
                        </div>
                    )}

                    {/* Inline Action Icons */}
                    <div className="file-item-actions">
                        <button
                            className="file-item-action-btn"
                            onClick={(e) => {
                                e.stopPropagation();
                                const text = `[${node.name}]`;
                                window.dispatchEvent(new CustomEvent('mentori:insert-chat-text', { detail: { text } }));
                            }}
                            title="Insert Name in Chat"
                        >
                            <ArrowUpRight size={12} />
                        </button>
                        <button
                            className="file-item-action-btn"
                            onClick={(e) => {
                                e.stopPropagation();
                                onRename && onRename(node);
                            }}
                            title="Rename"
                        >
                            <Edit2 size={12} />
                        </button>
                        <button
                            className="file-item-action-btn"
                            onClick={(e) => {
                                e.stopPropagation();
                                onCopy && onCopy(node);
                            }}
                            title="Copy"
                        >
                            <Copy size={12} />
                        </button>
                        {!isTaskFolder && (
                            <button
                                className="file-item-action-btn danger"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onDelete && onDelete(node);
                                }}
                                title="Delete"
                            >
                                <Trash2 size={12} />
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {isFolder && isOpen && node.children && (
                <div className="folder-content">
                    {node.children
                        .filter(child => showHiddenFiles || !child.name.startsWith('.'))
                        .map((child, idx) => (
                            <FileTreeItem
                                key={`${child.path}-${idx}`}
                                node={child}
                                depth={depth + 1}
                                onFileClick={onFileClick}
                                onMoveItem={onMoveItem}
                                selectedPath={selectedPath}
                                searchQuery={searchQuery}
                                onRename={onRename}
                                onDelete={onDelete}
                                onCopy={onCopy}
                                taskFolders={taskFolders}
                                activeTaskFolder={activeTaskFolder}
                                showHiddenFiles={showHiddenFiles}
                                expandedPaths={expandedPaths}
                                onToggle={onToggle}
                            />
                        ))}
                    {node.children.filter(child => showHiddenFiles || !child.name.startsWith('.')).length === 0 && (
                        <div
                            className="file-tree-item"
                            data-depth={depth + 1}
                            style={{ cursor: 'default', opacity: 0.5 }}
                        >
                            <span style={{ width: '14px' }} />
                            <FolderX size={14} className="file-icon" style={{ opacity: 0.3 }} />
                            <span className="file-item-name" style={{ fontStyle: 'italic', fontSize: '0.75rem' }}>
                                Empty folder
                            </span>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

/**
 * Main FileTree Component
 */
export default function FileTree({
    taskId,
    onFileSelect,
    refreshKey,
    onMoveItem,
    selectedPath,
    searchQuery = '',
    onRename,
    onDelete,
    onCopy,
    taskFolders = [],
    activeTaskFolder = null,
    showHiddenFiles = false
}) {
    const [files, setFiles] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [isRootDragOver, setIsRootDragOver] = useState(false);

    // State for expanded folders (persisted in localStorage)
    const [expandedPaths, setExpandedPaths] = useState(() => {
        try {
            const saved = localStorage.getItem('mentori_expanded_paths');
            return new Set(saved ? JSON.parse(saved) : []);
        } catch (e) {
            console.error("Failed to load expanded paths", e);
            return new Set();
        }
    });

    const handleToggleExpand = (path) => {
        const newSet = new Set(expandedPaths);
        if (newSet.has(path)) {
            newSet.delete(path);
        } else {
            newSet.add(path);
        }
        setExpandedPaths(newSet);
        try {
            localStorage.setItem('mentori_expanded_paths', JSON.stringify([...newSet]));
        } catch (e) {
            console.error("Failed to save expanded paths", e);
        }
    };

    useEffect(() => {
        // Allow viewing files even without task selected
        // Backend stores files at user level, not task level
        const fetchFiles = async () => {
            setLoading(true);
            const token = localStorage.getItem("mentori_token");
            try {
                // Use current task or 'default' for user-level browsing
                const endpoint = taskId || 'default';
                // Pass include_hidden parameter to backend
                const url = `${config.API_BASE_URL}/tasks/${endpoint}/files?include_hidden=${showHiddenFiles}`;
                const res = await fetch(url, {
                    headers: { "Authorization": `Bearer ${token}` }
                });
                if (res.ok) {
                    const data = await res.json();
                    setFiles(data);
                    setError(null);
                } else {
                    setError("Failed to load files");
                }
            } catch (e) {
                setError(e.message);
            } finally {
                setLoading(false);
            }
        };

        fetchFiles();
    }, [taskId, refreshKey, showHiddenFiles]);

    // Filter files based on search query and hidden files setting
    const filterTree = (nodes) => {
        return nodes.reduce((acc, node) => {
            // Filter hidden files unless showHiddenFiles is enabled
            if (!showHiddenFiles && node.name.startsWith('.')) {
                return acc;
            }

            if (node.type === 'folder') {
                const filteredChildren = filterTree(node.children || []);
                // If searching, only include if matches or has matching children
                if (searchQuery) {
                    const query = searchQuery.toLowerCase();
                    if (filteredChildren.length > 0 || node.name.toLowerCase().includes(query)) {
                        acc.push({ ...node, children: filteredChildren });
                    }
                } else {
                    acc.push({ ...node, children: filteredChildren });
                }
            } else {
                // If searching, only include if matches
                if (searchQuery) {
                    const query = searchQuery.toLowerCase();
                    if (node.name.toLowerCase().includes(query)) {
                        acc.push(node);
                    }
                } else {
                    acc.push(node);
                }
            }
            return acc;
        }, []);
    };

    const filteredFiles = filterTree(files);

    if (loading && files.length === 0) {
        return (
            <div className="file-skeleton-container">
                {[...Array(8)].map((_, i) => (
                    <div key={i} className="file-skeleton">
                        <div className="skeleton-icon" />
                        <div className={`skeleton-text ${i % 3 === 0 ? 'long' : 'short'}`} />
                    </div>
                ))}
            </div>
        );
    }

    if (error) {
        return (
            <div className="file-empty-state">
                <FolderX size={64} className="empty-state-icon" />
                <div className="empty-state-title">Error Loading Files</div>
                <div className="empty-state-text">{error}</div>
            </div>
        );
    }

    if (files.length === 0) {
        return (
            <div className="file-empty-state">
                <FolderX size={64} className="empty-state-icon" />
                <div className="empty-state-title">Workspace is Empty</div>
                <div className="empty-state-text">Upload files or create new ones to get started</div>
            </div>
        );
    }

    if (searchQuery && filteredFiles.length === 0) {
        return (
            <div className="file-empty-state">
                <FolderX size={64} className="empty-state-icon" />
                <div className="empty-state-title">No Results Found</div>
                <div className="empty-state-text">No files match "{searchQuery}"</div>
            </div>
        );
    }

    // Root drop zone handlers
    const handleRootDragOver = (e) => {
        e.preventDefault();
        setIsRootDragOver(true);
        // Check if external files or internal move
        if (e.dataTransfer.types.includes('Files')) {
            // External files - allow copy and let bubble up
            e.dataTransfer.dropEffect = "copy";
        } else {
            // Internal move - stop propagation
            e.stopPropagation();
            e.dataTransfer.dropEffect = "move";
        }
    };

    const handleRootDragLeave = (e) => {
        // Only set to false if we're leaving the container itself
        if (e.target === e.currentTarget) {
            setIsRootDragOver(false);
        }
    };

    const handleRootDrop = (e) => {
        e.preventDefault();
        setIsRootDragOver(false);

        // Check if external files are being dropped
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            // External files - let the event bubble up to parent handler
            console.log('External files detected in root, letting bubble up');
            return;
        }

        // Internal move operation
        e.stopPropagation();
        const data = e.dataTransfer.getData("application/mentori-file");
        if (!data) return;

        try {
            const sourceNode = JSON.parse(data);
            // Create a fake root node
            const rootNode = {
                name: 'root',
                type: 'folder',
                path: '.'
            };
            onMoveItem && onMoveItem(sourceNode, rootNode);
        } catch (err) {
            console.error("Root drop error", err);
        }
    };

    return (
        <div
            className={clsx("file-tree-container", { 'drag-over-root': isRootDragOver })}
            onDragOver={handleRootDragOver}
            onDragLeave={handleRootDragLeave}
            onDrop={handleRootDrop}
        >
            {filteredFiles.map((node, idx) => (
                <FileTreeItem
                    key={`${node.path}-${idx}`}
                    node={node}
                    onFileClick={onFileSelect}
                    onMoveItem={onMoveItem}
                    selectedPath={selectedPath}
                    searchQuery={searchQuery}
                    onRename={onRename}
                    onDelete={onDelete}
                    onCopy={onCopy}
                    taskFolders={taskFolders}
                    activeTaskFolder={activeTaskFolder}
                    showHiddenFiles={showHiddenFiles}
                    expandedPaths={expandedPaths}
                    onToggle={handleToggleExpand}
                />
            ))}
        </div>
    );
}
