'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { ExportDialog } from '@/components/ExportDialog';
import { QuestionCard } from '@/components/QuestionCard';
import { BackButton } from '@/components/ui/BackButton';
import { Button } from '@/components/ui/button';
import { Download, Loader2 } from 'lucide-react';
import { api } from '@/lib/api';
import toast from 'react-hot-toast';

export default function PaperViewerPage() {
  const params = useParams();
  const paperId = params.paperId as string;
  const [paper, setPaper] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [isExportOpen, setIsExportOpen] = useState(false);

  useEffect(() => {
    const fetchPaper = async () => {
      try {
        setLoading(true);
        const res = await api.get(`/questions/papers/${paperId}`);
        setPaper(res.data);
      } catch (err) {
        console.error("Failed to load paper", err);
        toast.error("Failed to load paper");
      } finally {
        setLoading(false);
      }
    };
    if (paperId) fetchPaper();
  }, [paperId]);

  const handleSwap = (oldQuestionId: string, newQuestion: any) => {
    setPaper((prev: any) => {
      const newQuestions = prev.questions.map((q: any) => {
        if (q.id === oldQuestionId) {
          return newQuestion;
        }
        return q;
      });
      return { ...prev, questions: newQuestions };
    });
    toast.success('Question swapped successfully');
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-[50vh]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!paper) {
    return (
      <div className="p-8 text-center text-red-500 bg-red-50 rounded-2xl border border-red-100 font-medium">
        Failed to load question paper.
      </div>
    );
  }

  // Group questions by type
  const mcqQuestions = paper.questions.filter((q: any) => q.type === 'mcq');
  const theoryQuestions = paper.questions.filter((q: any) => q.type === 'theory');

  return (
    <div className="max-w-4xl mx-auto pb-24 animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div className="flex items-center justify-between mb-8 pb-6 border-b border-slate-200">
        <div className="flex items-center gap-4">
          <BackButton />
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-slate-900">Paper Review</h1>
            <p className="text-sm text-slate-500 mt-1">
              Review, swap questions with AI alternatives, and export your paper.
            </p>
          </div>
        </div>
        <Button 
          onClick={() => setIsExportOpen(true)}
          className="bg-primary hover:bg-primary/90 shadow-sm rounded-xl px-5 h-11"
        >
          <Download className="h-4 w-4 mr-2" />
          Export Paper
        </Button>
      </div>

      <div className="space-y-12">
        <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200 text-center">
          <h2 className="text-2xl font-bold uppercase tracking-wider text-slate-900 mb-2">{paper.title}</h2>
          <div className="flex justify-center items-center gap-6 text-sm font-medium text-slate-600">
            <span>Subject: {paper.subject?.name || 'Standard'}</span>
            <span>Date: {new Date(paper.created_at).toLocaleDateString()}</span>
            <span>Questions: {paper.questions.length}</span>
          </div>
        </div>

        {mcqQuestions.length > 0 && (
          <section>
            <h3 className="text-xl font-bold mb-6 text-slate-900 flex items-center gap-2">
              <span className="bg-primary/10 text-primary w-8 h-8 rounded-lg flex items-center justify-center text-sm">A</span>
              Multiple Choice Questions
            </h3>
            <div className="space-y-6">
              {mcqQuestions.map((q: any, i: number) => (
                <QuestionCard 
                  key={q.id} 
                  question={q} 
                  index={i}
                  onSwap={(newQ) => handleSwap(q.id, newQ)}
                />
              ))}
            </div>
          </section>
        )}

        {theoryQuestions.length > 0 && (
          <section>
            <h3 className="text-xl font-bold mb-6 text-slate-900 flex items-center gap-2">
              <span className="bg-primary/10 text-primary w-8 h-8 rounded-lg flex items-center justify-center text-sm">B</span>
              Theory & Subjective
            </h3>
            <div className="space-y-6">
              {theoryQuestions.map((q: any, i: number) => (
                <QuestionCard 
                  key={q.id} 
                  question={q} 
                  index={mcqQuestions.length + i}
                  onSwap={(newQ) => handleSwap(q.id, newQ)}
                />
              ))}
            </div>
          </section>
        )}
      </div>
      
      <ExportDialog 
        paperId={paperId} 
        paperTitle={paper.title || "Question_Paper"} 
        isOpen={isExportOpen} 
        onClose={() => setIsExportOpen(false)} 
      />
    </div>
  );
}
