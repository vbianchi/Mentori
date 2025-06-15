import { h } from 'preact';
import { useState, useEffect } from 'preact/hooks';
import { ArchitectIcon, CheckCircleIcon, ChevronDownIcon, CircleDotIcon, EditorIcon, ForemanIcon, LoaderIcon, PlusCircleIcon, SupervisorIcon, Trash2Icon, WorkerIcon, XCircleIcon } from './Icons';
import { CopyButton } from './Common';

const AgentResponseCard = ({ icon, title, children, showCopy, copyText }) => (
    <div class="p-4 rounded-lg shadow-md bg-gray-800/50 border border-gray-700/50 relative">
        <h3 class="font-bold text-sm text-gray-300 mb-3 capitalize flex items-center gap-2">{icon}{title}</h3>
        {showCopy && <CopyButton textToCopy={copyText} className="absolute top-3 right-3" />}
        <div class="pl-1">{children}</div>
    </div>
);

const StepCard = ({ step }) => {
    const [isExpanded, setIsExpanded] = useState(true);
    const getStatusIcon = () => {
        switch (step.status) {
            case 'in-progress': return <LoaderIcon class="h-5 w-5 text-yellow-400" />;
            case 'completed': return <CheckCircleIcon class="h-5 w-5 text-green-400" />;
            case 'failure': return <XCircleIcon class="h-5 w-5 text-red-500" />;
            case 'pending': default: return <CircleDotIcon class="h-5 w-5 text-gray-500" />;
        }
    };
    return (
        <div class="bg-gray-900/50 rounded-lg border border-gray-700/50 mb-2 last:mb-0 transition-all">
             <div class="flex items-center gap-4 p-4 cursor-pointer" onClick={() => setIsExpanded(!isExpanded)}>
                {getStatusIcon()}
                <p class="text-gray-200 font-medium flex-1">{step.instruction}</p>
                <ChevronDownIcon class={`h-5 w-5 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
             </div>
             {isExpanded && (step.status === 'completed' || step.status === 'failure') && step.toolCall && (
                <div class="p-4 pt-0">
                    <div class="ml-9 pl-4 border-l-2 border-gray-700 space-y-4">
                        <div>
                           <div class="flex items-center gap-2 text-sm font-semibold text-gray-400"> <WorkerIcon class="h-4 w-4" /> <span>The Worker: Execute Step</span> </div>
                           <pre class="text-xs text-cyan-300 overflow-x-auto p-2 mt-1 ml-7 bg-black/20 rounded-md font-mono relative"> <CopyButton textToCopy={JSON.stringify(step.toolCall, null, 2)} className="absolute top-1 right-1" /> <code>{JSON.stringify(step.toolCall, null, 2)}</code> </pre>
                        </div>
                        <div>
                           <div class="flex items-center gap-2 text-sm font-semibold text-gray-400"> <SupervisorIcon class="h-4 w-4" /> <span>The Project Supervisor: Evaluation</span> </div>
                           <pre class="text-xs text-gray-300 mt-1 ml-7 whitespace-pre-wrap font-mono relative bg-black/20 p-2 rounded-md"> <CopyButton textToCopy={step.evaluation?.reasoning || 'No evaluation.'} className="absolute top-1 right-1" /> {step.evaluation?.reasoning || 'No evaluation provided.'} </pre>
                        </div>
                    </div>
                </div>
             )}
        </div>
    );
};

const EditableStep = ({ step, index, updateStep, removeStep, availableTools }) => {
    const handleInputChange = (e) => {
        const { name, value } = e.target;
        updateStep(index, { ...step, [name]: value });
    };

    const handleToolInputChange = (e) => {
        updateStep(index, { ...step, tool_input: e.target.value });
    };

    return (
        <div class="bg-gray-900/50 p-4 rounded-lg border border-gray-700/50 mb-3 relative">
            <button onClick={() => removeStep(index)} class="absolute top-2 right-2 p-1 text-gray-500 hover:text-red-400" title="Delete Step">
                <Trash2Icon class="h-4 w-4" />
            </button>
            <p class="text-sm font-bold text-gray-400 mb-2">Step {index + 1}</p>
            <div class="space-y-3">
                <div>
                    <label class="block text-xs font-medium text-gray-400 mb-1">Instruction</label>
                    <input type="text" name="instruction" value={step.instruction} onInput={handleInputChange} class="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white text-sm" />
                </div>
                <div>
                    <label class="block text-xs font-medium text-gray-400 mb-1">Tool</label>
                    <select name="tool_name" value={step.tool_name} onInput={handleInputChange} class="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white text-sm">
                        <option value="">(Auto-select)</option>
                        {availableTools.map(tool => (
                            <option key={tool.name} value={tool.name}>{tool.name}</option>
                        ))}
                    </select>
                </div>
                <div>
                    <label class="block text-xs font-medium text-gray-400 mb-1">Tool Input (as JSON)</label>
                    <textarea name="tool_input" value={typeof step.tool_input === 'string' ? step.tool_input : JSON.stringify(step.tool_input || {}, null, 2)} onInput={handleToolInputChange} rows="3" class="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white font-mono text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none resize-y"></textarea>
                </div>
            </div>
        </div>
    );
};


export const ArchitectCard = ({ plan, isAwaitingApproval, onModify, onReject, availableTools }) => {
    const [editablePlan, setEditablePlan] = useState(plan.steps || []);

    useEffect(() => {
        setEditablePlan(plan.steps || []);
    }, [plan]);

    const updateStep = (index, updatedStep) => {
        const newPlan = [...editablePlan];
        newPlan[index] = updatedStep;
        setEditablePlan(newPlan);
    };

    const addStep = () => {
        const newStep = { step_id: editablePlan.length + 1, instruction: '', tool_name: '', tool_input: {} };
        setEditablePlan([...editablePlan, newStep]);
    };

    const removeStep = (index) => {
        const newPlan = editablePlan.filter((_, i) => i !== index).map((step, i) => ({ ...step, step_id: i + 1 }));
        setEditablePlan(newPlan);
    };

    const handleApprove = () => {
        const finalizedPlan = editablePlan.map(step => {
            try {
                const toolInput = typeof step.tool_input === 'string' ? JSON.parse(step.tool_input) : step.tool_input;
                return { ...step, tool_input: toolInput };
            } catch (e) {
                console.warn(`Could not parse tool_input for step ${step.step_id}. Leaving as is.`, e);
                return step;
            }
        });
        onModify(finalizedPlan);
    };

    return (
        <AgentResponseCard icon={<ArchitectIcon class="h-5 w-5" />} title="The Chief Architect">
            {isAwaitingApproval ? (
                <div>
                    <h4 class="text-sm font-bold text-gray-400 mb-2">Proposed Plan (Awaiting Approval)</h4>
                    <p class="text-sm text-gray-400 mb-3">Review and edit the plan below before running.</p>
                    <div class="space-y-2">
                        {editablePlan.map((step, index) => (
                            <EditableStep key={index} index={index} step={step} updateStep={updateStep} removeStep={removeStep} availableTools={availableTools} />
                        ))}
                    </div>
                     <button onClick={addStep} class="flex items-center gap-2 w-full justify-center p-2 mt-3 text-sm font-semibold text-gray-300 hover:bg-gray-700/50 border border-dashed border-gray-600 rounded-lg">
                        <PlusCircleIcon class="h-4 w-4" /> Add Step
                    </button>
                    <div class="flex justify-end gap-3 mt-4">
                        <button onClick={onReject} class="px-4 py-2 bg-red-600/50 text-white font-semibold rounded-lg hover:bg-red-600/80 transition-colors">
                            Reject
                        </button>
                        <button onClick={handleApprove} class="px-4 py-2 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors">
                            Approve & Run
                        </button>
                    </div>
                </div>
            ) : (
                <div>
                    <h4 class="text-sm font-bold text-gray-400 mb-2">Proposed Plan</h4>
                    <ul class="list-decimal list-inside text-gray-300 space-y-1">
                        {plan.steps.map(step => <li key={step.step_id}>{step.instruction}</li>)}
                    </ul>
                </div>
            )}
        </AgentResponseCard>
    );
};


export const SiteForemanCard = ({ plan }) => (
    // This wrapper div adds the indentation
    <div class="ml-4"> 
        <AgentResponseCard icon={<ForemanIcon class="h-5 w-5" />} title="The Site Foreman">
            <h4 class="text-sm font-bold text-gray-400 mb-2">Execution Log</h4>
            {plan.steps.map(step => <StepCard key={step.step_id} step={step} />)}
        </AgentResponseCard>
    </div>
);

export const DirectAnswerCard = ({ answer }) => {
    const parsedHtml = window.marked ? window.marked.parse(answer, { breaks: true, gfm: true }) : answer.replace(/\n/g, '<br />');
    return (
        <AgentResponseCard icon={<EditorIcon class="h-5 w-5" />} title="The Editor" showCopy={true} copyText={answer}>
            <div class="prose prose-sm prose-invert max-w-none text-gray-200" dangerouslySetInnerHTML={{ __html: parsedHtml }}></div>
        </AgentResponseCard>
    );
};

export const FinalAnswerCard = ({ answer }) => {
    const parsedHtml = window.marked ? window.marked.parse(answer, { breaks: true, gfm: true }) : answer.replace(/\n/g, '<br />');
    return (
        <AgentResponseCard icon={<EditorIcon class="h-5 w-5" />} title="The Editor" showCopy={true} copyText={answer}>
            <div class="prose prose-sm prose-invert max-w-none text-gray-200" dangerouslySetInnerHTML={{ __html: parsedHtml }}></div>
        </AgentResponseCard>
    );
};
