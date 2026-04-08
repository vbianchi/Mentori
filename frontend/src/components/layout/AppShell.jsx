import config from '../../config';
import { SidebarSizer } from '../ui/SidebarSizer';
import './AppShell.css';

/**
 * AppShell
 * The main layout container for the Agentic IDE.
 *
 * Uses simple flex layout with size-controlled sidebars:
 * - Sidebars have chevron buttons to toggle between small/normal/large
 * - Center panel flexes to fill remaining space
 * - Size state managed in parent (App.jsx)
 *
 * Structure:
 * [ Sidebar (Left) ] [ Center Panel (Feed) ] [ Artifact Panel (Right) ]
 */
export default function AppShell({
    leftSidebarSize,
    setLeftSidebarSize,
    leftSidebarWidth,
    rightSidebarSize,
    setRightSidebarSize,
    rightSidebarWidth,
    sidebar,
    centerPanel,
    rightPanel
}) {
    return (
        <div className="app-shell">
            <div className="shell-layout">
                {/* 1. Left Sidebar */}
                <aside
                    className="shell-sidebar glass-panel"
                    style={{ width: `${leftSidebarWidth}px` }}
                >
                    <div className="sidebar-header">
                        <span className="app-logo">✨ {config.APP_NAME}</span>
                        <SidebarSizer
                            side="left"
                            size={leftSidebarSize}
                            setSize={setLeftSidebarSize}
                        />
                    </div>
                    <div className="sidebar-content scroll-thin">
                        {sidebar}
                    </div>
                </aside>

                {/* 2. Center Panel */}
                <main className="shell-center">
                    {centerPanel}
                </main>

                {/* 3. Right Panel (Artifacts) */}
                <aside
                    className="shell-right glass-panel"
                    style={{ width: `${rightSidebarWidth}px` }}
                >
                    <div className="sidebar-header">
                        <SidebarSizer
                            side="right"
                            size={rightSidebarSize}
                            setSize={setRightSidebarSize}
                        />
                    </div>
                    <div className="sidebar-content scroll-thin">
                        {rightPanel}
                    </div>
                </aside>
            </div>
        </div>
    );
}
