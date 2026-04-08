import { visit } from 'unist-util-visit';

/**
 * Remark plugin that transforms [N] citation patterns in text into
 * custom citation nodes that React can render as interactive elements.
 */
export function remarkCitations() {
    return (tree) => {
        visit(tree, 'text', (node, index, parent) => {
            if (!parent || !node.value) return;

            // Match [N] patterns (single or comma-separated like [1][2] or [1,2])
            const regex = /\[(\d+(?:,\s*\d+)*)\]/g;
            const parts = [];
            let lastIndex = 0;
            let match;

            while ((match = regex.exec(node.value)) !== null) {
                // Text before the citation
                if (match.index > lastIndex) {
                    parts.push({ type: 'text', value: node.value.slice(lastIndex, match.index) });
                }

                // The citation itself
                const nums = match[1].split(',').map(n => n.trim());
                for (let i = 0; i < nums.length; i++) {
                    if (i > 0) parts.push({ type: 'text', value: '' });
                    parts.push({
                        type: 'citation',
                        data: {
                            hName: 'citation',
                            hProperties: { number: nums[i] },
                        },
                        children: [{ type: 'text', value: `[${nums[i]}]` }],
                    });
                }

                lastIndex = match.index + match[0].length;
            }

            if (parts.length > 0) {
                // Remaining text after last citation
                if (lastIndex < node.value.length) {
                    parts.push({ type: 'text', value: node.value.slice(lastIndex) });
                }
                parent.children.splice(index, 1, ...parts);
                return index + parts.length;
            }
        });
    };
}
