import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, CheckCircle, RefreshCw, Save, XCircle } from 'lucide-react';
import { getDocument, updateExtractedData, finalizeDocument, retryDocumentJob, cancelDocumentJob, getProgressStreamUrl } from '../api/client';
import { JobStatus, type Document } from '../types';

export default function DocumentDetail() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const [doc, setDoc] = useState<Document | null>(null);
    const [loading, setLoading] = useState(true);

    const [progressEvent, setProgressEvent] = useState<string>('');
    const [progressLogs, setProgressLogs] = useState<{time: string, event: string}[]>([]);
    const [liveSummary, setLiveSummary] = useState<string>('');

    
    const [formData, setFormData] = useState({
        title: '',
        category: '',
        summary: '',
        keywords: ''
    });

    const fetchDoc = async () => {
        try {
            const data = await getDocument(Number(id));
            setDoc(data);
            if (data.extracted_data) {
                setFormData({
                    title: data.extracted_data.title || '',
                    category: data.extracted_data.category || '',
                    summary: data.extracted_data.summary || '',
                    keywords: data.extracted_data.keywords?.join(', ') || ''
                });
            }
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDoc();
    }, [id]);

 
    useEffect(() => {
        if (!doc) return;
        if (doc.status === JobStatus.COMPLETED || doc.status === JobStatus.FAILED) return;

        const evtSource = new EventSource(getProgressStreamUrl(Number(id)));
        
        evtSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            setProgressEvent(data.event);
            
            if (data.event === 'token_stream') {
                setLiveSummary(prev => prev + data.payload.chunk);
            } else {
                let msg = data.event;
                if (data.payload?.error) msg += `: ${data.payload.error}`;
                if (data.payload?.reason) msg += `: ${data.payload.reason}`;
                setProgressLogs(prev => [...prev, { time: new Date().toLocaleTimeString(), event: msg }]);
            }
         
            if (data.event === 'job_completed' || data.event === 'job_failed') {
                setTimeout(fetchDoc, 1000);
            }
        };

        return () => evtSource.close();
    }, [doc?.status, id]);

    const handleSave = async () => {
        try {
            await updateExtractedData(Number(id), {
                title: formData.title,
                category: formData.category,
                summary: formData.summary,
                keywords: formData.keywords.split(',').map(k => k.trim()).filter(k => k)
            });
            alert('Saved successfully!');
            fetchDoc();
        } catch (error) {
            console.error(error);
            alert('Failed to save');
        }
    };

    const handleFinalize = async () => {
        if (window.confirm('Are you sure you want to finalize this record? No further edits will be allowed.')) {
            try {
                await finalizeDocument(Number(id));
                fetchDoc();
            } catch (error) {
                console.error(error);
                alert('Failed to finalize');
            }
        }
    };

    const handleRetry = async () => {
        try {
            await retryDocumentJob(Number(id));
            setProgressLogs([]);
            fetchDoc();
        } catch (error) {
            console.error(error);
            alert('Failed to retry');
        }
    };

    const handleCancel = async () => {
        if (window.confirm('Are you sure you want to cancel this job?')) {
            try {
                await cancelDocumentJob(Number(id));
                fetchDoc();
            } catch (error) {
                console.error(error);
                alert('Failed to cancel');
            }
        }
    };

    if (loading) return <div className="app-container"><div className="loading-spinner"></div></div>;
    if (!doc) return <div className="app-container">Document not found.</div>;

    const isProcessing = doc.status === JobStatus.QUEUED || doc.status === JobStatus.PROCESSING;
    const isFinalized = doc.extracted_data?.is_finalized;

    return (
        <div className="app-container">
            <button className="btn btn-outline" onClick={() => navigate('/')} style={{ marginBottom: '2rem' }}>
                <ArrowLeft size={18} /> Back to Dashboard
            </button>

            <div className="glass-panel" style={{ padding: '2rem', marginBottom: '2rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
                    <div>
                        <h2 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '0.5rem' }}>{doc.filename}</h2>
                        <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                            Uploaded: {new Date(doc.created_at).toLocaleString()} | Size: {(doc.size / 1024).toFixed(2)} KB
                        </div>
                    </div>
                    <div>
                        <span className={`status-badge status-${doc.status}`} style={{ fontSize: '1rem', padding: '0.5rem 1rem' }}>
                            {doc.status}
                        </span>
                    </div>
                </div>

                {isProcessing && (
                    <div style={{ marginTop: '2rem', background: '#f9fafb', border: '1px solid #e5e7eb', padding: '1.5rem', borderRadius: '12px' }}>
                        <h3 style={{ marginBottom: '1rem', fontSize: '1rem', color: 'var(--primary)' }}>
                            Live Progress: <span className="animate-pulse">{progressEvent || doc.status}...</span>
                        </h3>
                        <div className="progress-container">
                            <div className="progress-bar" style={{ width: progressEvent === 'job_started' ? '20%' : progressEvent.includes('parsing') ? '50%' : progressEvent.includes('extraction') ? '80%' : progressEvent === 'token_stream' ? '90%' : '100%' }}></div>
                        </div>
                        {liveSummary && (
                            <div style={{ marginTop: '1.5rem', background: '#ffffff', padding: '1rem', borderRadius: '8px', border: '1px solid #e5e7eb', borderLeft: '3px solid var(--primary)' }}>
                                <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--primary)', marginBottom: '0.5rem', fontWeight: 600 }}>AI Generating Summary</div>
                                <div style={{ lineHeight: 1.6, color: 'var(--text-primary)' }}>{liveSummary}<span className="animate-pulse">|</span></div>
                            </div>
                        )}
                        <div style={{ marginTop: '1rem', maxHeight: '100px', overflowY: 'auto', fontSize: '0.75rem', color: 'var(--text-secondary)', fontFamily: 'monospace' }}>
                            {progressLogs.map((log, i) => (
                                <div key={i}>[{log.time}] - {log.event}</div>
                            ))}
                        </div>
                        <button className="btn btn-outline" onClick={handleCancel} style={{ marginTop: '1rem', borderColor: 'var(--danger)', color: 'var(--danger)' }}>
                            <XCircle size={18} /> Cancel Job
                        </button>
                    </div>
                )}

                {doc.status === JobStatus.FAILED && (
                    <div style={{ marginTop: '2rem', background: '#fef2f2', border: '1px solid var(--danger)', padding: '1.5rem', borderRadius: '12px' }}>
                        <h3 style={{ color: 'var(--danger)', marginBottom: '1rem' }}>Processing Failed</h3>
                        <button className="btn btn-outline" onClick={handleRetry} style={{ borderColor: 'var(--danger)', color: 'var(--danger)' }}>
                            <RefreshCw size={18} /> Retry Job
                        </button>
                    </div>
                )}
            </div>

            {doc.status === JobStatus.COMPLETED && doc.extracted_data && (
                <div className="glass-panel" style={{ padding: '2rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                        <h3 style={{ fontSize: '1.25rem', fontWeight: 600 }}>Review Extracted Data</h3>
                        {isFinalized && <span style={{ color: 'var(--success)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}><CheckCircle size={18} /> Record Finalized</span>}
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
                        <div>
                            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Title</label>
                            <input 
                                type="text" 
                                value={formData.title} 
                                onChange={e => setFormData({...formData, title: e.target.value})}
                                disabled={isFinalized}
                            />
                        </div>
                        <div>
                            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Category</label>
                            <input 
                                type="text" 
                                value={formData.category} 
                                onChange={e => setFormData({...formData, category: e.target.value})}
                                disabled={isFinalized}
                            />
                        </div>
                        <div style={{ gridColumn: '1 / -1' }}>
                            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Summary</label>
                            <textarea 
                                value={formData.summary} 
                                onChange={e => setFormData({...formData, summary: e.target.value})}
                                disabled={isFinalized}
                                rows={4}
                            />
                        </div>
                        <div style={{ gridColumn: '1 / -1' }}>
                            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Keywords (comma separated)</label>
                            <input 
                                type="text" 
                                value={formData.keywords} 
                                onChange={e => setFormData({...formData, keywords: e.target.value})}
                                disabled={isFinalized}
                            />
                        </div>
                    </div>

                    {!isFinalized && (
                        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end', paddingTop: '1.5rem', borderTop: '1px solid var(--panel-border)' }}>
                            <button className="btn btn-outline" onClick={handleSave}>
                                <Save size={18} /> Save Draft
                            </button>
                            <button className="btn btn-success" onClick={handleFinalize}>
                                <CheckCircle size={18} /> Finalize Record
                            </button>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
