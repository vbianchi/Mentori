import { describe, it, expect } from 'vitest';
import { feedToMarkdown, extractFollowUpSuggestions } from './exportChat';

describe('feedToMarkdown', () => {
    it('exports user and assistant messages', () => {
        const feed = [
            { type: 'user', content: 'What is RAG?' },
            { type: 'synthesis', content: 'RAG stands for Retrieval-Augmented Generation.' },
        ];
        const md = feedToMarkdown(feed, 'Test Task');
        expect(md).toContain('# Test Task');
        expect(md).toContain('## User');
        expect(md).toContain('What is RAG?');
        expect(md).toContain('## Assistant');
        expect(md).toContain('RAG stands for Retrieval-Augmented Generation.');
    });

    it('includes thinking in details tag', () => {
        const feed = [
            { type: 'synthesis', content: 'Answer', thinking: 'Let me think...' },
        ];
        const md = feedToMarkdown(feed);
        expect(md).toContain('<details><summary>Thinking</summary>');
        expect(md).toContain('Let me think...');
    });

    it('handles empty feed', () => {
        const md = feedToMarkdown([], 'Empty');
        expect(md).toContain('# Empty');
        expect(md).not.toContain('## User');
    });

    it('exports tool steps with input/output', () => {
        const feed = [
            { type: 'step', toolName: 'web_search', toolInput: '{"query":"test"}', toolOutput: 'result' },
        ];
        const md = feedToMarkdown(feed);
        expect(md).toContain('### Tool: web_search');
        expect(md).toContain('"query": "test"');
        expect(md).toContain('result');
    });
});

describe('extractFollowUpSuggestions', () => {
    it('returns suggestions for content with citations', () => {
        const feed = [
            { type: 'synthesis', content: 'According to [1] and [2], the method is effective.' },
        ];
        const suggestions = extractFollowUpSuggestions(feed);
        expect(suggestions.length).toBeGreaterThan(0);
        expect(suggestions.some(s => s.toLowerCase().includes('source'))).toBe(true);
    });

    it('returns empty for empty feed', () => {
        expect(extractFollowUpSuggestions([])).toEqual([]);
    });

    it('returns max 3 suggestions', () => {
        const feed = [
            {
                type: 'synthesis',
                content: 'This method [1] has limitations [2]. The approach is novel.' +
                    ' '.repeat(1000) // long content
            },
        ];
        const suggestions = extractFollowUpSuggestions(feed);
        expect(suggestions.length).toBeLessThanOrEqual(3);
    });
});
