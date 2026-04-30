import { useState, useRef } from 'react';
import { UploadCloud, X } from 'lucide-react';
import { uploadDocument } from '../api/client';

interface UploadModalProps {
    isOpen: boolean;
    onClose: () => void;
    onUploadSuccess: () => void;
}

export default function UploadModal({ isOpen, onClose, onUploadSuccess }: UploadModalProps) {
    const [isDragging, setIsDragging] = useState(false);
    const [file, setFile] = useState<File | null>(null);
    const [isUploading, setIsUploading] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    if (!isOpen) return null;

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            setFile(e.dataTransfer.files[0]);
        }
    };

    const handleUpload = async () => {
        if (!file) return;
        setIsUploading(true);
        try {
            await uploadDocument(file);
            onUploadSuccess();
            onClose();
        } catch (error) {
            console.error("Upload failed", error);
            alert("Upload failed. Please try again.");
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50
        }}>
            <div className="glass-panel" style={{ width: '100%', maxWidth: '500px', padding: '2rem', position: 'relative' }}>
                <button onClick={onClose} style={{ position: 'absolute', top: '1rem', right: '1rem', background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                    <X size={24} />
                </button>
                <h2 style={{ marginBottom: '1.5rem', fontWeight: 600 }}>Upload Document</h2>
                
                <div 
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                    style={{
                        border: `2px dashed ${isDragging ? 'var(--primary)' : 'var(--panel-border)'}`,
                        borderRadius: '12px',
                        padding: '3rem 2rem',
                        textAlign: 'center',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                        background: isDragging ? 'rgba(59, 130, 246, 0.1)' : 'rgba(0,0,0,0.2)'
                    }}
                >
                    <input 
                        type="file" 
                        ref={fileInputRef} 
                        style={{ display: 'none' }} 
                        onChange={(e) => setFile(e.target.files?.[0] || null)}
                    />
                    <UploadCloud size={48} color={isDragging ? 'var(--primary)' : 'var(--text-secondary)'} style={{ margin: '0 auto 1rem' }} />
                    <p style={{ color: 'var(--text-secondary)' }}>
                        {file ? file.name : "Drag & drop a file here, or click to select"}
                    </p>
                </div>

                <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
                    <button className="btn btn-outline" onClick={onClose} disabled={isUploading}>Cancel</button>
                    <button className="btn btn-primary" onClick={handleUpload} disabled={!file || isUploading}>
                        {isUploading ? <div className="loading-spinner"></div> : "Upload & Process"}
                    </button>
                </div>
            </div>
        </div>
    );
}
