import { h } from 'preact';
// --- FIX: Added ArrowDownCircleIcon to the import list ---
import { ArrowDownCircleIcon, BriefcaseIcon } from './Icons';

/**
 * A single node representing a step in a plan.
 * @param {{step: object}} props
 */
const PlanNode = ({ step }) => (
    <div class="bg-gray-800/70 border border-gray-700 rounded-lg p-4 w-full max-w-md mx-auto">
        <div class="flex items-center gap-3">
            <div class="bg-gray-900 p-2 rounded-full">
                <BriefcaseIcon class="h-5 w-5 text-blue-400" />
            </div>
            <div class="flex-grow">
                <p class="font-bold text-white">{step.tool_name}</p>
                <p class="text-xs text-gray-400">{step.instruction}</p>
            </div>
        </div>
    </div>
);

/**
 * A static, read-only component that visualizes a multi-step plan
 * as a vertical sequence of nodes.
 * @param {{plan: {steps: object[]}}} props
 */
export const PlanVisualizer = ({ plan }) => {
    if (!plan || !plan.steps || plan.steps.length === 0) {
        return <div class="text-center text-gray-500">No plan steps to visualize.</div>;
    }

    return (
        <div class="p-6">
            <div class="flex flex-col items-center space-y-2">
                {plan.steps.map((step, index) => (
                    <>
                        <PlanNode key={step.step_id || index} step={step} />
                        {index < plan.steps.length - 1 && (
                            <ArrowDownCircleIcon class="h-6 w-6 text-gray-600" />
                        )}
                    </>
                ))}
            </div>
        </div>
    );
};
