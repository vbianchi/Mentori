/**
 * Export chat feed to markdown or trigger download.
 */
export function feedToMarkdown(feed, taskName) {
    const lines = [];
    const date = new Date().toISOString().slice(0, 10);
    lines.push(`# ${taskName || 'Mentori Conversation'}`);
    lines.push(`*Exported on ${date}*\n`);
    lines.push('---\n');

    for (const msg of feed) {
        switch (msg.type) {
            case 'user':
                lines.push(`## User\n`);
                lines.push(msg.content || '');
                lines.push('');
                break;

            case 'synthesis':
            case 'assistant':
                lines.push(`## Assistant${msg.agentName ? ` (${msg.agentName})` : ''}\n`);
                if (msg.thinking) {
                    lines.push('<details><summary>Thinking</summary>\n');
                    lines.push(msg.thinking);
                    lines.push('\n</details>\n');
                }
                lines.push(msg.content || '');
                lines.push('');
                break;

            case 'step':
                if (msg.toolName) {
                    lines.push(`### Tool: ${msg.toolName}\n`);
                    if (msg.toolInput) {
                        lines.push('**Input:**');
                        lines.push('```json');
                        try {
                            lines.push(JSON.stringify(JSON.parse(msg.toolInput), null, 2));
                        } catch {
                            lines.push(msg.toolInput);
                        }
                        lines.push('```\n');
                    }
                    if (msg.toolOutput) {
                        lines.push('**Output:**');
                        lines.push('```');
                        lines.push(typeof msg.toolOutput === 'string' ? msg.toolOutput.slice(0, 2000) : JSON.stringify(msg.toolOutput).slice(0, 2000));
                        lines.push('```\n');
                    }
                }
                break;

            case 'analysis':
                if (msg.thinking) {
                    lines.push(`### Analysis\n`);
                    lines.push(`*Decision: ${msg.decision || 'N/A'}*\n`);
                }
                break;

            case 'plan':
                if (msg.plan) {
                    lines.push(`### Plan\n`);
                    const steps = msg.plan.steps || msg.plan;
                    if (Array.isArray(steps)) {
                        steps.forEach((s, i) => {
                            lines.push(`${i + 1}. ${s.description || s}`);
                        });
                    }
                    lines.push('');
                }
                break;

            default:
                break;
        }
    }

    return lines.join('\n');
}

export function downloadMarkdown(content, filename) {
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || 'mentori-export.md';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

export function extractFollowUpSuggestions(feed) {
    // Look at the last synthesis/assistant message
    const lastAiMsg = [...feed].reverse().find(
        m => (m.type === 'synthesis' || m.type === 'assistant') && m.content
    );
    if (!lastAiMsg?.content) return [];

    const content = lastAiMsg.content;

    // Skip suggestions for short/casual responses (greetings, clarifications, errors)
    if (content.length < 400) return [];
    if (content.match(/could you (let me know|specify|clarify|tell me)|which (topic|subject)/i)) return [];

    const suggestions = [];

    // Only suggest when the AI response is clearly a scientific/technical document analysis
    // with citations — this is Mentori's core use case
    const hasCitations = content.match(/\[\d+\]/) || content.match(/\[.*?\.pdf/);

    if (hasCitations) {
        suggestions.push('Elaborate on the cited sources');

        if (content.match(/however|limitation|caveat|challenge|drawback/i)) {
            suggestions.push('What are the main limitations?');
        }

        // Only suggest comparison when the response explicitly compares multiple named things
        if (content.match(/(compared to|versus|in contrast to|differs from|as opposed to)/i)) {
            suggestions.push('Create a detailed comparison table');
        }

        if (content.match(/pipeline|workflow|protocol|methodology/i) && suggestions.length < 3) {
            suggestions.push('Break down the methodology step by step');
        }

        if (content.length > 3000 && suggestions.length < 3) {
            suggestions.push('Summarize the key points concisely');
        }
    }

    return suggestions.slice(0, 3);
}
