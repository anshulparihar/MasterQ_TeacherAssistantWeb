'use client';

import { useState } from 'react';
import { QuestionCard } from './QuestionCard';

interface PaperExportProps {
  paper: any; // Contains title, paper_id, questions array
}

export function PaperExport({ paper }: PaperExportProps) {
  const [showAnswers, setShowAnswers] = useState(true);

  const handlePrint = () => {
    window.print();
  };

  const mcqQuestions = paper.questions.filter((q: any) => q.type === 'mcq');
  const theoryQuestions = paper.questions.filter((q: any) => q.type === 'theory');

  return (
    <div className="bg-background">
      {/* UI Controls (Hidden on Print) */}
      <div className="print:hidden flex flex-col md:flex-row justify-between items-center mb-8 pb-4 border-b gap-4">
        <div>
          <h1 className="text-3xl font-bold">{paper.title}</h1>
          <p className="text-sm text-muted-foreground mt-2">ID: {paper.paper_id}</p>
        </div>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 cursor-pointer text-sm font-medium border px-4 py-2 rounded-md hover:bg-muted transition-colors">
            <input 
              type="checkbox" 
              className="h-4 w-4 rounded border-gray-300 text-primary"
              checked={showAnswers}
              onChange={(e) => setShowAnswers(e.target.checked)}
            />
            Include Model Answers & Hints
          </label>
          <button 
            onClick={handlePrint}
            className="bg-primary text-primary-foreground px-6 py-2 rounded-md font-medium hover:bg-primary/90 flex items-center gap-2"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M6 9V2h12v7"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><path d="M6 14h12v8H6z"/></svg>
            Export PDF
          </button>
        </div>
      </div>

      {/* Printable Area */}
      <div className={`print:block space-y-12 ${!showAnswers ? 'hide-answers' : ''}`}>
        
        {/* Paper Header for Print */}
        <div className="hidden print:block border-b-2 border-black pb-4 mb-8 text-center">
          <h1 className="text-2xl font-bold uppercase tracking-wider">{paper.title}</h1>
          <div className="flex justify-between items-center mt-4 text-sm font-medium">
            <span>Subject: {paper.subject_id?.split('-')[0] || 'Standard'}</span>
            <span>Date: {new Date(paper.created_at).toLocaleDateString()}</span>
            <span>Total Marks: {paper.total_marks || 100}</span>
          </div>
        </div>

        {mcqQuestions.length > 0 && (
          <section>
            <h2 className="text-xl font-bold mb-6 uppercase tracking-wider text-primary print:text-black border-l-4 border-primary print:border-black pl-3">
              Section A: Multiple Choice Questions
            </h2>
            <div className="space-y-6">
              {mcqQuestions.map((q: any, i: number) => (
                <div key={q.id} className="relative">
                  <span className="absolute -left-8 top-6 font-bold text-lg print:text-black">{i + 1}.</span>
                  <QuestionCard question={q} />
                </div>
              ))}
            </div>
          </section>
        )}

        {theoryQuestions.length > 0 && (
          <section>
            <h2 className="text-xl font-bold mb-6 uppercase tracking-wider text-primary print:text-black border-l-4 border-primary print:border-black pl-3 mt-12 print:mt-16">
              Section B: Theory & Subjective
            </h2>
            <div className="space-y-6">
              {theoryQuestions.map((q: any, i: number) => (
                <div key={q.id} className="relative break-inside-avoid">
                  <span className="absolute -left-8 top-6 font-bold text-lg print:text-black">{mcqQuestions.length + i + 1}.</span>
                  <QuestionCard question={q} />
                  
                  {/* Print Answer Lines Space if answers are hidden */}
                  {!showAnswers && (
                    <div className="hidden print:block mt-6 space-y-8">
                      <div className="border-b border-gray-300 w-full"></div>
                      <div className="border-b border-gray-300 w-full"></div>
                      <div className="border-b border-gray-300 w-full"></div>
                      <div className="border-b border-gray-300 w-full"></div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

      </div>

      {/* Advanced Print CSS */}
      <style jsx global>{`
        @media print {
          @page { margin: 20mm; }
          body {
            background: white;
            color: black;
            font-size: 12pt;
          }
          .bg-card {
            background: white !important;
            border: none !important;
            box-shadow: none !important;
            border-bottom: 1px solid #e5e7eb !important;
            border-radius: 0 !important;
            padding-left: 0 !important;
            padding-right: 0 !important;
          }
          .bg-primary\\/10 {
            background: transparent !important;
            border: 1px solid black !important;
            color: black !important;
          }
          .border-l-4 {
            border-left: 3px solid black !important;
          }
          .hide-answers details,
          .hide-answers .text-green-600,
          .hide-answers .bg-green-50,
          .hide-answers .bg-green-200 {
            display: none !important;
            background: transparent !important;
            border-color: #e5e7eb !important;
            color: black !important;
          }
        }
      `}</style>
    </div>
  );
}
