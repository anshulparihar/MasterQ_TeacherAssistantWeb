import React, { useState } from 'react';
import Latex from 'react-latex-next';

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
  isRecommendation?: boolean;
  onSwap?: () => void;
}

export const QuestionCard = React.memo(function QuestionCard({ question, isRecommendation, onSwap }: QuestionCardProps) {
  const getDifficultyColor = (diff: string) => {
    switch (diff.toLowerCase()) {
      case 'easy': return 'bg-green-100 text-green-800 border-green-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'hard': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <div className={`border rounded-xl p-6 shadow-sm mb-4 relative group transition-colors ${isRecommendation ? 'bg-primary/5 border-primary/20' : 'bg-card'}`}>
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold uppercase tracking-wider bg-primary/10 text-primary px-2 py-1 rounded">
            {question.type}
          </span>
          {isRecommendation && (
            <span className="text-xs font-bold uppercase tracking-wider bg-blue-100 text-blue-800 px-2 py-1 rounded flex items-center gap-1">
              ⭐ Recommended
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {onSwap && (
            <button 
              onClick={onSwap}
              className="opacity-0 group-hover:opacity-100 transition-opacity text-xs bg-muted hover:bg-primary hover:text-primary-foreground px-3 py-1.5 rounded-md font-medium print:hidden shadow-sm flex items-center gap-1"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 2v6h-6"/><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 2v6h6"/></svg>
              Swap
            </button>
          )}
          <span className={`text-xs font-bold uppercase tracking-wider px-2 py-1 rounded border ${getDifficultyColor(question.difficulty)}`}>
            {question.difficulty}
          </span>
        </div>
      </div>
      
      <div className="text-lg font-medium mb-6 whitespace-pre-wrap leading-relaxed"><Latex>{question.text}</Latex></div>
      
      {question.diagram_url && (
        <div className="my-6 flex flex-col items-center">
          <img 
            src={question.diagram_url} 
            alt="Question Diagram" 
            className="max-w-[400px] w-full border border-border rounded-md shadow-sm"
          />
        </div>
      )}
      
      {question.type === 'mcq' && question.options && (
        <div className="space-y-3 mt-4">
          {question.options.map((option, idx) => (
            <div 
              key={idx} 
              className="p-3 border rounded-lg transition-colors flex items-center print:border-gray-300 bg-muted/30 hover:bg-muted"
            >
              <span className="font-bold mr-3 w-6 h-6 flex items-center justify-center rounded-full text-xs bg-muted text-muted-foreground">
                {String.fromCharCode(65 + idx)}
              </span>
              <span><Latex>{option}</Latex></span>
            </div>
          ))}
        </div>
      )}

      {/* Answer Collapsible Data */}
      <div className="mt-6 space-y-2 print:hidden">
        {question.type === 'theory' && question.model_answer && (
          <details className="group border rounded-lg overflow-hidden [&_summary::-webkit-details-marker]:hidden">
            <summary className="flex items-center justify-between p-3 bg-muted/50 cursor-pointer font-medium text-sm hover:bg-muted transition-colors">
              View Model Answer
              <span className="transition group-open:rotate-180">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m6 9 6 6 6-6"/></svg>
              </span>
            </summary>
            <div className="p-4 bg-background text-sm border-t leading-relaxed whitespace-pre-wrap">
              <Latex>{question.model_answer}</Latex>
            </div>
          </details>
        )}

        {question.type === 'mcq' && question.correct_answer && (
          <details className="group border rounded-lg overflow-hidden [&_summary::-webkit-details-marker]:hidden">
            <summary className="flex items-center justify-between p-3 bg-green-50/50 cursor-pointer font-medium text-sm hover:bg-green-50 transition-colors text-green-900 border-b border-transparent group-open:border-green-100">
              View Answer
              <span className="transition group-open:rotate-180">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m6 9 6 6 6-6"/></svg>
              </span>
            </summary>
            <div className="p-4 bg-background text-sm border-t border-green-100 leading-relaxed whitespace-pre-wrap font-medium text-green-900">
              Correct Answer: <Latex>{question.correct_answer}</Latex>
            </div>
          </details>
        )}

        {question.explanation && (
          <details className="group border rounded-lg overflow-hidden [&_summary::-webkit-details-marker]:hidden">
            <summary className="flex items-center justify-between p-3 bg-muted/50 cursor-pointer font-medium text-sm hover:bg-muted transition-colors">
              View Explanation
              <span className="transition group-open:rotate-180">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m6 9 6 6 6-6"/></svg>
              </span>
            </summary>
            <div className="p-4 bg-background text-sm border-t leading-relaxed whitespace-pre-wrap text-muted-foreground">
              <Latex>{question.explanation}</Latex>
            </div>
          </details>
        )}

        {question.hint && (
          <details className="group border rounded-lg overflow-hidden border-yellow-200 [&_summary::-webkit-details-marker]:hidden">
            <summary className="flex items-center justify-between p-3 bg-yellow-50 cursor-pointer font-medium text-sm text-yellow-800 hover:bg-yellow-100 transition-colors">
              Show Hint
              <span className="transition group-open:rotate-180">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m6 9 6 6 6-6"/></svg>
              </span>
            </summary>
            <div className="p-4 bg-background text-sm border-t border-yellow-200 leading-relaxed text-yellow-900">
              💡 <Latex>{question.hint}</Latex>
            </div>
          </details>
        )}
      </div>

    </div>
  );
});
