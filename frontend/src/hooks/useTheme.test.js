import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useTheme } from './useTheme';

const mockStorage = {};
const mockLocalStorage = {
    getItem: vi.fn((key) => mockStorage[key] || null),
    setItem: vi.fn((key, value) => { mockStorage[key] = value; }),
    removeItem: vi.fn((key) => { delete mockStorage[key]; }),
};

Object.defineProperty(window, 'localStorage', { value: mockLocalStorage });

describe('useTheme', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        Object.keys(mockStorage).forEach(k => delete mockStorage[k]);
        document.documentElement.removeAttribute('data-theme');
    });

    it('defaults to dark theme', () => {
        const { result } = renderHook(() => useTheme());
        expect(result.current.theme).toBe('dark');
    });

    it('reads theme from localStorage', () => {
        mockStorage['mentori_theme'] = 'light';
        const { result } = renderHook(() => useTheme());
        expect(result.current.theme).toBe('light');
    });

    it('toggles between dark and light', () => {
        const { result } = renderHook(() => useTheme());
        expect(result.current.theme).toBe('dark');

        act(() => { result.current.toggleTheme(); });
        expect(result.current.theme).toBe('light');

        act(() => { result.current.toggleTheme(); });
        expect(result.current.theme).toBe('dark');
    });

    it('persists theme to localStorage', () => {
        const { result } = renderHook(() => useTheme());
        act(() => { result.current.toggleTheme(); });
        expect(mockLocalStorage.setItem).toHaveBeenCalledWith('mentori_theme', 'light');
    });

    it('sets data-theme attribute on document', () => {
        const { result } = renderHook(() => useTheme());
        act(() => { result.current.setTheme('light'); });
        expect(document.documentElement.getAttribute('data-theme')).toBe('light');
    });
});
