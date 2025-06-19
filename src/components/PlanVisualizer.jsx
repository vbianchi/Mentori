import { h } from 'preact';
import { useState, useRef } from 'preact/hooks';
import { ArrowDownCircleIcon, BriefcaseIcon, MoveVerticalIcon, Trash2Icon } from './Icons';

const DropIndicator = () => <div class="w-full max-w-md mx-auto my-0.5 h-1 bg-blue-500 rounded-full" />;

const PlanNode = ({ step, isDragging, onDelete }) => (
    <div 
      // --- DEFINITIVE SIZING FIX: Using a flex container with fixed height and no-shrink on children ---
      class={`bg-gray-800/70 border border-gray-700 rounded-lg p-3 w-full max-w-md mx-auto flex items-center gap-3 h-20 transition-opacity ${isDragging ? 'opacity-30' : 'opacity-100'}`}
    >
        <MoveVerticalIcon class="h-5 w-5 text-gray-500 cursor-grab flex-shrink-0" />
        <div class="flex items-center gap-3 flex-grow min-w-0">
            <div class="bg-gray-900 p-2 rounded-full flex-shrink-0">
                <BriefcaseIcon class="h-5 w-5 text-blue-400" />
            </div>
            <div class="flex-grow min-w-0">
                <p class="font-bold text-white truncate">{step.tool_name}</p>
                <p class="text-xs text-gray-400 truncate">{step.instruction}</p>
            </div>
        </div>
        <button onClick={onDelete} class="p-1 text-gray-500 hover:text-red-400 flex-shrink-0" title="Remove step">
            <Trash2Icon class="h-4 w-4" />
        </button>
    </div>
);

export const PlanVisualizer = ({ plan, setPlan }) => {
    const [dragOverIndex, setDragOverIndex] = useState(null);
    const draggedItemIndex = useRef(null);

    const steps = plan?.steps || [];

    if (steps.length === 0) {
        return <div class="text-center text-gray-500 p-8 border-t border-gray-700/50">The Canvas is Empty</div>;
    }

    const removeStep = (indexToRemove) => {
        const newSteps = steps.filter((_, index) => index !== indexToRemove);
        setPlan({ ...plan, steps: newSteps });
    };
    
    const handleDragStart = (e, index) => {
        draggedItemIndex.current = index;
        e.dataTransfer.effectAllowed = 'move';
        const img = new Image();
        img.src = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
        e.dataTransfer.setDragImage(img, 0, 0);
    };

    const handleDragOver = (e, index) => {
        e.preventDefault();
        const rect = e.currentTarget.getBoundingClientRect();
        const midpoint = rect.top + rect.height / 2;
        setDragOverIndex(e.clientY < midpoint ? index : index + 1);
    };
    
    const handleDrop = () => {
        if (draggedItemIndex.current === null || dragOverIndex === null) return;
        const fromIndex = draggedItemIndex.current;
        let toIndex = dragOverIndex;
        if (fromIndex < toIndex) toIndex--;

        const reorderedSteps = [...steps];
        const [movedItem] = reorderedSteps.splice(fromIndex, 1);
        reorderedSteps.splice(toIndex, 0, movedItem);
        
        setPlan({ ...plan, steps: reorderedSteps });
        handleDragEnd();
    };

    const handleDragEnd = () => {
        draggedItemIndex.current = null;
        setDragOverIndex(null);
    };

    const handleContainerDragLeave = (e) => {
        if (!e.currentTarget.contains(e.relatedTarget)) {
            setDragOverIndex(null);
        }
    };

    return (
        <div class="p-6 border-t border-gray-700/50" onDrop={handleDrop} onDragEnd={handleDragEnd} onDragLeave={handleContainerDragLeave}>
            <h3 class="text-lg font-bold text-center mb-4">Canvas</h3>
            <div class="flex flex-col items-center space-y-2">
                {steps.map((step, index) => (
                    <div 
                      key={step.step_id || index}
                      class="w-full"
                      draggable="true"
                      onDragStart={(e) => handleDragStart(e, index)}
                      onDragOver={(e) => handleDragOver(e, index)}
                    >
                        {dragOverIndex === index && <DropIndicator />}
                        <PlanNode 
                            step={step} 
                            isDragging={draggedItemIndex.current === index} 
                            onDelete={() => removeStep(index)}
                        />
                    </div>
                ))}
                {dragOverIndex === steps.length && <DropIndicator />}
            </div>
        </div>
    );
};
