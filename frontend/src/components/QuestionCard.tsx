import React, { useState, useEffect } from 'react';
import Latex from 'react-latex-next';
import { Sparkles, Loader2, ArrowLeftRight, CheckCircle2 } from 'lucide-react';

interface Question {
  id: string;
  text: string;
  type: string;
  options?: string[];
  correct_answer?: string;
  model_answer?: string;
  explanation?: string;
  hint?: string;
  difficulty: string;
  diagram_url?: string;
}

interface QuestionCardProps {
  question: Question;
  index?: number;
  isRecommendation?: boolean;
  onSwap?: (newQuestion: Question) => void;
}

export const QuestionCard = React.memo(function QuestionCard({ question, index, isRecommendation, onSwap }: QuestionCardProps) {
  const [showAI, setShowAI] = useState(false);
  const [isFetchingAI, setIsFetchingAI] = useState(false);
  const [alternatives, setAlternatives] = useState<Question[]>([]);

  const getDifficultyColor = (diff: string) => {
    switch (diff.toLowerCase()) {
      case 'easy': return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'medium': return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'hard': return 'bg-red-50 text-red-700 border-red-200';
      default: return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  useEffect(() => {
    if (showAI && alternatives.length === 0) {
      setIsFetchingAI(true);
      // Simulate API call to fetch AI alternatives
      const timer = setTimeout(() => {
        setAlternatives([
          {
            ...question,
            id: `alt-1-${Date.now()}`,
            text: `[Alternative 1] ${question.text}`,
          },
          {
            ...question,
            id: `alt-2-${Date.now()}`,
            text: `[Alternative 2] ${question.text}`,
            difficulty: question.difficulty === 'hard' ? 'medium' : 'hard'
          }
        ]);
        setIsFetchingAI(false);
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [showAI, question, alternatives.length]);

  return (
    <div className={`border rounded-2xl p-6 shadow-sm mb-6 transition-all duration-300 ${isRecommendation ? 'bg-indigo-50/50 border-primary/20' : 'bg-white border-slate-200'}`}>
      
      {/* Header */}
      <div className="flex justify-between items-center mb-5 pb-4 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <span className="font-bold text-slate-900 text-lg">
            {isRecommendation ? 'Alternative' : `Question ${index ? index + 1 : ''}`}
          </span>
          <span className="text-[10px] font-bold uppercase tracking-widest bg-slate-100 text-slate-600 px-2 py-1 rounded-md">
            {question.type}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className={`text-[11px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-md border ${getDifficultyColor(question.difficulty)}`}>
            {question.difficulty}
          </span>
        </div>
      </div>
      
      {/* Body */}
      <div className="text-base font-medium mb-6 text-slate-800 whitespace-pre-wrap leading-relaxed"><Latex>{question.text}</Latex></div>
      
      {question.diagram_url && (
        <div className="my-6 flex flex-col items-center">
          <img 
            src={question.diagram_url} 
            alt="Question Diagram" 
            className="max-w-[400px] w-full border border-slate-200 rounded-xl shadow-sm"
          />
        </div>
      )}
      
      {question.type === 'mcq' && question.options && (
        <div className="space-y-3 mt-4">
          {question.options.map((option, idx) => (
            <div 
              key={idx} 
              className="p-3 border border-slate-200 rounded-xl transition-colors flex items-center bg-slate-50/50"
            >
              <span className="font-bold mr-3 w-7 h-7 flex items-center justify-center rounded-lg text-sm bg-white border border-slate-200 text-slate-600 shadow-sm shrink-0">
                {String.fromCharCode(65 + idx)}
              </span>
              <span className="text-slate-700 text-sm"><Latex>{option}</Latex></span>
            </div>
          ))}
        </div>
      )}

      {/* Answer Collapsible Data (Teacher View) */}
      <div className="mt-6 space-y-2 print:hidden">
        {question.type === 'theory' && question.model_answer && (
          <details className="group border border-slate-200 rounded-xl overflow-hidden [&_summary::-webkit-details-marker]:hidden">
            <summary className="flex items-center justify-between p-4 bg-slate-50 cursor-pointer font-semibold text-sm text-slate-700 hover:bg-slate-100 transition-colors">
              View Model Answer
              <span className="transition-transform duration-200 group-open:rotate-180 text-slate-400">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m6 9 6 6 6-6"/></svg>
              </span>
            </summary>
            <div className="p-4 bg-white text-sm border-t border-slate-100 leading-relaxed whitespace-pre-wrap text-slate-600">
              <Latex>{question.model_answer}</Latex>
            </div>
          </details>
        )}

        {question.type === 'mcq' && question.correct_answer && (
          <details className="group border border-emerald-200 rounded-xl overflow-hidden [&_summary::-webkit-details-marker]:hidden">
            <summary className="flex items-center justify-between p-4 bg-emerald-50/50 cursor-pointer font-semibold text-sm hover:bg-emerald-50 transition-colors text-emerald-800">
              View Correct Answer
              <span className="transition-transform duration-200 group-open:rotate-180 text-emerald-600">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m6 9 6 6 6-6"/></svg>
              </span>
            </summary>
            <div className="p-4 bg-white text-sm border-t border-emerald-100 leading-relaxed whitespace-pre-wrap font-medium text-emerald-900 flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              <Latex>{question.correct_answer}</Latex>
            </div>
          </details>
        )}
      </div>

      {/* AI Action Bar & Alternatives Panel */}
      {!isRecommendation && (
        <div className="mt-8 border-t border-slate-100 pt-4 print:hidden">
          <button 
            onClick={() => setShowAI(!showAI)}
            className={`inline-flex items-center justify-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-200 ${
              showAI 
                ? 'bg-primary/10 text-primary hover:bg-primary/20' 
                : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 hover:border-slate-300 shadow-sm'
            }`}
          >
            <Sparkles className={`h-4 w-4 ${showAI ? 'text-primary' : 'text-slate-400'}`} />
            {showAI ? 'Hide Alternatives' : 'AI Alternatives'}
          </button>

          {showAI && (
            <div className="mt-4 p-5 bg-slate-50 border border-slate-200 rounded-xl">
              {isFetchingAI ? (
                <div className="flex flex-col items-center justify-center py-8 text-slate-500 space-y-3">
                  <Loader2 className="h-6 w-6 animate-spin text-primary" />
                  <p className="text-sm font-medium animate-pulse">AI is analyzing syllabus and generating alternatives...</p>
                </div>
              ) : (
                <div className="space-y-4">
                  <h4 className="text-sm font-bold text-slate-900 mb-2">Recommended Alternatives</h4>
                  {alternatives.map((alt, i) => (
                    <div key={alt.id} className="relative">
                      <QuestionCard 
                        question={alt} 
                        isRecommendation 
                      />
                      <div className="absolute top-4 right-4 print:hidden">
                        <button 
                          onClick={() => onSwap && onSwap(alt)}
                          className="inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all duration-200 bg-white border border-slate-200 text-slate-700 hover:bg-primary hover:text-white hover:border-primary shadow-sm"
                        >
                          <ArrowLeftRight className="h-3 w-3" />
                          Swap with this
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

    </div>
  );
});
