'use client';

import { useEffect, useState, useCallback } from 'react';
import { api } from '@/lib/api';
import { Trash2, FileText, UploadCloud, X, CheckCircle2, Loader2, Upload, AlertTriangle, FolderOpen } from 'lucide-react';
import { useAuthStore } from '@/store/auth';
import { BackButton } from '@/components/ui/BackButton';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { useDropzone } from 'react-dropzone';
import toast from 'react-hot-toast';

interface Doc {
  id: string;
  filename: string;
  doc_type: string;
  status: string;
  created_at: string;
  subject?: string;
  level?: string;
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Doc[]>([]);
  const [loading, setLoading] = useState(true);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState<string | null>(null);
  const { user } = useAuthStore();

  const fetchDocuments = async () => {
    try {
      const endpoint = user?.is_admin ? '/documents/admin' : '/documents/user/me';
      const response = await api.get(endpoint);
      setDocuments(response.data);
    } catch (error) {
      console.error("Failed to fetch documents", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      fetchDocuments();
    }
    // Set up polling for processing documents
    const interval = setInterval(() => {
      if (user) {
        fetchDocuments();
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [user]);

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/documents/${id}`);
      setDocuments(documents.filter(d => d.id !== id));
      setShowDeleteModal(null);
      toast.success('Document deleted successfully');
    } catch (error) {
      console.error("Failed to delete", error);
      toast.error('Failed to delete document');
    }
  };

  // Upload Modal State
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [levels, setLevels] = useState<any[]>([]);

  useEffect(() => {
    if (showUploadModal) {
      api.get('/subjects').then(res => setSubjects(res.data)).catch(() => {});
    }
  }, [showUploadModal]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
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

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);

    const formData = new FormData();
    formData.append('file', file);
    // Note: If backend supports these, they go here
    // formData.append('subject_id', selectedSubject);

    const endpoint = user?.is_admin ? '/documents/admin/upload' : '/documents/user/upload';

    try {
      await api.post(endpoint, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      toast.success('Document uploaded! Processing in background...');
      setShowUploadModal(false);
      setFile(null);
      fetchDocuments();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="animate-in fade-in slide-in-from-top-4 duration-300">
      <BackButton />
      
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">My Documents</h1>
          <p className="text-sm text-slate-500 mt-1">
            Upload and manage your curriculum materials.
          </p>
        </div>
        <Button onClick={() => setShowUploadModal(true)} className="bg-primary hover:bg-primary/90 shadow-sm rounded-xl px-5 h-11">
          <Upload className="h-4 w-4 mr-2" />
          Upload Document
        </Button>
      </div>

      <Card className="border border-slate-200 shadow-sm bg-white rounded-2xl overflow-hidden">
        {loading ? (
          <div className="flex justify-center items-center h-48">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : documents.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
            <FolderOpen className="h-12 w-12 text-slate-300 mb-4" />
            <h3 className="text-lg font-semibold text-slate-900">No documents yet</h3>
            <p className="text-slate-500 text-sm mt-1 max-w-sm">
              Upload your syllabi, textbooks, and past papers to generate AI question papers.
            </p>
            <Button onClick={() => setShowUploadModal(true)} variant="outline" className="mt-6 rounded-xl">
              <Upload className="h-4 w-4 mr-2" />
              Upload your first document
            </Button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-4 font-semibold">File</th>
                  <th className="px-6 py-4 font-semibold">Subject</th>
                  <th className="px-6 py-4 font-semibold">Level</th>
                  <th className="px-6 py-4 font-semibold">Status</th>
                  <th className="px-6 py-4 font-semibold">Uploaded</th>
                  <th className="px-6 py-4 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <FileText className="h-5 w-5 text-slate-400 shrink-0" />
                        <span className="font-medium text-slate-900 truncate max-w-[200px]" title={doc.filename}>{doc.filename}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-slate-500">{typeof doc.subject === 'object' ? (doc.subject as any)?.name : doc.subject || '-'}</td>
                    <td className="px-6 py-4 text-slate-500">{typeof doc.level === 'object' ? (doc.level as any)?.name : doc.level || '-'}</td>
                    <td className="px-6 py-4">
                      {doc.status === 'ready' && (
                        <span className="inline-flex items-center gap-1.5 bg-green-50 text-green-700 border border-green-200 px-2.5 py-1 rounded-full text-xs font-semibold">
                          <CheckCircle2 className="h-3.5 w-3.5" /> Ready
                        </span>
                      )}
                      {doc.status === 'processing' && (
                        <span className="inline-flex items-center gap-1.5 bg-amber-50 text-amber-700 border border-amber-200 px-2.5 py-1 rounded-full text-xs font-semibold animate-pulse">
                          <Loader2 className="h-3.5 w-3.5 animate-spin" /> Processing
                        </span>
                      )}
                      {doc.status === 'failed' && (
                        <span className="inline-flex items-center gap-1.5 bg-red-50 text-red-700 border border-red-200 px-2.5 py-1 rounded-full text-xs font-semibold">
                          <X className="h-3.5 w-3.5" /> Failed
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-slate-500">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button 
                        onClick={() => setShowDeleteModal(doc.id)}
                        className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        title="Delete Document"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-white w-full max-w-lg rounded-2xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between p-6 border-b border-slate-100">
              <h2 className="text-xl font-bold text-slate-900">Upload Document</h2>
              <button onClick={() => { setShowUploadModal(false); setFile(null); }} className="text-slate-400 hover:text-slate-600 transition-colors rounded-full p-1 hover:bg-slate-100">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-6 max-h-[70vh] overflow-y-auto">
              {!file ? (
                <div 
                  {...getRootProps()} 
                  className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors ${
                    isDragActive ? 'border-primary bg-primary/5' : 'border-slate-200 hover:border-primary/50 hover:bg-slate-50'
                  }`}
                >
                  <input {...getInputProps()} />
                  <UploadCloud className="mx-auto h-12 w-12 text-slate-400 mb-4" />
                  <h3 className="text-base font-semibold text-slate-900">Drag & drop files here, or click to browse</h3>
                  <p className="text-sm text-slate-500 mt-1">Accepted: PDF, DOCX, TXT, MD. Max: 50MB.</p>
                </div>
              ) : (
                <div className="flex items-center justify-between p-4 border border-slate-200 rounded-xl bg-slate-50">
                  <div className="flex items-center space-x-3 overflow-hidden">
                    <FileText className="h-8 w-8 text-primary shrink-0" />
                    <div className="min-w-0">
                      <p className="font-semibold text-sm text-slate-900 truncate">{file.name}</p>
                      <p className="text-xs text-slate-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                    </div>
                  </div>
                  <button onClick={() => setFile(null)} className="p-2 text-slate-400 hover:text-red-500 rounded-lg hover:bg-red-50 transition-colors shrink-0">
                    <X className="h-4 w-4" />
                  </button>
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-1.5">Assign to Subject</label>
                  <select className="w-full h-11 rounded-xl border border-slate-200 px-3 text-sm focus:ring-primary focus:border-primary bg-white">
                    <option value="">Select a subject...</option>
                    {subjects.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-1.5">Academic Level</label>
                  <select className="w-full h-11 rounded-xl border border-slate-200 px-3 text-sm focus:ring-primary focus:border-primary bg-white">
                    <option value="">Select level...</option>
                    <option value="high-school">High School</option>
                    <option value="undergraduate">Undergraduate</option>
                    <option value="postgraduate">Postgraduate</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="p-6 border-t border-slate-100 bg-slate-50 flex justify-end gap-3">
              <Button variant="outline" onClick={() => { setShowUploadModal(false); setFile(null); }} className="rounded-xl h-11 px-6">
                Cancel
              </Button>
              <Button onClick={handleUpload} disabled={!file || uploading} className="rounded-xl h-11 px-6 bg-primary hover:bg-primary/90 text-white shadow-sm">
                {uploading ? (
                  <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Uploading...</>
                ) : (
                  'Upload'
                )}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-white w-full max-w-sm rounded-2xl shadow-2xl p-6 text-center animate-in zoom-in-95 duration-200">
            <div className="mx-auto w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mb-4">
              <AlertTriangle className="h-6 w-6 text-red-600" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 mb-2">Delete Document?</h3>
            <p className="text-sm text-slate-500 mb-6">This action cannot be undone. This will permanently delete the document and its embeddings.</p>
            <div className="flex gap-3 justify-center">
              <Button variant="outline" onClick={() => setShowDeleteModal(null)} className="rounded-xl h-11 px-6 flex-1">
                Cancel
              </Button>
              <Button variant="destructive" onClick={() => handleDelete(showDeleteModal)} className="rounded-xl h-11 px-6 flex-1 bg-red-600 hover:bg-red-700">
                Delete
              </Button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
