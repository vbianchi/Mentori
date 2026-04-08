import clsx from 'clsx';
import './PhaseIndicator.css';

/**
 * PhaseIndicator - Shows orchestrator execution phases
 *
 * Displays a horizontal bar showing progress through:
 * Analyzing → Planning → Executing → Synthesizing
 *
 * Each phase has visual states:
 * - completed: green background
 * - active: purple background with pulsing dot
 * - pending: gray background
 */
export const PhaseIndicator = ({ currentPhase }) => {
    const phases = ['analyzing', 'planning', 'executing', 'synthesizing'];
    const currentIdx = phases.indexOf(currentPhase);

    // If phase not found, default to first
    const effectiveIdx = currentIdx === -1 ? 0 : currentIdx;

    return (
        <div className="phase-indicator">
            {phases.map((phase, idx) => (
                <div
                    key={phase}
                    className={clsx('phase', {
                        'completed': idx < effectiveIdx,
                        'active': idx === effectiveIdx,
                        'pending': idx > effectiveIdx
                    })}
                >
                    <span className="phase-dot" />
                    <span className="phase-label">
                        {phase.charAt(0).toUpperCase() + phase.slice(1)}
                    </span>
                </div>
            ))}
        </div>
    );
};

export default PhaseIndicator;
