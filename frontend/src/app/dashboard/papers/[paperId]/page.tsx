'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { PaperExport } from '@/components/PaperExport';
import { ExportDialog } from '@/components/ExportDialog';

export default function PaperViewerPage() {
  const params = useParams();
  const paperId = params.paperId as string;
  const [paper, setPaper] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPaper = async () => {
      try {
        const res = await fetch(`http://localhost:8000/questions/papers/${paperId}`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        const data = await res.json();
        setPaper(data);
      } catch (err) {
        console.error("Failed to load paper", err);
      } finally {
        setLoading(false);
      }
    };
    if (paperId) fetchPaper();
  }, [paperId]);

  const handlePrint = () => {
    window.print();
  };

  const handleSwap = (questionId: string) => {
    // Optimistic UI update logic: find a mock recommended question and swap instantly
    setPaper((prev: any) => {
      const newQuestions = prev.questions.map((q: any) => {
        if (q.id === questionId) {
          return {
            ...q,
            id: 'swapped_' + Date.now(),
            text: '[SWAPPED] ' + q.text,
            is_swapped: true
          };
        }
        return q;
      });
      return { ...prev, questions: newQuestions };
    });
    
    // Background fetch to actually log the swap or fetch real data would go here
  };

  const [isExportOpen, setIsExportOpen] = useState(false);

  if (loading) {
    return <div className="p-8 text-center animate-pulse">Loading Question Paper...</div>;
  }

  if (!paper) {
    return <div className="p-8 text-center text-red-500">Failed to load question paper.</div>;
  }

  // Group questions by type for neat rendering
  const mcqQuestions = paper.questions.filter((q: any) => q.type === 'mcq');
  const theoryQuestions = paper.questions.filter((q: any) => q.type === 'theory');

  return (
    <div className="max-w-5xl mx-auto p-4 md:p-8">
      <div className="flex justify-end mb-4 no-print">
        <button 
          onClick={() => setIsExportOpen(true)}
          className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow hover:bg-primary/90 h-9 px-4 py-2"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-download mr-2 h-4 w-4"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/></svg>
          Export Paper
        </button>
      </div>
      <PaperExport paper={paper} />
      
      <ExportDialog 
        paperId={paperId} 
        paperTitle={paper.title || "Question_Paper"} 
        isOpen={isExportOpen} 
        onClose={() => setIsExportOpen(false)} 
      />
    </div>
  );
}
