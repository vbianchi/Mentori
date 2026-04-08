import { useState } from 'react';
import { Edit2, Trash2, Settings, Save, Plus, LogOut, Shield, GripVertical, Sun, Moon } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import clsx from 'clsx';
import IconButton from '../primitives/IconButton';
import Button from '../primitives/Button';
import { useTheme } from '../../hooks/useTheme';
import './Sidebar.css';

/**
 * Sidebar Component
 * Displays navigation and task list with drag-to-reorder.
 * Files/Workspace moved to right panel.
 * Connection status in Sidebar footer.
 */
export default function Sidebar({ tasks = [], activeTaskId, onSelectTask, onCreateTask, onDeleteTask, onRenameTask, onReorderTask, user, onLogout, onAdminClick, connectionStatus = { backend: 'connected', tools: 'error' } }) {
    const navigate = useNavigate();
    const { theme, toggleTheme } = useTheme();
    const [draggedTaskId, setDraggedTaskId] = useState(null);
    const [dragOverTaskId, setDragOverTaskId] = useState(null);

    const handleDragStart = (e, taskId) => {
        setDraggedTaskId(taskId);
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', taskId);
    };

    const handleDragEnd = () => {
        setDraggedTaskId(null);
        setDragOverTaskId(null);
    };

    const handleDragOver = (e, taskId) => {
        e.preventDefault();
        if (draggedTaskId && draggedTaskId !== taskId) {
            setDragOverTaskId(taskId);
        }
    };

    const handleDragLeave = () => {
        setDragOverTaskId(null);
    };

    const handleDrop = (e, targetTaskId) => {
        e.preventDefault();
        if (draggedTaskId && draggedTaskId !== targetTaskId && onReorderTask) {
            onReorderTask(draggedTaskId, targetTaskId);
        }
        setDraggedTaskId(null);
        setDragOverTaskId(null);
    };
    return (
        <div className="sidebar-container">

            {/* 1. Tasks List */}
            <div className="nav-group pb-4 mb-4 border-b border-white/20">
                <div className="flex justify-between items-center pr-2 mb-2">
                    <label className="nav-label mb-0 flex-1">
                        TASKS - Total: {tasks.length}
                    </label>
                    <IconButton
                        icon={<Plus size={14} />}
                        size="sm"
                        variant="ghost"
                        onClick={onCreateTask}
                        title="New Task"
                        className="text-accent-primary hover:bg-white/10"
                    />
                </div>

                <div className="task-list scroll-thin">
                    {tasks.length === 0 ? (
                        <div className="empty-state">No active tasks</div>
                    ) : (
                        tasks.map((task, index) => (
                            <div
                                key={task.id}
                                onClick={() => onSelectTask(task.id)}
                                className={clsx('sidebar-task-item group', {
                                    active: activeTaskId === task.id,
                                    dragging: draggedTaskId === task.id,
                                    'drag-over': dragOverTaskId === task.id
                                })}
                                draggable
                                onDragStart={(e) => handleDragStart(e, task.id)}
                                onDragEnd={handleDragEnd}
                                onDragOver={(e) => handleDragOver(e, task.id)}
                                onDragLeave={handleDragLeave}
                                onDrop={(e) => handleDrop(e, task.id)}
                            >
                                <div
                                    className="task-drag-handle"
                                    onMouseDown={(e) => e.stopPropagation()}
                                    title="Drag to reorder"
                                >
                                    <GripVertical size={12} />
                                </div>

                                <div className="task-name-container">
                                    <span className="task-title">{task.name || `Unnamed Task`}</span>
                                </div>

                                <div className="task-actions">
                                    <IconButton
                                        variant="ghost"
                                        size="sm"
                                        icon={<Edit2 size={12} />}
                                        title="Rename"
                                        onClick={(e) => { e.stopPropagation(); onRenameTask(task.id); }}
                                    />
                                    <IconButton
                                        variant="ghost"
                                        size="sm"
                                        icon={<Trash2 size={12} />}
                                        title="Delete"
                                        className="text-error"
                                        onClick={(e) => { e.stopPropagation(); onDeleteTask(task.id); }}
                                    />
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>



            {/* 5. User & Status Footer */}
            <div className="sidebar-footer">
                {/* User Profile Badge */}
                <div className="user-badge">
                    <div className="user-profile-info">
                        <div className="user-main-identity" title={user?.email}>
                            {user?.first_name ? (
                                <>
                                    <span className="user-name">{user.first_name} {user.last_name}</span>
                                    <span className="user-divider">-</span>
                                    <span className="user-email">{user.email}</span>
                                </>
                            ) : (
                                <span className="user-email">{user?.email || 'User'}</span>
                            )}
                        </div>
                        {user?.id && <div className="user-id-badge">{user.id}</div>}
                    </div>

                    <div className="user-badge-actions">
                        <button
                            className="sidebar-action-btn"
                            onClick={toggleTheme}
                            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
                        >
                            {theme === 'dark' ? <Sun size={14} /> : <Moon size={14} />}
                        </button>

                        <div
                            className="user-action-btn settings"
                            onClick={() => navigate('/settings')}
                            title="User Settings"
                        >
                            <Settings size={14} />
                        </div>

                        {/* Admin Action */}
                        {user?.role === 'admin' && (
                            <div
                                className="user-action-btn admin"
                                onClick={onAdminClick}
                                title="Admin Panel"
                            >
                                <Shield size={14} />
                            </div>
                        )}

                        {/* Logout Action */}
                        <div
                            className="user-action-btn logout"
                            onClick={onLogout}
                            title="Logout"
                        >
                            <LogOut size={14} />
                        </div>
                    </div>
                </div>

                {/* Connection Status (Text Only + Separator) */}
                <div className="status-row mt-3 pt-3 border-t border-white/20">
                    <div className="flex items-center gap-2">
                        <span>Backend</span>
                    </div>
                    <span className={clsx("status-dot", connectionStatus.backend === 'connected' ? 'success' : 'error')}></span>
                </div>
                <div className="status-row">
                    <div className="flex items-center gap-2">
                        <span>Tools</span>
                    </div>
                    <span className={clsx("status-dot", connectionStatus.tools === 'connected' ? 'success' : 'error')}></span>
                </div>
            </div>
        </div>
    );
}
