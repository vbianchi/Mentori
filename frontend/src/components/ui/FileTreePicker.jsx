import { useState, useEffect } from 'react';
import {
    Folder, FolderOpen, File, FileCode, FileImage, FileText, FileJson,
    FileSpreadsheet, ChevronRight, FolderX
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
        '.pdf': { Icon: FileText, className: 'pdf' },
        '.png': { Icon: FileImage, className: 'image' },
        '.jpg': { Icon: FileImage, className: 'image' },
        '.jpeg': { Icon: FileImage, className: 'image' },
    };

    const iconConfig = iconMap[ext] || { Icon: File, className: 'generic' };
    const { Icon, className } = iconConfig;

    return <Icon size={14} className={`file-icon ${className}`} />;
};

/**
 * Recursive function to get all file paths from a folder node
 */
const getAllFilePaths = (node) => {
    if (node.type === 'file') {
        return [node.path];
    }

    if (node.type === 'folder' && node.children) {
        return node.children.flatMap(child => getAllFilePaths(child));
    }

    return [];
};

/**
 * FileTreePicker Item Component with Checkboxes
 */
export const FileTreePickerItem = ({
    node,
    depth = 0,
    selectedPaths,
    onToggleSelection,
}) => {
    const [isOpen, setIsOpen] = useState(false);
    const isFolder = node.type === 'folder';
    const isSelected = selectedPaths.includes(node.path);

    // Check if this folder has any selected children
    const hasSelectedChildren = isFolder && node.children?.some(child => {
        if (child.type === 'file') {
            return selectedPaths.includes(child.path);
        }
        // Recursively check folder children
        return getAllFilePaths(child).some(path => selectedPaths.includes(path));
    });

    const handleCheckboxChange = (e) => {
        e.stopPropagation();

        if (isFolder) {
            // Get all file paths in this folder
            const folderFiles = getAllFilePaths(node);
            onToggleSelection(node.path, folderFiles, isSelected);
        } else {
            onToggleSelection(node.path, [node.path], isSelected);
        }
    };

    const handleClick = (e) => {
        e.stopPropagation();
        if (isFolder) {
            setIsOpen(!isOpen);
        }
    };

    return (
        <div>
            <div
                className={clsx('file-tree-item', {
                    'selected': isSelected || hasSelectedChildren,
                    'folder': isFolder
                })}
                data-depth={depth}
                onClick={handleClick}
            >
                {/* Checkbox */}
                <input
                    type="checkbox"
                    checked={isSelected || hasSelectedChildren}
                    onChange={handleCheckboxChange}
                    onClick={(e) => e.stopPropagation()}
                    className="mr-2"
                    style={{ cursor: 'pointer' }}
                />

                {isFolder ? (
                    <div
                        className={clsx('file-expand-icon', { expanded: isOpen })}
                        onClick={(e) => {
                            e.stopPropagation();
                            setIsOpen(!isOpen);
                        }}
                    >
                        <ChevronRight size={14} />
                    </div>
                ) : (
                    <span style={{ width: '14px' }} />
                )}

                {getFileIcon(node, isOpen)}

                <div className="file-item-content">
                    <span className="file-item-name">{node.name}</span>
                    {isFolder && node.children && (
                        <span className="text-xs text-muted ml-2">
                            ({node.children.length} items)
                        </span>
                    )}
                </div>
            </div>

            {isFolder && isOpen && node.children && (
                <div className="folder-content">
                    {node.children.map((child, idx) => (
                        <FileTreePickerItem
                            key={`${child.path}-${idx}`}
                            node={child}
                            depth={depth + 1}
                            selectedPaths={selectedPaths}
                            onToggleSelection={onToggleSelection}
                        />
                    ))}
                    {node.children.length === 0 && (
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
 * Main FileTreePicker Component
 */
export default function FileTreePicker({ taskId, selectedPaths, onSelectionChange }) {
    const [files, setFiles] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchFiles = async () => {
            setLoading(true);
            const token = localStorage.getItem("mentori_token");
            try {
                const endpoint = taskId || 'default';
                const res = await fetch(`${config.API_BASE_URL}/tasks/${endpoint}/files`, {
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
    }, [taskId]);

    const handleToggleSelection = (nodePath, filePaths, isCurrentlySelected) => {
        let newSelection;

        if (isCurrentlySelected) {
            // Remove these paths
            newSelection = selectedPaths.filter(path => !filePaths.includes(path));
        } else {
            // Add these paths (avoiding duplicates)
            const pathsToAdd = filePaths.filter(path => !selectedPaths.includes(path));
            newSelection = [...selectedPaths, ...pathsToAdd];
        }

        onSelectionChange(newSelection);
    };

    if (loading && files.length === 0) {
        return (
            <div className="file-skeleton-container">
                {[...Array(6)].map((_, i) => (
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
                <FolderX size={48} className="empty-state-icon" />
                <div className="empty-state-title">Error Loading Files</div>
                <div className="empty-state-text">{error}</div>
            </div>
        );
    }

    if (files.length === 0) {
        return (
            <div className="file-empty-state">
                <FolderX size={48} className="empty-state-icon" />
                <div className="empty-state-title">Workspace is Empty</div>
                <div className="empty-state-text">Upload files to your workspace first</div>
            </div>
        );
    }

    return (
        <div className="file-tree-container" style={{ maxHeight: '400px', overflowY: 'auto' }}>
            {files.map((node, idx) => (
                <FileTreePickerItem
                    key={`${node.path}-${idx}`}
                    node={node}
                    selectedPaths={selectedPaths}
                    onToggleSelection={handleToggleSelection}
                />
            ))}
        </div>
    );
}
