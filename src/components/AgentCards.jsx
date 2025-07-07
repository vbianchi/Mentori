// src/components/AgentCards.jsx
// -----------------------------------------------------------------------------
// ResearchAgent UI Components (Phase 17 - Four-Track Card Consolidation)
//
// This version reintegrates the UI components from the original three-track
// agent, making them available for the unified four-track system.
//
// Key Architectural Changes:
// 1. `ArchitectCard` Restored: The interactive plan editor component has been
//    re-added. This card will be used to display, edit, and approve plans
//    from the `std_chief_architect_node`.
// 2. `SiteForemanCard` Restored: The execution log component, which displays
//    a list of collapsable `StepCard` components, has been re-added. This
//    will be used to visualize the step-by-step execution of a standard
//    complex project.
// 3. `StepCard` Restored: The dependent `StepCard` component is also included,
//    providing the detailed view for each step within the `SiteForemanCard`.
// 4. All components from both codebases are now consolidated into this single
//    file, ready for the state management and rendering logic updates.
// -----------------------------------------------------------------------------

import { h } from 'preact';
import { useState, useEffect } from 'preact/hooks';
import { ArchitectIcon, CheckCircleIcon, ChevronDownIcon, CircleDotIcon, EditorIcon, ForemanIcon, LoaderIcon, PlusCircleIcon, SupervisorIcon, Trash2Icon, UserIcon, WorkerIcon, XCircleIcon, BoardIcon, CheckIcon, ChairIcon, CritiqueIcon } from './Icons';
import { CopyButton } from './Common';

const AgentResponseCard = ({ icon, title, children, showCopy, copyText, color = 'gray' }) => (
    <div class={`p-4 rounded-lg shadow-md bg-gray-800/50 border border-${color}-700/50 relative`}>
        <h3 class={`font-bold text-sm text-${color}-300 mb-3 capitalize flex items-center gap-2`}>{icon}{title}</h3>
        {showCopy && <CopyButton textToCopy={copyText} className="absolute top-3 right-3" />}
        <div class="pl-1">{children}</div>
    </div>
);


const StepCard = ({ step }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    
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


const PlanStepView = ({ step }) => {
    const isNew = (step.instruction || '').startsWith('**NEW:**');
    const isModified = (step.instruction || '').startsWith('**MODIFIED:**');
    let text = step.instruction || '';
    let style = '';

    if (isNew) {
        text = text.substring('**NEW:**'.length).trim();
        style = 'text-green-400 font-bold';
    } else if (isModified) {
        text = text.substring('**MODIFIED:**'.length).trim();
        style = 'text-yellow-400 font-bold';
    }

    return (
        <li class={`flex items-start gap-3 py-1.5 ${style}`}>
            <CheckIcon class="h-4 w-4 text-blue-400 mt-1 flex-shrink-0" />
            <span>
                {text}
                <span class="ml-2 inline-block bg-gray-700 text-blue-300 text-xs font-mono px-1.5 py-0.5 rounded">
                    {step.tool || step.tool_name}
                </span>
            </span>
        </li>
    );
};

export const ArchitectCard = ({ plan, isAwaitingApproval, onModify, onReject, availableTools }) => {
    const [editablePlan, setEditablePlan] = useState([]);

    useEffect(() => {
        setEditablePlan(plan?.steps || plan || []);
    }, [plan]);

    const updateStep = (index, updatedStep) => {
        const newPlan = [...editablePlan]; newPlan[index] = updatedStep; setEditablePlan(newPlan);
    };
    const addStep = () => {
        setEditablePlan([...editablePlan, { step_id: editablePlan.length + 1, instruction: '', tool_name: '', tool_input: {} }]);
    };
    const removeStep = (index) => {
        setEditablePlan(editablePlan.filter((_, i) => i !== index).map((step, i) => ({ ...step, step_id: i + 1 })));
    };
    const handleApprove = () => {
        const finalizedPlan = editablePlan.map(step => {
            try { return { ...step, tool_input: typeof step.tool_input === 'string' ? JSON.parse(step.tool_input) : step.tool_input }; }
            catch (e) { return step; }
        });
        onModify(finalizedPlan);
    };

    return (
        <AgentResponseCard icon={<ArchitectIcon class="h-5 w-5" />} title="The Chief Architect">
            {isAwaitingApproval ? (
                <div>
                    <h4 class="text-sm font-bold text-gray-400 mb-3">Proposed Plan (Awaiting Approval)</h4>
                    <div class="space-y-2">
                        {editablePlan.map((step, index) => (
                            <EditableStep key={index} index={index} step={step} updateStep={updateStep} removeStep={removeStep} availableTools={availableTools} />
                        ))}
                    </div>
                     <button onClick={addStep} class="flex items-center gap-2 w-full justify-center p-2 mt-3 text-sm font-semibold text-gray-300 hover:bg-gray-700/50 border border-dashed border-gray-600 rounded-lg">
                        <PlusCircleIcon class="h-4 w-4" /> Add Step
                    </button>
                    <div class="flex justify-end gap-3 mt-4">
                        <button onClick={onReject} class="px-4 py-2 bg-red-600/50 text-white font-semibold rounded-lg hover:bg-red-600/80">Reject</button>
                        <button onClick={handleApprove} class="px-4 py-2 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700">Approve & Run</button>
                    </div>
                </div>
            ) : (
                <div>
                    <h4 class="text-sm font-bold text-gray-400 mb-2">Tactical Plan Generated</h4>
                    <ul class="space-y-1 text-gray-300">
                        {(editablePlan || []).map((step, index) => <PlanStepView key={index} step={step} />)}
                    </ul>
                </div>
            )}
        </AgentResponseCard>
    );
};

export const BoardApprovalCard = ({ experts, onApproval }) => {
    const [isApproved, setIsApproved] = useState(null);

    const handleDecision = (approved) => {
        setIsApproved(approved);
        onApproval(approved);
    };

    return (
        <AgentResponseCard icon={<BoardIcon class="h-5 w-5" />} title="Board of Experts Formation" color="rose">
             <p class="text-sm text-gray-400 mb-3">The agent has proposed the following board for your approval:</p>
             <ul class="space-y-3 mb-4">
                {(experts || []).map(expert => (
                    <li key={expert.title} class="p-3 bg-gray-900/50 rounded-lg border border-gray-700/50">
                        <p class="font-semibold text-white">{expert.title}</p>
                        <p class="text-sm text-gray-400">{expert.qualities}</p>
                    </li>
                ))}
             </ul>
             {isApproved === null ? (
                <div class="flex justify-end gap-3">
                    <button onClick={() => handleDecision(false)} class="px-4 py-2 bg-red-600/50 text-white font-semibold rounded-lg hover:bg-red-600/80">Reject</button>
                    <button onClick={() => handleDecision(true)} class="px-4 py-2 bg-green-600/80 text-white font-semibold rounded-lg hover:bg-green-700">Approve Board</button>
                </div>
             ) : (
                <div class={`text-sm font-bold flex items-center gap-2 justify-end ${isApproved ? 'text-green-400' : 'text-red-400'}`}>
                    {isApproved ? <CheckIcon class="h-5 w-5" /> : <XCircleIcon class="h-5 w-5" />}
                    Board {isApproved ? 'Approved' : 'Rejected'}
                </div>
             )}
        </AgentResponseCard>
    );
};

export const ChairPlanCard = ({ plan }) => (
    <AgentResponseCard icon={<ChairIcon class="h-5 w-5" />} title="The Chair's Initial Plan" color="amber">
        <p class="text-sm text-gray-400 mb-3">The Chair has drafted the following initial plan for review by the experts:</p>
        <ul class="space-y-1 text-gray-300">
            {(plan || []).map((step, index) => <PlanStepView key={index} step={step} />)}
        </ul>
    </AgentResponseCard>
);

export const ExpertCritiqueCard = ({ critique }) => (
    <AgentResponseCard icon={<CritiqueIcon class="h-5 w-5" />} title={`${critique.title}'s Critique`} color="purple">
        <p class="text-sm text-gray-300 italic whitespace-pre-wrap">"{critique.critique}"</p>
        <div class="mt-3 pt-3 border-t border-gray-700/50">
             <h4 class="text-xs font-bold text-gray-400 mb-2">Plan after this critique:</h4>
             <ul class="space-y-1 text-gray-300 text-sm">
                {(critique.plan_after_critique || []).map((step, index) => <PlanStepView key={index} step={step} />)}
            </ul>
        </div>
    </AgentResponseCard>
);

export const FinalPlanApprovalCard = ({ plan, critiques, implementationNotes, onModify, onReject }) => {
    const [isApproved, setIsApproved] = useState(null);

    const handleDecision = (approved) => {
        setIsApproved(approved);
        if (approved) {
            onModify(plan);
        } else {
            onReject();
        }
    };
    
    return (
        <AgentResponseCard icon={<ChairIcon class="h-5 w-5" />} title="The Chair's Final Review" color="amber">
            <p class="text-sm text-gray-400 mb-4">The board has completed its review and the Chair has synthesized the final plan. Please review and give your approval to begin execution.</p>
            
            <details class="mb-4">
                <summary class="text-sm font-bold text-gray-400 cursor-pointer hover:text-white">View Full Board Deliberation ({critiques?.length || 0} critiques)</summary>
                <ul class="space-y-2 mt-2 border-l-2 border-gray-700 pl-4">
                    {(critiques || []).map((c, i) => (
                        <li key={i} class="p-3 bg-gray-900/50 rounded-lg text-sm">
                            <p class="font-semibold text-purple-300">{c.title}:</p>
                            <p class="text-gray-300 italic whitespace-pre-wrap">"{c.critique}"</p>
                        </li>
                    ))}
                </ul>
            </details>

            {implementationNotes && implementationNotes.length > 0 && (
                <div class="mb-4">
                    <h4 class="text-sm font-bold text-gray-400 mb-3">Key Implementation Notes:</h4>
                    <ul class="list-disc list-inside text-gray-300 space-y-1 text-sm bg-gray-900/50 p-3 rounded-lg border border-gray-700/50">
                        {implementationNotes.map((note, index) => <li key={index}>{note}</li>)}
                    </ul>
                </div>
            )}
            
            <div>
                <h4 class="text-sm font-bold text-gray-400 mb-3">Final Plan for Execution:</h4>
                 <ul class="space-y-1 text-gray-300 pl-2 border-l-2 border-green-700/50">
                    {(plan || []).map((step, index) => <PlanStepView key={index} step={step} />)}
                </ul>
                
                {isApproved === null ? (
                    <div class="flex justify-end gap-3 mt-4">
                        <button onClick={() => handleDecision(false)} class="px-4 py-2 bg-red-600/50 text-white font-semibold rounded-lg hover:bg-red-600/80">Reject & End Task</button>
                        <button onClick={() => handleDecision(true)} class="px-4 py-2 bg-green-600/80 text-white font-semibold rounded-lg hover:bg-green-700">Approve & Execute</button>
                    </div>
                ) : (
                    <div class={`text-sm mt-4 font-bold flex items-center gap-2 justify-end ${isApproved ? 'text-green-400' : 'text-red-400'}`}>
                        {isApproved ? <CheckIcon class="h-5 w-5" /> : <XCircleIcon class="h-5 w-5" />}
                        {isApproved ? 'Plan Approved for Execution' : 'Plan Rejected'}
                    </div>
                )}
            </div>
        </AgentResponseCard>
    );
};

export const ForemanCard = ({ step }) => (
    <AgentResponseCard icon={<ForemanIcon class="h-5 w-5" />} title="The Site Foreman" color="cyan">
        <p class="text-sm text-gray-400 mb-2">Preparing to execute the following step:</p>
        {step ? (
            <div class="p-3 bg-gray-900/50 rounded-lg border border-gray-700/50">
                <p class="text-white font-medium">{step.instruction}</p>
                <p class="text-xs text-cyan-300 font-mono mt-1">Tool: {step.tool_name}</p>
            </div>
        ) : (
            <p class="text-sm text-gray-500">No step information available.</p>
        )}
    </AgentResponseCard>
);

export const WorkerCard = ({ toolCall, output }) => (
    <AgentResponseCard icon={<WorkerIcon class="h-5 w-5" />} title="The Worker" color="blue">
        <p class="text-sm text-gray-400 mb-2">Executed tool <code class="bg-gray-700 text-blue-300 text-xs font-mono px-1.5 py-0.5 rounded">{toolCall?.tool_name}</code> and received the following output:</p>
        <pre class="text-xs text-gray-300 whitespace-pre-wrap font-mono p-3 bg-black/20 rounded-md">
            {output || "No output was returned."}
        </pre>
    </AgentResponseCard>
);

export const SupervisorCard = ({ evaluation }) => {
    const isSuccess = evaluation?.status === 'success';
    const color = isSuccess ? 'green' : 'red';
    const icon = isSuccess ? <CheckCircleIcon class="h-5 w-5" /> : <XCircleIcon class="h-5 w-5" />;

    return (
        <AgentResponseCard icon={<SupervisorIcon class="h-5 w-5" />} title="The Project Supervisor" color={color}>
            <p class="text-sm text-gray-400 mb-2">Evaluated the previous step with the following result:</p>
            <div class={`p-3 bg-gray-900/50 rounded-lg border border-${color}-700/50`}>
                <div class="flex items-center gap-2 font-semibold mb-1">
                    {icon}
                    <span class={`text-${color}-400`}>Status: {evaluation?.status || 'Unknown'}</span>
                </div>
                <p class="text-xs text-gray-300 whitespace-pre-wrap font-mono pl-7">
                    {evaluation?.reasoning || "No reasoning provided."}
                </p>
            </div>
        </AgentResponseCard>
    );
};

export const EditorReportCard = ({ report }) => (
    <AgentResponseCard icon={<EditorIcon class="h-5 w-5" />} title="Editor's Checkpoint Report" color="sky">
        <p class="text-sm text-gray-300 whitespace-pre-wrap">{report}</p>
    </AgentResponseCard>
);

export const BoardDecisionCard = ({ decision }) => (
    <AgentResponseCard icon={<BoardIcon class="h-5 w-5" />} title="Board Checkpoint Review" color="rose">
        <p class="text-sm text-gray-400 mb-2">The Board has reviewed the progress and made a decision:</p>
        <div class="p-3 bg-gray-900/50 rounded-lg border border-gray-700/50">
            <p class="text-white font-semibold text-center capitalize">{decision}</p>
        </div>
    </AgentResponseCard>
);

export const UserGuidanceCard = ({ report, isAwaitingApproval, submittedGuidance, onGuidanceSubmit }) => {
    const [guidanceText, setGuidanceText] = useState('');

    const handleSubmit = () => {
        if (guidanceText.trim()) {
            onGuidanceSubmit(guidanceText);
        }
    };

    return (
        <AgentResponseCard icon={<UserIcon class="h-5 w-5" />} title="User Guidance Required" color="blue">
            <div class="mb-3 p-3 bg-gray-900/50 rounded-lg border border-sky-700/50">
                <h4 class="text-xs font-bold text-sky-300 mb-1">Editor's Report:</h4>
                <p class="text-sm text-gray-300 whitespace-pre-wrap">{report}</p>
            </div>
            <p class="text-sm text-gray-400 mb-3">The Board of Experts has escalated the task and requires your guidance on how to proceed.</p>

            {isAwaitingApproval ? (
                <div class="flex gap-2">
                    <input
                        type="text"
                        value={guidanceText}
                        onInput={(e) => setGuidanceText(e.target.value)}
                        onKeyDown={(e) => { if (e.key === 'Enter') handleSubmit(); }}
                        class="flex-grow bg-input border border-border rounded-lg p-2 text-sm"
                        placeholder="Provide guidance to the board..."
                    />
                    <button onClick={handleSubmit} class="px-4 py-2 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 text-sm">
                        Submit Guidance
                    </button>
                </div>
            ) : (
                <div>
                    <h4 class="text-xs font-bold text-green-400 mb-1">Your Submitted Guidance:</h4>
                    <p class="text-sm text-gray-300 italic p-3 bg-gray-900/50 rounded-lg border border-green-700/50">
                        "{submittedGuidance}"
                    </p>
                </div>
            )}
        </AgentResponseCard>
    );
};


export const SiteForemanCard = ({ plan }) => (
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
