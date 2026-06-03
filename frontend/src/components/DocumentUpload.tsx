'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, File, X, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { api } from '@/lib/api';

interface DocumentUploadProps {
  isAdminMode?: boolean;
  onUploadComplete?: () => void;
}

export function DocumentUpload({ isAdminMode = false, onUploadComplete }: DocumentUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<'idle' | 'uploading' | 'processing' | 'ready' | 'failed'>('idle');
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
      setStatus('idle');
      setError(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt', '.md']
    },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024 // 50MB
  });

  const pollStatus = async (documentId: string) => {
    const interval = setInterval(async () => {
      try {
        const res = await api.get(`/documents/${documentId}/status`);
        if (res.data.status === 'ready') {
          setStatus('ready');
          clearInterval(interval);
          if (onUploadComplete) onUploadComplete();
        } else if (res.data.status === 'failed') {
          setStatus('failed');
          setError('Document processing failed.');
          clearInterval(interval);
        }
      } catch (err) {
        clearInterval(interval);
      }
    }, 3000);
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setStatus('uploading');
    setProgress(0);

    const formData = new FormData();
    formData.append('file', file);

    const endpoint = isAdminMode ? '/documents/admin/upload' : '/documents/user/upload';

    try {
      const response = await api.post(endpoint, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1));
          setProgress(percentCompleted);
        }
      });

      setStatus('processing');
      const documentId = response.data.document_id;
      pollStatus(documentId);
    } catch (err: any) {
      setStatus('failed');
      setError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto p-4 border rounded-xl bg-card text-card-foreground shadow-sm">
      {!file ? (
        <div 
          {...getRootProps()} 
          className={`border-2 border-dashed rounded-lg p-10 text-center cursor-pointer transition-colors ${
            isDragActive ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50'
          }`}
        >
          <input {...getInputProps()} />
          <UploadCloud className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium">Drag & drop your document here</h3>
          <p className="text-sm text-muted-foreground mt-1">
            Supports PDF, DOCX, TXT up to 50MB
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 border rounded-lg bg-muted/50">
            <div className="flex items-center space-x-3">
              <File className="h-8 w-8 text-primary" />
              <div>
                <p className="font-medium text-sm truncate max-w-[200px] sm:max-w-xs">{file.name}</p>
                <p className="text-xs text-muted-foreground">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
              </div>
            </div>
            {status === 'idle' && (
              <button 
                onClick={() => setFile(null)} 
                className="p-1 text-muted-foreground hover:text-destructive"
              >
                <X className="h-5 w-5" />
              </button>
            )}
          </div>

          {status === 'idle' && (
            <button
              onClick={handleUpload}
              className="w-full py-2 bg-primary text-primary-foreground rounded-md font-medium hover:bg-primary/90"
            >
              Upload Document
            </button>
          )}

          {status === 'uploading' && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Uploading...</span>
                <span>{progress}%</span>
              </div>
              <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
                <div 
                  className="h-full bg-primary transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          {status === 'processing' && (
            <div className="flex items-center justify-center space-x-2 text-primary py-4">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span>Processing document and generating embeddings...</span>
            </div>
          )}

          {status === 'ready' && (
            <div className="flex items-center justify-center space-x-2 text-green-600 py-4">
              <CheckCircle2 className="h-5 w-5" />
              <span>Document is ready!</span>
            </div>
          )}

          {status === 'failed' && (
            <div className="flex flex-col items-center justify-center space-y-2 text-destructive py-4">
              <div className="flex items-center space-x-2">
                <AlertCircle className="h-5 w-5" />
                <span>{error || 'Processing failed'}</span>
              </div>
              <button 
                onClick={() => { setFile(null); setStatus('idle'); }}
                className="text-sm underline"
              >
                Try again
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
