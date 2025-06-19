import { h } from 'preact';
import { useState, useEffect } from 'preact/hooks';
import { BriefcaseIcon, ForgeIcon, PlusCircleIcon, SaveIcon, Trash2Icon, LoaderIcon, FileTextIcon, GitCommitIcon, PlusIcon } from './Icons';
import { PlanVisualizer } from './PlanVisualizer';

// NOTE: ToolCreator is currently unused as we focus on the canvas, but we leave it for future use.
const ArgumentInput = ({ index, arg, updateArg, removeArg }) => {
    const handleInputChange = (e) => {
        const { name, value } = e.target;
        updateArg(index, { ...arg, [name]: value });
    };

    return (
        <div class="flex items-start gap-3 p-3 bg-gray-900/50 rounded-lg border border-gray-700/50">
            <div class="flex-grow grid grid-cols-3 gap-3">
                <div>
                    <label class="block text-xs font-medium text-gray-400 mb-1">Arg Name</label>
                    <input type="text" name="name" value={arg.name} onInput={handleInputChange} placeholder="e.g., query" class="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"/>
                </div>
                <div>
                    <label class="block text-xs font-medium text-gray-400 mb-1">Arg Type</label>
                    <select name="type" value={arg.type} onInput={handleInputChange} class="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none">
                        <option value="string">String</option>
                        <option value="number">Number</option>
                        <option value="boolean">Boolean</option>
                    </select>
                </div>
                <div>
                    <label class="block text-xs font-medium text-gray-400 mb-1">Arg Description</label>
                    <input type="text" name="description" value={arg.description} onInput={handleInputChange} placeholder="A description for the LLM" class="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"/>
                </div>
            </div>
            <button onClick={() => removeArg(index)} class="p-2 text-gray-500 hover:text-red-400 mt-6" title="Remove Argument">
                <Trash2Icon class="h-5 w-5" />
            </button>
        </div>
    );
};
const ToolCreator = ({ onSave }) => {
    const [toolName, setToolName] = useState('');
    const [toolDescription, setToolDescription] = useState('');
    const [args, setArgs] = useState([]);
    const [isSaving, setIsSaving] = useState(false);

    const addArgument = () => setArgs([...args, { name: '', type: 'string', description: '' }]);
    const updateArg = (index, updatedArg) => { const newArgs = [...args]; newArgs[index] = updatedArg; setArgs(newArgs); };
    const removeArg = (index) => setArgs(args.filter((_, i) => i !== index));

    const handleSaveTool = async () => {
        const toolDefinition = { name: toolName, description: toolDescription, arguments: args };
        setIsSaving(true);
        await onSave(toolDefinition);
        setIsSaving(false);
        setToolName(''); setToolDescription(''); setArgs([]);
    };

    return (
        <div class="flex flex-col h-full">
            <div class="p-6 border-b border-gray-700/50">
                <h3 class="text-lg font-bold text-white">Create New Tool</h3>
                <p class="text-sm text-gray-400 mt-1">Define a new "Engine Tool" powered by an LLM.</p>
            </div>
            <div class="flex-grow p-6 pt-4 overflow-y-auto">
                <div class="space-y-6">
                    <div>
                        <label class="block text-sm font-medium text-gray-300 mb-1">Tool Name</label>
                        <input type="text" value={toolName} onInput={(e) => setToolName(e.target.value)} placeholder="my_custom_tool_name" class="w-full p-2 bg-gray-900/70 border border-gray-600 rounded-md text-white focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                        <p class="text-xs text-gray-500 mt-1">A unique, Python-compliant name for the tool (e.g., `get_weather`).</p>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-300 mb-1">Tool Description</label>
                        <textarea value={toolDescription} onInput={(e) => setToolDescription(e.target.value)} rows="3" placeholder="A clear, detailed description for the LLM..." class="w-full p-2 bg-gray-900/70 border border-gray-600 rounded-md text-white focus:ring-2 focus:ring-blue-500 focus:outline-none resize-y" />
                        <p class="text-xs text-gray-500 mt-1">This is the most important part! The agent will use this to decide when to use your tool.</p>
                    </div>
                    <div>
                        <h4 class="text-md font-semibold text-gray-300 mb-2">Input Arguments</h4>
                        <div class="space-y-3">
                            {args.map((arg, index) => ( <ArgumentInput key={index} index={index} arg={arg} updateArg={updateArg} removeArg={removeArg} /> ))}
                            {args.length === 0 && ( <div class="text-center py-4 text-sm text-gray-500">This tool has no input arguments.</div> )}
                        </div>
                        <button onClick={addArgument} class="flex items-center gap-2 w-full justify-center p-2 mt-4 text-sm font-semibold text-gray-300 hover:bg-gray-700/50 border border-dashed border-gray-600 rounded-lg">
                            <PlusCircleIcon class="h-5 w-5" /> Add Argument
                        </button>
                    </div>
                </div>
            </div>
            <div class="flex-shrink-0 p-6 border-t border-gray-700/50">
                <button onClick={handleSaveTool} class="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-500 disabled:cursor-not-allowed" disabled={!toolName || !toolDescription || isSaving}>
                    {isSaving ? ( <><LoaderIcon class="h-5 w-5" /> Saving...</> ) : ( <><SaveIcon class="h-5 w-5" /> Save Tool</> )}
                </button>
            </div>
        </div>
    );
};

// The main ToolForge component
export const ToolForge = () => {
    const [tools, setTools] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [selectedTool, setSelectedTool] = useState(null);
    const [activePlan, setActivePlan] = useState({ steps: [] });

    const fetchTools = async () => {
        setIsLoading(true);
        try {
            const response = await fetch('http://localhost:8766/api/tools');
            if (!response.ok) throw new Error('Failed to fetch tools');
            const data = await response.json();
            const sortedTools = (data.tools || []).sort((a, b) => {
                if (a.type === 'blueprint' && b.type !== 'blueprint') return -1;
                if (a.type !== 'blueprint' && b.type === 'blueprint') return 1;
                return a.name.localeCompare(b.name);
            });
            setTools(sortedTools);
        } catch (error) { console.error("Error fetching tools:", error); setTools([]); }
        finally { setIsLoading(false); }
    };

    useEffect(() => { fetchTools(); }, []);
    
    useEffect(() => {
        if (selectedTool) {
            setActivePlan(selectedTool.plan || { steps: [] });
        } else {
            setActivePlan({ steps: [], arguments: [] });
        }
    }, [selectedTool]);

    const handleSaveTool = async (toolDefinition, isBlueprint = false) => {
        const endpoint = isBlueprint ? '/api/blueprints' : '/api/tools';
        try {
            const response = await fetch(`http://localhost:8766${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(toolDefinition),
            });
            if (!response.ok) throw new Error((await response.json()).error || 'Failed to save.');
            alert(`Success: ${(await response.json()).message}`);
            await fetchTools(); 
            setSelectedTool(null);
        } catch (error) { console.error("Error saving:", error); alert(`Error: ${error.message}`); }
    };
    
    const handleAddToolToCanvas = (tool) => {
        const newStep = {
            step_id: `temp_${Date.now()}`,
            tool_name: tool.name,
            instruction: tool.description,
            tool_input: {}
        };
        const currentSteps = activePlan?.steps || [];
        setActivePlan(prevPlan => ({
            ...prevPlan,
            steps: [...currentSteps, newStep]
        }));
        // --- FIX: This line was causing the view to reset. It has been removed. ---
        // if(selectedTool) setSelectedTool(null);
    };

    return (
        <div class="flex h-full">
            <div class="w-1/3 min-w-[250px] bg-gray-900/30 border-r border-gray-700/50 flex flex-col">
                <div class="flex-shrink-0 p-4 border-b border-gray-700/50">
                    <h2 class="text-lg font-bold text-white flex items-center gap-2"><ForgeIcon class="h-5 w-5" />Tool & Blueprint Forge</h2>
                </div>
                <div class="flex-grow overflow-y-auto p-2">
                    {isLoading ? ( <div class="flex items-center justify-center h-full text-gray-400"><LoaderIcon class="h-5 w-5" /></div> ) : (
                        <ul>
                            {tools.map(tool => (
                                <li key={tool.name} class="group flex justify-between items-center p-2 rounded-md text-sm mb-1 text-gray-300 hover:bg-gray-700/50">
                                    <div onClick={() => setSelectedTool(tool)} class="flex items-center gap-3 cursor-pointer flex-grow truncate">
                                        {tool.type === 'blueprint' ? <GitCommitIcon class="h-4 w-4 text-purple-400 flex-shrink-0" /> : <FileTextIcon class="h-4 w-4 text-cyan-400 flex-shrink-0" />}
                                        <span class="truncate">{tool.name}</span>
                                    </div>
                                    <button onClick={() => handleAddToolToCanvas(tool)} class="p-1 opacity-0 group-hover:opacity-100 hover:text-white" title="Add to canvas"><PlusIcon class="h-4 w-4" /></button>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
                <div class="p-2 border-t border-gray-700/50">
                     <button onClick={() => setSelectedTool(null)} class="w-full flex items-center gap-2 justify-center p-2 text-sm font-semibold text-gray-300 hover:bg-blue-600/30 rounded-md"><PlusCircleIcon class="h-5 w-5" /> Create New Blueprint</button>
                </div>
            </div>
            
            <div class="w-2/3 flex-grow overflow-y-auto">
                <PlanVisualizer plan={activePlan} setPlan={setActivePlan} />
            </div>
        </div>
    );
};
