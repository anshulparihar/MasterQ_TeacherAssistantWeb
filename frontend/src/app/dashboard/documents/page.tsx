'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { DocumentUpload } from '@/components/DocumentUpload';
import { Trash2, FileText, File as FileIcon, Loader2 } from 'lucide-react';
import { useAuthStore } from '@/store/auth';

interface Doc {
  id: string;
  filename: string;
  doc_type: string;
  status: string;
  created_at: string;
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Doc[]>([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuthStore();

  const fetchDocuments = async () => {
    try {
      setLoading(true);
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
  }, [user]);

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this document?')) return;
    try {
      await api.delete(`/documents/${id}`);
      setDocuments(documents.filter(d => d.id !== id));
    } catch (error) {
      console.error("Failed to delete", error);
    }
  };

  return (
    <div className="container mx-auto py-8 space-y-8 px-4">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Documents</h1>
        <p className="text-muted-foreground mt-2">
          Manage your knowledge base for question generation and chatbot interactions.
        </p>
      </div>

      <DocumentUpload 
        isAdminMode={user?.is_admin} 
        onUploadComplete={fetchDocuments} 
      />

      <div className="space-y-4">
        <h2 className="text-xl font-semibold">Your Uploaded Documents</h2>
        {loading ? (
          <div className="flex items-center justify-center p-8">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center p-8 border rounded-lg bg-card text-muted-foreground">
            No documents uploaded yet.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {documents.map((doc) => (
              <div key={doc.id} className="p-4 border rounded-xl bg-card shadow-sm flex flex-col space-y-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-primary/10 rounded-lg text-primary">
                      <FileIcon className="h-6 w-6" />
                    </div>
                    <div>
                      <p className="font-medium truncate max-w-[150px]" title={doc.filename}>
                        {doc.filename}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(doc.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <button 
                    onClick={() => handleDelete(doc.id)}
                    className="p-2 text-muted-foreground hover:text-destructive transition-colors rounded-md hover:bg-destructive/10"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
                
                <div className="flex items-center space-x-2 pt-2 border-t">
                  <span className="text-sm font-medium">Status:</span>
                  <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                    doc.status === 'ready' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                    doc.status === 'processing' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' :
                    'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                  }`}>
                    {doc.status?.toUpperCase() || 'UNKNOWN'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
