import { useState, useEffect } from 'preact/hooks';

/**
 * Custom hook for managing global application settings, including models and tools.
 */
export const useSettings = () => {
    // State for available models and the user's current selections
    const [availableModels, setAvailableModels] = useState([]);
    const [selectedModels, setSelectedModels] = useState({});

    // State for all available tools and which ones are currently enabled by the user
    const [availableTools, setAvailableTools] = useState([]);
    const [enabledTools, setEnabledTools] = useState({});

    // This effect runs once on mount to fetch the initial configuration from the server.
    useEffect(() => {
        const fetchConfig = async () => {
            try {
                // Fetch model configuration
                const modelsResponse = await fetch('http://localhost:8766/api/models');
                if (!modelsResponse.ok) throw new Error('Failed to fetch model configuration.');
                const modelsConfig = await modelsResponse.json();
                if (modelsConfig.available_models && modelsConfig.available_models.length > 0) {
                    setAvailableModels(modelsConfig.available_models);
                    setSelectedModels(modelsConfig.default_models);
                }
                
                // Fetch tool configuration
                const toolsResponse = await fetch('http://localhost:8766/api/tools');
                if (!toolsResponse.ok) throw new Error('Failed to fetch available tools.');
                const toolsConfig = await toolsResponse.json();
                const loadedTools = toolsConfig.tools || [];
                setAvailableTools(loadedTools);
                
                // Initialize all loaded tools to be enabled by default
                const initialEnabledState = {};
                loadedTools.forEach(tool => {
                    initialEnabledState[tool.name] = true;
                });
                setEnabledTools(initialEnabledState);

            } catch (error) {
                console.error("Failed to fetch startup config:", error);
            }
        };
        fetchConfig();
    }, []);

    /**
     * Handles changes to the model selection for a specific agent role.
     * @param {string} roleKey - The key identifying the agent role (e.g., 'EDITOR_LLM_ID').
     * @param {string} modelId - The ID of the selected model.
     */
    const handleModelChange = (roleKey, modelId) => {
        setSelectedModels(prev => ({ ...prev, [roleKey]: modelId }));
    };

    /**
     * Toggles the enabled/disabled state of a specific tool.
     * @param {string} toolName - The name of the tool to toggle.
     */
    const handleToggleTool = (toolName) => {
        setEnabledTools(prev => ({
            ...prev,
            [toolName]: !(prev[toolName] ?? true) // Safely toggle, defaulting to true if undefined
        }));
    };

    // Expose all state and handlers for components to use
    return {
        availableModels,
        selectedModels,
        handleModelChange,
        availableTools,
        enabledTools,
        handleToggleTool,
    };
};
