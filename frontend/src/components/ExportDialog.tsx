'use client';

import { useState } from 'react';
import { Download, Loader2, X } from 'lucide-react';

interface ExportDialogProps {
  paperId: string;
  paperTitle: string;
  isOpen: boolean;
  onClose: () => void;
}

export function ExportDialog({ paperId, paperTitle, isOpen, onClose }: ExportDialogProps) {
  const [format, setFormat] = useState<'pdf' | 'docx'>('pdf');
  const [includeAnswers, setIncludeAnswers] = useState(false);
  const [includeExplanations, setIncludeExplanations] = useState(false);
  const [includeHints, setIncludeHints] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  // If Answers is unchecked, uncheck Explanations and Hints automatically
  const handleIncludeAnswersChange = (checked: boolean) => {
    setIncludeAnswers(checked);
    if (!checked) {
      setIncludeExplanations(false);
      setIncludeHints(false);
    }
  };

  const handleExport = async () => {
    setIsExporting(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      if (!token) throw new Error('Not authenticated');

      const params = new URLSearchParams({
        format,
        include_answers: includeAnswers.toString(),
        include_explanations: includeExplanations.toString(),
        include_hints: includeHints.toString(),
      });

      const response = await fetch(`/api/questions/papers/${paperId}/export?${params.toString()}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Export failed. Please try again.');
      }

      const blob = await response.blob();
      
      const contentDisposition = response.headers.get('Content-Disposition');
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
      
      onClose();
    } catch (err: any) {
      setError(err.message || 'An error occurred during export.');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-lg w-full max-w-md overflow-hidden relative">
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-lg font-semibold text-slate-900">Export Question Paper</h2>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-700 transition-colors">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {error && <div className="text-red-500 text-sm font-medium bg-red-50 p-3 rounded-md">{error}</div>}
          
          <div className="space-y-3">
            <h4 className="font-medium text-sm text-slate-700">Format</h4>
            <div className="flex flex-col space-y-2">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input 
                  type="radio" 
                  name="format" 
                  value="pdf" 
                  checked={format === 'pdf'} 
                  onChange={() => setFormat('pdf')}
                  className="w-4 h-4 text-blue-600 border-slate-300 focus:ring-blue-500"
                />
                <span className="text-sm font-medium text-slate-700">PDF Document (.pdf)</span>
              </label>
              <label className="flex items-center space-x-2 cursor-pointer">
                <input 
                  type="radio" 
                  name="format" 
                  value="docx" 
                  checked={format === 'docx'} 
                  onChange={() => setFormat('docx')}
                  className="w-4 h-4 text-blue-600 border-slate-300 focus:ring-blue-500"
                />
                <span className="text-sm font-medium text-slate-700">Word Document (.docx)</span>
              </label>
            </div>
          </div>

          <div className="space-y-3">
            <h4 className="font-medium text-sm text-slate-700">Include in export</h4>
            <div className="space-y-3">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input 
                  type="checkbox" 
                  checked={includeAnswers}
                  onChange={(e) => handleIncludeAnswersChange(e.target.checked)}
                  className="w-4 h-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500"
                />
                <span className="text-sm font-medium text-slate-700">Answers (Teacher's Copy)</span>
              </label>
              
              <label className={`flex items-center space-x-2 ml-6 ${!includeAnswers ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}`}>
                <input 
                  type="checkbox" 
                  checked={includeExplanations}
                  onChange={(e) => setIncludeExplanations(e.target.checked)}
                  disabled={!includeAnswers}
                  className="w-4 h-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500 disabled:bg-slate-100"
                />
                <span className="text-sm font-medium text-slate-700">Explanations</span>
              </label>

              <label className={`flex items-center space-x-2 ml-6 ${!includeAnswers ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}`}>
                <input 
                  type="checkbox" 
                  checked={includeHints}
                  onChange={(e) => setIncludeHints(e.target.checked)}
                  disabled={!includeAnswers}
                  className="w-4 h-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500 disabled:bg-slate-100"
                />
                <span className="text-sm font-medium text-slate-700">Hints</span>
              </label>
            </div>
          </div>
        </div>

        <div className="flex justify-end space-x-2 p-6 border-t bg-slate-50">
          <button 
            onClick={onClose} 
            disabled={isExporting}
            className="px-4 py-2 border border-slate-300 rounded-md text-sm font-medium text-slate-700 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            Cancel
          </button>
          <button 
            onClick={handleExport} 
            disabled={isExporting}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {isExporting ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Download className="mr-2 h-4 w-4" />
            )}
            Export
          </button>
        </div>
      </div>
    </div>
  );
}
