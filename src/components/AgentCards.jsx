import { h } from 'preact';
import { useState, useEffect } from 'preact/hooks';
import { ArchitectIcon, CheckCircleIcon, ChevronDownIcon, CircleDotIcon, EditorIcon, ForemanIcon, LibrarianIcon, LoaderIcon, SupervisorIcon, WorkerIcon, XCircleIcon, ChevronsRightIcon } from './Icons';
import { CopyButton } from './Common';

const AgentResponseCard = ({ icon, title, children }) => (
    <div class="p-4 rounded-lg shadow-md bg-gray-800/50 border border-gray-700/50">
        <h3 class="font-bold text-sm text-gray-300 mb-3 capitalize flex items-center gap-2">{icon}{title}</h3>
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

// --- UPDATED ArchitectCard with HITL capabilities ---
export const ArchitectCard = ({ plan, isAwaitingApproval, onApprove, onReject, onModify }) => {
    const [planText, setPlanText] = useState(JSON.stringify(plan.steps, null, 2));

    // Effect to update the textarea if the plan prop changes from outside
    useEffect(() => {
        setPlanText(JSON.stringify(plan.steps, null, 2));
    }, [plan]);

    const handleModify = () => {
        try {
            const modifiedPlan = JSON.parse(planText);
            // Basic validation
            if (Array.isArray(modifiedPlan)) {
                onModify(modifiedPlan);
            } else {
                alert("Invalid format. The plan must be a JSON array of steps.");
            }
        } catch (e) {
            alert("Invalid JSON. Please check the format of your plan.");
        }
    };

    return (
        <AgentResponseCard icon={<ArchitectIcon class="h-5 w-5" />} title="The Chief Architect">
            {isAwaitingApproval ? (
                <div>
                    <h4 class="text-sm font-bold text-gray-400 mb-2">Proposed Plan (Awaiting Approval)</h4>
                    <p class="text-sm text-gray-400 mb-3">Review the plan below. You can approve it as is, or modify the JSON and then approve.</p>
                    <textarea
                        class="w-full h-48 p-2 bg-gray-900/70 border border-gray-600 rounded-md text-white font-mono text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
                        value={planText}
                        onInput={(e) => setPlanText(e.target.value)}
                    />
                    <div class="flex justify-end gap-3 mt-3">
                        <button onClick={onReject} class="px-4 py-2 bg-red-600/50 text-white font-semibold rounded-lg hover:bg-red-600/80 transition-colors">
                            Reject
                        </button>
                        <button onClick={handleModify} class="px-4 py-2 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors">
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
    <AgentResponseCard icon={<ForemanIcon class="h-5 w-5" />} title="The Site Foreman">
        <h4 class="text-sm font-bold text-gray-400 mb-2">Execution Log</h4>
        {plan.steps.map(step => <StepCard key={step.step_id} step={step} />)}
    </AgentResponseCard>
);

export const DirectAnswerCard = ({ answer }) => {
    const parsedHtml = window.marked ? window.marked.parse(answer, { breaks: true, gfm: true }) : answer.replace(/\n/g, '<br />');
    return (
        <AgentResponseCard icon={<LibrarianIcon class="h-5 w-5" />} title="The Librarian">
            <div class="prose prose-sm prose-invert max-w-none text-gray-200" dangerouslySetInnerHTML={{ __html: parsedHtml }}></div>
        </AgentResponseCard>
    );
};

export const FinalAnswerCard = ({ answer }) => {
    const parsedHtml = window.marked ? window.marked.parse(answer, { breaks: true, gfm: true }) : answer.replace(/\n/g, '<br />');
    return (
        <AgentResponseCard icon={<EditorIcon class="h-5 w-5" />} title="The Editor">
            <div class="prose prose-sm prose-invert max-w-none text-gray-200" dangerouslySetInnerHTML={{ __html: parsedHtml }}></div>
        </AgentResponseCard>
    );
};
