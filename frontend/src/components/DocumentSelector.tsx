'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';

interface DocumentSelectorProps {
  subjectId: string | null;
  selectedIds: string[];
  onChange: (ids: string[]) => void;
  fromThisOnly: boolean;
  onFromThisOnlyChange: (val: boolean) => void;
}

export function DocumentSelector({ subjectId, selectedIds, onChange, fromThisOnly, onFromThisOnlyChange }: DocumentSelectorProps) {
  
  const { data: documents = [], isLoading: loading } = useQuery({
    queryKey: ['user-documents', subjectId],
    queryFn: async () => {
      const url = subjectId 
        ? `http://localhost:8000/documents/user/me?subject_id=${subjectId}` 
        : `http://localhost:8000/documents/user/me`;
        
      const res = await fetch(url, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      if (!res.ok) throw new Error("Failed to fetch documents");
      return res.json();
    },
    enabled: !!subjectId, // Only fetch if subjectId is provided
  });

  const toggleSelection = (id: string) => {
    if (selectedIds.includes(id)) {
      const next = selectedIds.filter(x => x !== id);
      onChange(next);
      if (next.length === 0) {
        onFromThisOnlyChange(false); // Disable strict mode if empty
      }
    } else {
      onChange([...selectedIds, id]);
    }
  };

  if (!subjectId) {
    return (
      <div className="space-y-4 border rounded-xl p-5 bg-card shadow-sm opacity-50 pointer-events-none">
        <h3 className="font-semibold text-sm border-b pb-3">Select Reference Documents</h3>
        <p className="text-sm text-muted-foreground text-center py-4">Select a subject to see your relevant documents</p>
      </div>
    );
  }

  if (loading) return <div className="text-sm text-muted-foreground animate-pulse p-4 border rounded-xl shadow-sm">Loading documents...</div>;

  if (documents.length === 0) return (
    <div className="text-sm text-muted-foreground p-5 border rounded-xl bg-card shadow-sm space-y-2">
      <h3 className="font-semibold text-sm border-b pb-3 text-foreground">Select Reference Documents</h3>
      <p className="pt-2">You have no documents uploaded for this subject.</p>
      <p>Upload documents from the <Link href="/dashboard/documents" className="text-primary hover:underline font-medium">Documents</Link> page to use them here.</p>
      <p className="text-xs text-muted-foreground pt-2">The AI will use standard Admin sources for now.</p>
    </div>
  );

  return (
    <div className="space-y-4 border rounded-xl p-5 bg-card shadow-sm">
      <div className="flex justify-between items-center border-b pb-3">
        <h3 className="font-semibold text-sm">Select Reference Documents</h3>
        <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded-full">{selectedIds.length} selected</span>
      </div>

      <div className="max-h-60 overflow-y-auto space-y-2 pr-2 custom-scrollbar">
        {documents.map((doc: any) => {
          const isSelected = selectedIds.includes(doc.id);
          return (
            <label 
              key={doc.id} 
              className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${isSelected ? 'bg-primary/5 border-primary/30' : 'hover:bg-muted/50 border-transparent hover:border-border'}`}
            >
              <input 
                type="checkbox" 
                className="mt-1 h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                checked={isSelected}
                onChange={() => toggleSelection(doc.id)}
              />
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate">{doc.filename}</div>
                <div className="text-xs text-muted-foreground mt-0.5 flex gap-2">
                  <span className="uppercase">{doc.subject_id ? "Subject Docs" : "Unknown"}</span>
                  <span>•</span>
                  <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            </label>
          );
        })}
      </div>

      <div className="pt-3 border-t">
        <label className={`flex items-center gap-2 text-sm ${selectedIds.length === 0 ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}>
          <input 
            type="checkbox" 
            className="h-4 w-4 rounded border-gray-300 text-primary"
            checked={fromThisOnly}
            onChange={(e) => onFromThisOnlyChange(e.target.checked)}
            disabled={selectedIds.length === 0}
          />
          <span className="font-medium">Restrict AI to selected documents only</span>
        </label>
        <p className="text-xs text-muted-foreground ml-6 mt-1 leading-relaxed">
          If checked, the Question Generator will ignore global admin documents and purely use your selected uploads to construct questions. This guarantees 100% curriculum alignment to your specific files.
        </p>
      </div>
    </div>
  );
}
