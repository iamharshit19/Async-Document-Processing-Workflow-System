export const JobStatus = {
    QUEUED: 'Queued',
    PROCESSING: 'Processing',
    COMPLETED: 'Completed',
    FAILED: 'Failed',
} as const;

export type JobStatus = typeof JobStatus[keyof typeof JobStatus];

export interface ExtractedData {
    id: number;
    document_id: number;
    title: string | null;
    category: string | null;
    summary: string | null;
    keywords: string[] | null;
    is_finalized: boolean;
}

export interface Document {
    id: number;
    filename: string;
    content_type: string;
    size: number;
    status: JobStatus;
    created_at: string;
    updated_at: string;
    extracted_data: ExtractedData | null;
}

export interface PaginatedDocuments {
    items: Document[];
    total: number;
}
