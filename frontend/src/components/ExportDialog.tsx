'use client';

import { useState } from 'react';
import { Download, Loader2, X, FileText } from 'lucide-react';
import { api } from '@/lib/api';
import toast from 'react-hot-toast';

interface ExportDialogProps {
  paperId: string;
  paperTitle: string;
  isOpen: boolean;
  onClose: () => void;
}

export function ExportDialog({ paperId, paperTitle, isOpen, onClose }: ExportDialogProps) {
  const [format, setFormat] = useState<'pdf' | 'docx'>('pdf');
  const [includeMarkingScheme, setIncludeMarkingScheme] = useState(false);
  const [includeSolutionKey, setIncludeSolutionKey] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  if (!isOpen) return null;

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const params = new URLSearchParams({
        format,
        include_marking_scheme: includeMarkingScheme.toString(),
        include_solution_key: includeSolutionKey.toString(),
      });

      const response = await api.get(`/questions/papers/${paperId}/export?${params.toString()}`, {
        responseType: 'blob'
      });

      const blob = response.data;
      const contentDisposition = response.headers['content-disposition'];
      let filename = `${paperTitle.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_export.${format}`;
      
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
        if (filenameMatch && filenameMatch.length > 1) {
          filename = filenameMatch[1];
        }
      }

      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(link.href);
      
      toast.success('Paper exported successfully');
      onClose();
    } catch (err: any) {
      console.error(err);
      toast.error('Failed to export paper. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden relative animate-in zoom-in-95 duration-200">
        <div className="flex justify-between items-center p-6 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="bg-primary/10 p-2 rounded-xl text-primary">
              <FileText className="h-5 w-5" />
            </div>
            <h2 className="text-lg font-bold text-slate-900">Export Paper</h2>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 hover:bg-slate-100 p-2 rounded-full transition-colors">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6 space-y-8">
          
          <div className="space-y-4">
            <h4 className="font-semibold text-sm text-slate-900 uppercase tracking-wider">Document Format</h4>
            <div className="grid grid-cols-2 gap-3">
              <label className={`flex flex-col items-center justify-center p-4 rounded-xl border-2 cursor-pointer transition-all ${format === 'pdf' ? 'border-primary bg-primary/5' : 'border-slate-200 hover:border-slate-300'}`}>
                <input 
                  type="radio" 
                  name="format" 
                  value="pdf" 
                  checked={format === 'pdf'} 
                  onChange={() => setFormat('pdf')}
                  className="sr-only"
                />
                <span className={`text-sm font-bold ${format === 'pdf' ? 'text-primary' : 'text-slate-600'}`}>PDF Document</span>
                <span className="text-xs text-slate-400 mt-1">.pdf format</span>
              </label>
              <label className={`flex flex-col items-center justify-center p-4 rounded-xl border-2 cursor-pointer transition-all ${format === 'docx' ? 'border-primary bg-primary/5' : 'border-slate-200 hover:border-slate-300'}`}>
                <input 
                  type="radio" 
                  name="format" 
                  value="docx" 
                  checked={format === 'docx'} 
                  onChange={() => setFormat('docx')}
                  className="sr-only"
                />
                <span className={`text-sm font-bold ${format === 'docx' ? 'text-primary' : 'text-slate-600'}`}>Word Document</span>
                <span className="text-xs text-slate-400 mt-1">.docx format</span>
              </label>
            </div>
          </div>

          <div className="space-y-4">
            <h4 className="font-semibold text-sm text-slate-900 uppercase tracking-wider">Include Additional Content</h4>
            <div className="space-y-3">
              <label className="flex items-center space-x-3 cursor-pointer p-3 rounded-xl border border-slate-200 hover:bg-slate-50 transition-colors">
                <input 
                  type="checkbox" 
                  checked={includeMarkingScheme}
                  onChange={(e) => setIncludeMarkingScheme(e.target.checked)}
                  className="w-5 h-5 text-primary rounded border-slate-300 focus:ring-primary focus:ring-offset-0 transition-all"
                />
                <span className="text-sm font-medium text-slate-700">Include Marking Scheme</span>
              </label>
              
              <label className="flex items-center space-x-3 cursor-pointer p-3 rounded-xl border border-slate-200 hover:bg-slate-50 transition-colors">
                <input 
                  type="checkbox" 
                  checked={includeSolutionKey}
                  onChange={(e) => setIncludeSolutionKey(e.target.checked)}
                  className="w-5 h-5 text-primary rounded border-slate-300 focus:ring-primary focus:ring-offset-0 transition-all"
                />
                <span className="text-sm font-medium text-slate-700">Include Solution Key</span>
              </label>
            </div>
          </div>
        </div>

        <div className="flex justify-end space-x-3 p-6 border-t border-slate-100 bg-slate-50/50">
          <button 
            onClick={onClose} 
            disabled={isExporting}
            className="px-5 py-2.5 rounded-xl text-sm font-semibold text-slate-600 hover:bg-slate-200 hover:text-slate-900 transition-colors focus:outline-none disabled:opacity-50"
          >
            Cancel
          </button>
          <button 
            onClick={handleExport} 
            disabled={isExporting}
            className="inline-flex items-center px-6 py-2.5 rounded-xl text-sm font-bold text-white bg-primary hover:bg-primary/90 shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary transition-all disabled:opacity-50"
          >
            {isExporting ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Download className="mr-2 h-4 w-4" />
            )}
            {isExporting ? 'Exporting...' : 'Export File'}
          </button>
        </div>
      </div>
    </div>
  );
}
