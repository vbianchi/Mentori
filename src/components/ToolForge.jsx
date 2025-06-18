import { h } from 'preact';
import { useState } from 'preact/hooks';
import { ForgeIcon, PlusCircleIcon, SaveIcon, Trash2Icon, LoaderIcon } from './Icons';

// A single row in the arguments list
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
                    <input
                        type="text"
                        name="name"
                        value={arg.name}
                        onInput={handleInputChange}
                        placeholder="e.g., query"
                        class="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                    />
                </div>
                <div>
                    <label class="block text-xs font-medium text-gray-400 mb-1">Arg Type</label>
                    <select
                        name="type"
                        value={arg.type}
                        onInput={handleInputChange}
                        class="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                    >
                        <option value="string">String</option>
                        <option value="number">Number</option>
                        <option value="boolean">Boolean</option>
                    </select>
                </div>
                <div>
                    <label class="block text-xs font-medium text-gray-400 mb-1">Arg Description</label>
                    <input
                        type="text"
                        name="description"
                        value={arg.description}
                        onInput={handleInputChange}
                        placeholder="A description for the LLM"
                        class="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                    />
                </div>
            </div>
            <button
                onClick={() => removeArg(index)}
                class="p-2 text-gray-500 hover:text-red-400 mt-6"
                title="Remove Argument"
            >
                <Trash2Icon class="h-5 w-5" />
            </button>
        </div>
    );
};


export const ToolForge = () => {
    const [toolName, setToolName] = useState('');
    const [toolDescription, setToolDescription] = useState('');
    const [args, setArgs] = useState([]);
    // --- NEW: State to handle the saving process ---
    const [isSaving, setIsSaving] = useState(false);

    const addArgument = () => {
        setArgs([...args, { name: '', type: 'string', description: '' }]);
    };

    const updateArg = (index, updatedArg) => {
        const newArgs = [...args];
        newArgs[index] = updatedArg;
        setArgs(newArgs);
    };

    const removeArg = (index) => {
        setArgs(args.filter((_, i) => i !== index));
    };

    // --- UPDATED: This function now calls the backend API ---
    const handleSaveTool = async () => {
        const toolDefinition = {
            name: toolName,
            description: toolDescription,
            arguments: args,
        };

        setIsSaving(true);
        try {
            const response = await fetch('http://localhost:8766/api/tools', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(toolDefinition),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to save the tool.');
            }

            const result = await response.json();
            alert(`Success: ${result.message}`);
            
            // Reset form after successful save
            setToolName('');
            setToolDescription('');
            setArgs([]);

        } catch (error) {
            console.error("Error saving tool:", error);
            alert(`Error: ${error.message}`);
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <div class="flex flex-col h-full">
            {/* Header */}
            <div class="flex-shrink-0 p-6 border-b border-gray-700/50">
                <h2 class="text-xl font-bold text-white flex items-center gap-3">
                    <ForgeIcon class="h-6 w-6" />
                    Tool Forge
                </h2>
                <p class="text-sm text-gray-400 mt-1">
                    Create a new custom tool for your agent to use.
                </p>
            </div>

            {/* Main Form Area */}
            <div class="flex-grow p-6 pt-4 overflow-y-auto">
                <div class="space-y-6">
                    {/* --- Tool Name --- */}
                    <div>
                        <label class="block text-sm font-medium text-gray-300 mb-1">Tool Name</label>
                        <input
                            type="text"
                            value={toolName}
                            onInput={(e) => setToolName(e.target.value)}
                            placeholder="my_custom_tool_name"
                            class="w-full p-2 bg-gray-900/70 border border-gray-600 rounded-md text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                        />
                         <p class="text-xs text-gray-500 mt-1">A unique, Python-compliant name for the tool (e.g., `get_weather`).</p>
                    </div>

                    {/* --- Tool Description --- */}
                    <div>
                        <label class="block text-sm font-medium text-gray-300 mb-1">Tool Description</label>
                        <textarea
                            value={toolDescription}
                            onInput={(e) => setToolDescription(e.target.value)}
                            rows="3"
                            placeholder="A clear, detailed description for the LLM to understand what this tool does."
                            class="w-full p-2 bg-gray-900/70 border border-gray-600 rounded-md text-white focus:ring-2 focus:ring-blue-500 focus:outline-none resize-y"
                        />
                         <p class="text-xs text-gray-500 mt-1">This is the most important part! The agent will use this to decide when to use your tool.</p>
                    </div>

                    {/* --- Arguments Section --- */}
                    <div>
                        <h4 class="text-md font-semibold text-gray-300 mb-2">Input Arguments</h4>
                        <div class="space-y-3">
                            {args.map((arg, index) => (
                                <ArgumentInput
                                    key={index}
                                    index={index}
                                    arg={arg}
                                    updateArg={updateArg}
                                    removeArg={removeArg}
                                />
                            ))}
                            {args.length === 0 && (
                                <div class="text-center py-4 text-sm text-gray-500">
                                    This tool has no input arguments.
                                </div>
                            )}
                        </div>
                        <button
                            onClick={addArgument}
                            class="flex items-center gap-2 w-full justify-center p-2 mt-4 text-sm font-semibold text-gray-300 hover:bg-gray-700/50 border border-dashed border-gray-600 rounded-lg"
                        >
                            <PlusCircleIcon class="h-5 w-5" /> Add Argument
                        </button>
                    </div>
                </div>
            </div>

             {/* Footer with Save Button */}
            <div class="flex-shrink-0 p-6 border-t border-gray-700/50">
                <button
                    onClick={handleSaveTool}
                    class="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-500 disabled:cursor-not-allowed"
                    disabled={!toolName || !toolDescription || isSaving}
                >
                    {isSaving ? (
                        <>
                            <LoaderIcon class="h-5 w-5" />
                            Saving...
                        </>
                    ) : (
                        <>
                            <SaveIcon class="h-5 w-5" />
                            Save Tool
                        </>
                    )}
                </button>
            </div>
        </div>
    );
};
