import { Sparkles } from 'lucide-react';
import './FollowUpChips.css';

/**
 * Follow-up suggestion chips shown after AI responses.
 * Extracts suggestions from synthesis content or provides defaults.
 */
export default function FollowUpChips({ suggestions = [], onSelect, disabled = false }) {
    if (!suggestions.length) return null;

    return (
        <div className="followup-chips">
            <Sparkles size={14} className="followup-icon" />
            {suggestions.map((text, i) => (
                <button
                    key={i}
                    className="followup-chip"
                    onClick={() => onSelect(text)}
                    disabled={disabled}
                    title={text}
                >
                    {text}
                </button>
            ))}
        </div>
    );
}
