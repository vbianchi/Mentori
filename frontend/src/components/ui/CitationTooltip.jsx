import { useState, useRef, useEffect } from 'react';
import './CitationTooltip.css';

export function CitationTooltip({ number, sources }) {
    const [isOpen, setIsOpen] = useState(false);
    const tooltipRef = useRef(null);
    const btnRef = useRef(null);

    const source = sources?.[number];

    useEffect(() => {
        if (!isOpen) return;
        const handleClick = (e) => {
            if (tooltipRef.current && !tooltipRef.current.contains(e.target) &&
                btnRef.current && !btnRef.current.contains(e.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClick);
        return () => document.removeEventListener('mousedown', handleClick);
    }, [isOpen]);

    return (
        <span className="citation-wrapper">
            <button
                ref={btnRef}
                className={`citation-btn ${source ? 'has-source' : ''}`}
                onClick={() => source && setIsOpen(!isOpen)}
                title={source ? `Source: ${source.file}` : `Citation ${number}`}
            >
                [{number}]
            </button>
            {isOpen && source && (
                <div ref={tooltipRef} className="citation-tooltip">
                    <div className="citation-tooltip-header">
                        <span className="citation-tooltip-file">{source.file}</span>
                        {source.page !== undefined && (
                            <span className="citation-tooltip-page">p. {source.page}</span>
                        )}
                    </div>
                    {source.text && (
                        <div className="citation-tooltip-text">"{source.text}"</div>
                    )}
                </div>
            )}
        </span>
    );
}
