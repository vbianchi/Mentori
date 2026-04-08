import { describe, it, expect } from 'vitest';
import { parseSources } from './parseSources';

describe('parseSources', () => {
    it('parses standard source format', () => {
        const text = `Some answer text [1] and [2].

## Sources (from your corpus)

[1] 15_rabies_tanzania.pdf, page 0: "Reducing spatial heterogeneity in coverage improves..."
[2] 02_snakemake.pdf, page 3: "Snakemake determines a directed acyclic graph..."
`;
        const sources = parseSources(text);
        expect(sources['1']).toEqual({
            file: '15_rabies_tanzania.pdf',
            page: 0,
            text: 'Reducing spatial heterogeneity in coverage improves',
        });
        expect(sources['2']).toEqual({
            file: '02_snakemake.pdf',
            page: 3,
            text: 'Snakemake determines a directed acyclic graph',
        });
    });

    it('returns empty object for text without sources', () => {
        expect(parseSources('No sources here')).toEqual({});
        expect(parseSources('')).toEqual({});
        expect(parseSources(null)).toEqual({});
    });

    it('handles sources with "(unverified)" suffix', () => {
        const text = `Answer [1].

## Sources (from your corpus)

[1] 12_hpai_netherlands.pdf, page 0: "Comparison of the Clinical Manifestation..." (unverified)
`;
        const sources = parseSources(text);
        expect(sources['1'].file).toBe('12_hpai_netherlands.pdf');
        expect(sources['1'].text).toBe('Comparison of the Clinical Manifestation');
    });
});
