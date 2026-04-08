import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import CollectionSettingsTab from './CollectionSettingsTab';
import config from '../../config';

// Mock config
vi.mock('../../config', () => ({
    default: {
        API_BASE_URL: 'http://localhost:8000/api'
    }
}));

describe('CollectionSettingsTab', () => {
    beforeEach(() => {
        vi.resetAllMocks();
        global.fetch = vi.fn();
        global.localStorage = {
            getItem: vi.fn(),
            setItem: vi.fn()
        };
        // Mock token
        global.localStorage.getItem.mockReturnValue('fake-token');
    });

    it('renders and fetches indexes', async () => {
        const mockIndexes = [
            { id: '1', name: 'Bio Research', status: 'READY', file_count: 5, created_at: '2023-01-01', estimated_time_seconds: 0 }
        ];

        global.fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => mockIndexes
        });

        render(<CollectionSettingsTab />);

        // Assert initial load
        expect(screen.getByText(/Knowledge Base/i)).toBeInTheDocument();

        // Wait for data
        await waitFor(() => {
            expect(screen.getByText('Bio Research')).toBeInTheDocument();
            expect(screen.getByText('Ready')).toBeInTheDocument();
        });

        expect(global.fetch).toHaveBeenCalledWith(
            'http://localhost:8000/api/rag/indexes/',
            expect.objectContaining({
                headers: { "Authorization": "Bearer fake-token" }
            })
        );
    });

    it('opens create modal and submits new index', async () => {
        // Mock List Fetch (Empty first)
        global.fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => []
        });

        render(<CollectionSettingsTab />);

        // Click New Index
        const newBtn = screen.getByText(/New Index/i);
        fireEvent.click(newBtn);

        // Check Modal
        expect(screen.getByText(/Create New Index/i)).toBeInTheDocument();

        // Fill Form
        fireEvent.change(screen.getByPlaceholderText(/e.g. Biology Research/i), { target: { value: 'My Index' } });
        fireEvent.change(screen.getByPlaceholderText(/\/Users\/you\/project\/paper1.pdf/i), { target: { value: '/tmp/test.pdf' } });

        // Mock Create Response
        global.fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ id: '2', status: 'PENDING' })
        });

        // Mock Refresh Fetch (After create)
        global.fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => [{ id: '2', name: 'My Index', status: 'PENDING', file_count: 1, created_at: 'Now' }]
        });

        // Submit
        fireEvent.click(screen.getByText(/Start Indexing/i));

        // Check if create API called
        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith(
                'http://localhost:8000/api/rag/indexes/',
                expect.objectContaining({
                    method: 'POST',
                    body: JSON.stringify({
                        name: 'My Index',
                        file_paths: ['/tmp/test.pdf']
                    })
                })
            );
        });
    });
});
