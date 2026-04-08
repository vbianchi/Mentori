/**
 * Parse the "Sources" section from an AI response to extract citation data.
 * Expected format:
 * [1] filename.pdf, page N: "quoted text..."
 */
export function parseSources(markdownText) {
    const sources = {};
    if (!markdownText) return sources;

    // Find the Sources section
    const sourcesMatch = markdownText.match(/##\s*Sources[^\n]*\n([\s\S]*?)(?=\n##|\n---|\s*$)/i);
    if (!sourcesMatch) return sources;

    const sourcesText = sourcesMatch[1];

    // Match individual source lines: [N] filename, page P: "text..."
    const lineRegex = /\[(\d+)\]\s*([^,\n]+?)(?:,\s*page\s*(\d+))?:\s*"([^"]+?)(?:\.\.\.)?"/g;
    let match;

    while ((match = lineRegex.exec(sourcesText)) !== null) {
        sources[match[1]] = {
            file: match[2].trim(),
            page: match[3] ? parseInt(match[3]) : undefined,
            text: match[4].trim(),
        };
    }

    return sources;
}
