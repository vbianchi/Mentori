import { PanelLeftClose, PanelRightClose, PanelLeftOpen, PanelRightOpen } from 'lucide-react';

/**
 * SidebarSizer Component
 * Provides chevron buttons to toggle sidebar sizes between small/normal/large
 *
 * @param {Object} props
 * @param {string} props.side - 'left' or 'right'
 * @param {string} props.size - 'small', 'normal', or 'large'
 * @param {Function} props.setSize - Function to update size
 */
export const SidebarSizer = ({ side, size, setSize }) => {
    const leftDisabled = side === 'left' ? size === 'small' : size === 'large';
    const rightDisabled = side === 'left' ? size === 'large' : size === 'small';

    const onLeftClick = () => {
        if (leftDisabled) return;
        if (side === 'left') {
            setSize(size === 'large' ? 'normal' : 'small');
        } else {
            setSize(size === 'small' ? 'normal' : 'large');
        }
    };

    const onRightClick = () => {
        if (rightDisabled) return;
        if (side === 'left') {
            setSize(size === 'small' ? 'normal' : 'large');
        } else {
            setSize(size === 'large' ? 'normal' : 'small');
        }
    };

    const LeftIcon = side === 'left' ? PanelLeftClose : PanelRightOpen;
    const RightIcon = side === 'left' ? PanelLeftOpen : PanelRightClose;

    const leftTitle =
        side === 'left'
            ? size === 'large'
                ? 'Back to normal'
                : 'Shrink to 50%'
            : size === 'small'
                ? 'Back to normal'
                : 'Expand to 150%';

    const rightTitle =
        side === 'left'
            ? size === 'small'
                ? 'Back to normal'
                : 'Expand to 150%'
            : size === 'large'
                ? 'Back to normal'
                : 'Shrink to 50%';

    return (
        <div className="flex items-center gap-1">
            <button
                onClick={onLeftClick}
                disabled={leftDisabled}
                aria-disabled={leftDisabled ? 'true' : 'false'}
                aria-label={`${side === 'left' ? 'Left' : 'Right'} sidebar: ${leftTitle}`}
                className="p-1 text-muted hover:text-white disabled:opacity-20 disabled:cursor-not-allowed transition-colors"
                style={{ backgroundColor: 'transparent', border: 'none' }}
                title={leftTitle}
            >
                <LeftIcon size={16} />
            </button>
            <button
                onClick={onRightClick}
                disabled={rightDisabled}
                aria-disabled={rightDisabled ? 'true' : 'false'}
                aria-label={`${side === 'left' ? 'Left' : 'Right'} sidebar: ${rightTitle}`}
                className="p-1 text-muted hover:text-white disabled:opacity-20 disabled:cursor-not-allowed transition-colors"
                style={{ backgroundColor: 'transparent', border: 'none' }}
                title={rightTitle}
            >
                <RightIcon size={16} />
            </button>
        </div>
    );
};
