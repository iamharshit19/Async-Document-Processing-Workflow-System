import axios from 'axios';
import { JobStatus, type Document, type PaginatedDocuments } from '../types';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
    baseURL: API_BASE_URL,
});

export const getDocuments = async (skip: number = 0, limit: number = 20, search?: string, status?: JobStatus): Promise<PaginatedDocuments> => {
    const params = new URLSearchParams({ skip: skip.toString(), limit: limit.toString() });
    if (search) params.append('search', search);
    if (status) params.append('status', status);

    const response = await api.get(`/documents?${params.toString()}`);
    return response.data;
};

export const getDocument = async (id: number): Promise<Document> => {
    const response = await api.get(`/documents/${id}`);
    return response.data;
};

export const uploadDocument = async (file: File): Promise<Document> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/documents/upload', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    return response.data;
};

export const updateExtractedData = async (id: number, data: Partial<Document['extracted_data']>): Promise<Document> => {
    const response = await api.put(`/documents/${id}/data`, data);
    return response.data;
};

export const finalizeDocument = async (id: number): Promise<Document> => {
    const response = await api.post(`/documents/${id}/finalize`);
    return response.data;
};

export const retryDocumentJob = async (id: number): Promise<Document> => {
    const response = await api.post(`/documents/${id}/retry`);
    return response.data;
};

export const getExportUrl = (format: 'csv' | 'json') => `${API_BASE_URL}/documents/export/${format}`;
export const getProgressStreamUrl = (id: number) => `${API_BASE_URL}/progress/${id}/stream`;
