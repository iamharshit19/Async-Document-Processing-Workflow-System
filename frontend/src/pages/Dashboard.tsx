import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { format } from 'date-fns';
import { Search, Filter, Upload, DownloadCloud, ChevronRight } from 'lucide-react';
import { getDocuments, getExportUrl } from '../api/client';
import { JobStatus, type Document, type PaginatedDocuments } from '../types';
import UploadModal from '../components/UploadModal';

export default function Dashboard() {
    const [data, setData] = useState<PaginatedDocuments | null>(null);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [statusFilter, setStatusFilter] = useState<string>('');
    const [sortBy, setSortBy] = useState<string>('created_at');
    const [sortOrder, setSortOrder] = useState<string>('desc');
    const [isUploadOpen, setIsUploadOpen] = useState(false);

    const fetchDocs = async () => {
        setLoading(true);
        try {
            const res = await getDocuments(0, 50, search, statusFilter as JobStatus || undefined, sortBy, sortOrder);
            setData(res);
        } catch (error) {
            console.error("Error fetching docs", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDocs();
        
        const interval = setInterval(fetchDocs, 5000);
        return () => clearInterval(interval);
    }, [search, statusFilter, sortBy, sortOrder]);

    const toggleSort = (field: string) => {
        if (sortBy === field) {
            setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
        } else {
            setSortBy(field);
            setSortOrder('desc');
        }
    };

    return (
        <div className="app-container">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                <div>
                    <h1 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '0.5rem' }}>Documents Pipeline</h1>
                    <p style={{ color: 'var(--text-secondary)' }}>Manage your asynchronous document processing.</p>
                </div>
                <div style={{ display: 'flex', gap: '1rem' }}>
                    <a href={getExportUrl('csv')} className="btn btn-outline" target="_blank" rel="noreferrer">
                        <DownloadCloud size={18} /> Export CSV
                    </a>
                    <a href={getExportUrl('json')} className="btn btn-outline" target="_blank" rel="noreferrer">
                        <DownloadCloud size={18} /> Export JSON
                    </a>
                    <button className="btn btn-primary" onClick={() => setIsUploadOpen(true)}>
                        <Upload size={18} /> Upload Document
                    </button>
                </div>
            </div>

            <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '2rem', display: 'flex', gap: '1rem' }}>
                <div style={{ flex: 1, position: 'relative' }}>
                    <Search size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
                    <input 
                        type="text" 
                        placeholder="Search filenames..." 
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        style={{ paddingLeft: '2.5rem' }}
                    />
                </div>
                <div style={{ width: '200px', position: 'relative' }}>
                    <Filter size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
                    <select 
                        value={statusFilter} 
                        onChange={(e) => setStatusFilter(e.target.value)}
                        style={{ paddingLeft: '2.5rem', appearance: 'none' }}
                    >
                        <option value="">All Statuses</option>
                        <option value={JobStatus.QUEUED}>Queued</option>
                        <option value={JobStatus.PROCESSING}>Processing</option>
                        <option value={JobStatus.COMPLETED}>Completed</option>
                        <option value={JobStatus.FAILED}>Failed</option>
                    </select>
                </div>
            </div>

            <div className="glass-panel" style={{ overflowX: 'auto' }}>
                <table className="data-table">
                    <thead>
                        <tr>
                            <th onClick={() => toggleSort('filename')} style={{ cursor: 'pointer' }}>
                                Filename {sortBy === 'filename' ? (sortOrder === 'asc' ? '↑' : '↓') : ''}
                            </th>
                            <th onClick={() => toggleSort('status')} style={{ cursor: 'pointer' }}>
                                Status {sortBy === 'status' ? (sortOrder === 'asc' ? '↑' : '↓') : ''}
                            </th>
                            <th onClick={() => toggleSort('created_at')} style={{ cursor: 'pointer' }}>
                                Uploaded At {sortBy === 'created_at' ? (sortOrder === 'asc' ? '↑' : '↓') : ''}
                            </th>
                            <th>Finalized</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading && !data ? (
                            <tr><td colSpan={5} style={{ textAlign: 'center', padding: '2rem' }}><div className="loading-spinner" style={{ margin: '0 auto' }}></div></td></tr>
                        ) : data?.items.length === 0 ? (
                            <tr><td colSpan={5} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>No documents found.</td></tr>
                        ) : (
                            data?.items.map((doc: Document) => (
                                <tr key={doc.id}>
                                    <td style={{ fontWeight: 500 }}>{doc.filename}</td>
                                    <td>
                                        <span className={`status-badge status-${doc.status}`}>
                                            {doc.status}
                                        </span>
                                    </td>
                                    <td style={{ color: 'var(--text-secondary)' }}>
                                        {format(new Date(doc.created_at), 'MMM dd, yyyy HH:mm')}
                                    </td>
                                    <td>
                                        {doc.extracted_data?.is_finalized ? 
                                            <span style={{ color: 'var(--success)' }}>Yes</span> : 
                                            <span style={{ color: 'var(--text-secondary)' }}>No</span>}
                                    </td>
                                    <td>
                                        <Link to={`/documents/${doc.id}`} className="btn btn-outline" style={{ padding: '0.4rem 0.8rem' }}>
                                            View <ChevronRight size={16} />
                                        </Link>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            <UploadModal 
                isOpen={isUploadOpen} 
                onClose={() => setIsUploadOpen(false)} 
                onUploadSuccess={() => fetchDocs()} 
            />
        </div>
    );
}
