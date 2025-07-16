import { h } from 'preact';
import { useState, useRef, useCallback } from 'preact/hooks';

// --- NEW: Use the window's hostname to determine the backend API address ---
const API_BASE_URL = `http://${window.location.hostname}:8766`;

export const useWorkspace = (initialPath) => {
    const [items, setItems] = useState([]);
    const [currentPath, setCurrentPath] = useState(initialPath || '');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const [selectedFile, setSelectedFile] = useState(null);
    const [fileContent, setFileContent] = useState('');
    const [isFileLoading, setIsFileLoading] = useState(false);

    const [isDragOver, setIsDragOver] = useState(false);
    const dragCounter = useRef(0);
    const fileInputRef = useRef(null);

    const fetchFiles = useCallback(async (path) => {
        if (!path) return;
        setLoading(true);
        setError(null);
        try {
            // --- MODIFIED: Use dynamic base URL ---
            const response = await fetch(`${API_BASE_URL}/api/workspace/items?path=${path}`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to fetch items');
            }
            const data = await response.json();
            const sortedItems = (data.items || []).sort((a, b) => {
                if (a.type === 'directory' && b.type !== 'directory') return -1;
                if (a.type !== 'directory' && b.type === 'directory') return 1;
                return a.name.localeCompare(b.name);
            });
            setItems(sortedItems);
        } catch (err) {
            console.error("Failed to fetch workspace items:", err);
            setError(err.message);
            setItems([]);
        } finally {
            setLoading(false);
        }
    }, []);

    const selectAndFetchFile = async (file) => {
        if (!currentPath || !file) return;

        setSelectedFile(file);
        setFileContent('');

        const extension = file.name.split('.').pop().toLowerCase();
        const isImage = ['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'].includes(extension);

        if (isImage) {
            setIsFileLoading(false);
            return;
        }

        setIsFileLoading(true);
        try {
            // --- MODIFIED: Use dynamic base URL ---
            const response = await fetch(`${API_BASE_URL}/file-content?path=${currentPath}&filename=${file.name}`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to fetch file content');
            }
            const textContent = await response.text();
            setFileContent(textContent);
        } catch (err) {
            console.error("Failed to fetch file content:", err);
            setFileContent(`Error loading file: ${err.message}`);
        } finally {
            setIsFileLoading(false);
        }
    };

    const handleNavigation = (item) => {
        if (item.type === 'directory') {
            const newPath = `${currentPath}/${item.name}`;
            setCurrentPath(newPath);
            setSelectedFile(null);
        } else {
            selectAndFetchFile(item);
        }
    };

    const handleBreadcrumbNav = (path) => {
        setCurrentPath(path);
        setSelectedFile(null);
    };

    const deleteItem = async (item) => {
        if (!confirm(`Are you sure you want to delete '${item.name}'?`)) return;
        
        const itemFullPath = `${currentPath}/${item.name}`;
        setLoading(true);
        setError(null);
        try {
            // --- MODIFIED: Use dynamic base URL ---
            const response = await fetch(`${API_BASE_URL}/api/workspace/items?path=${itemFullPath}`, { method: 'DELETE' });
            if (!response.ok) throw new Error((await response.json()).error || 'Failed to delete item');
            if (selectedFile && selectedFile.name === item.name) {
                setSelectedFile(null);
            }
            await fetchFiles(currentPath);
        } catch (err) {
            console.error("Failed to delete item:", err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };
    
    const startInlineCreate = (type) => {
        if (items.some(item => item.isEditing)) return;
        
        const placeholderItem = {
            name: '',
            type: type,
            isEditing: true,
            isNew: true,
        };
        setItems(prevItems => [...prevItems, placeholderItem]);
    };

    const handleConfirmName = async (tempName, finalName, type, isNew) => {
        setItems(prevItems => prevItems.filter(item => item.name !== tempName));

        if (!finalName || finalName.trim() === '') {
            console.log("Creation/Rename cancelled.");
            return;
        }
        
        const newPath = `${currentPath}/${finalName.trim()}`;
        
        if (isNew) {
            // --- MODIFIED: Use dynamic base URL ---
            const endpoint = type === 'folder' ? `${API_BASE_URL}/api/workspace/folders` : `${API_BASE_URL}/api/workspace/files`;
            const body = type === 'folder' ? { path: newPath } : { path: newPath, content: '' };
            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body),
                });
                if (!response.ok) throw new Error((await response.json()).error || `Failed to create ${type}`);
            } catch (err) {
                console.error(`Failed to create ${type}:`, err);
                setError(err.message);
            } finally {
                await fetchFiles(currentPath);
            }
        } else {
             const oldPath = `${currentPath}/${tempName}`;
             try {
                // --- MODIFIED: Use dynamic base URL ---
                const response = await fetch(`${API_BASE_URL}/api/workspace/items`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ old_path: oldPath, new_path: newPath }),
                });
                 if (!response.ok) throw new Error((await response.json()).error || 'Failed to rename item');
            } catch (err) {
                 console.error("Failed to rename item:", err);
                setError(err.message);
            } finally {
                await fetchFiles(currentPath);
            }
        }
    };
    
    const startInlineRename = (itemToRename) => {
        if (items.some(item => item.isEditing)) return;
        setItems(prevItems => prevItems.map(item => 
            item.name === itemToRename.name ? { ...item, isEditing: true } : item
        ));
    };

    const uploadFiles = async (files) => {
        if (!files || files.length === 0 || !currentPath) return;
        
        setItems(prev => {
            const newItems = [...prev];
            Array.from(files).forEach(file => {
                newItems.push({ name: file.name, type: 'file', isLoading: true });
            });
            return newItems;
        });

        await Promise.all(Array.from(files).map(async (file) => {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('workspace_id', currentPath);
            try {
                // --- MODIFIED: Use dynamic base URL ---
                const response = await fetch(`${API_BASE_URL}/upload`, { method: 'POST', body: formData });
                if (!response.ok) throw new Error((await response.json()).error || 'File upload failed');
            } catch (err) {
                console.error(`File upload error for ${file.name}:`, err);
                setError(`Upload failed for ${file.name}: ${err.message}`);
            }
        }));

        if(fileInputRef.current) fileInputRef.current.value = "";
        await fetchFiles(currentPath);
    };

    const handleDragEnter = (e) => { e.preventDefault(); e.stopPropagation(); dragCounter.current++; if (e.dataTransfer.items?.length > 0) setIsDragOver(true); };
    const handleDragLeave = (e) => { e.preventDefault(); e.stopPropagation(); dragCounter.current--; if (dragCounter.current === 0) setIsDragOver(false); };
    const handleDragOver = (e) => { e.preventDefault(); e.stopPropagation(); };
    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragOver(false);
        dragCounter.current = 0;
        if (e.dataTransfer.files?.length > 0) {
            uploadFiles(e.dataTransfer.files);
            e.dataTransfer.clearData();
        }
    };

    const resetWorkspaceViews = () => {
        setItems([]);
        setError(null);
        setSelectedFile(null);
    };

    return {
        items, currentPath, loading, error, selectedFile, setSelectedFile, fileContent, isFileLoading, isDragOver, fileInputRef,
        setCurrentPath, fetchFiles, handleNavigation, handleBreadcrumbNav, deleteItem,
        uploadFiles, handleDragEnter, handleDragLeave, handleDragOver, handleDrop, resetWorkspaceViews,
        startInlineCreate, startInlineRename, handleConfirmName,
    };
};