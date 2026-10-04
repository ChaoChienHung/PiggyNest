import { apiClient } from './client';

export const backupApi = {
    export: async (): Promise<void> => {
        const response = await apiClient.get('/backup/export', { responseType: 'blob' });
        const url = URL.createObjectURL(response.data);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'piggynest-backup.xlsx';
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
    },
    import: async (file: File): Promise<{ piggy_banks_imported: number; transactions_imported: number; categories_imported: number }> => {
        const form = new FormData();
        form.append('file', file);
        const { data } = await apiClient.post('/backup/import', form, {
            headers: { 'Content-Type': undefined },
        });
        return data;
    },
};
