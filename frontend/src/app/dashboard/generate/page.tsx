'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useQuestionGeneration } from '@/lib/hooks/useQuestionGeneration';
import { DocumentSelector } from '@/components/DocumentSelector';
import { TopicSelector } from '@/components/TopicSelector';

import { api } from '@/lib/api';

export default function GeneratePaperPage() {
  const { data: subjects = [], isLoading: loadingSubjects } = useQuery({
    queryKey: ['subjects'],
    queryFn: async () => {
      const res = await api.get('/subjects');
      return res.data;
    }
  });

  const { data: examTypes = [], isLoading: loadingExamTypes } = useQuery({
    queryKey: ['examTypes'],
    queryFn: async () => {
      const res = await api.get('/exam-types');
      return res.data;
    }
  });

  const [subjectId, setSubjectId] = useState('');
  const [academicLevel, setAcademicLevel] = useState('');
  const [examTypeId, setExamTypeId] = useState('');
  
  const [selectedDocs, setSelectedDocs] = useState<string[]>([]);
  const [fromThisOnly, setFromThisOnly] = useState(false);
  
  const [selectedTopics, setSelectedTopics] = useState<string[]>([]);
  const [selectedSubtopics, setSelectedSubtopics] = useState<string[]>([]);

  const [mcqCounts, setMcqCounts] = useState({ easy: 3, medium: 4, hard: 3 });
  const [theoryCounts, setTheoryCounts] = useState({ easy: 1, medium: 2, hard: 2 });
  
  const { generate, loading } = useQuestionGeneration();

  // Load academic levels when subject changes
  const { data: academicLevels = [], isFetching: loadingLevels } = useQuery({
    queryKey: ['academic-levels', subjectId],
    queryFn: async () => {
      const res = await api.get(`/subjects/${subjectId}/academic-levels`);
      return res.data;
    },
    enabled: !!subjectId,
  });

  const handleSubjectChange = (newSubjectId: string) => {
    setSubjectId(newSubjectId);
    // Reset dependent states
    setAcademicLevel('');
    setSelectedDocs([]);
    setFromThisOnly(false);
    setSelectedTopics([]);
    setSelectedSubtopics([]);
  };



  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const payload = {
      subject_id: subjectId,
      exam_type_id: examTypeId,
      academic_level: academicLevel || 'Any / General',
      selected_document_ids: selectedDocs,
      from_this_only: fromThisOnly,
      mcq_easy: mcqCounts.easy,
      mcq_medium: mcqCounts.medium,
      mcq_hard: mcqCounts.hard,
      theory_easy: theoryCounts.easy,
      theory_medium: theoryCounts.medium,
      theory_hard: theoryCounts.hard,
      selected_topics: selectedTopics,
      selected_subtopics: selectedSubtopics,
      topics: [] // keep for backward compatibility
    };

    await generate(payload);
  };

  return (
    <div className="max-w-4xl mx-auto p-6 bg-background rounded-xl shadow-sm border mb-10">
      <h1 className="text-2xl font-bold mb-6">Generate Question Paper</h1>
      
      <form onSubmit={handleGenerate} className="space-y-8">
        
        {/* A. Subject Selector */}
        <div className="space-y-2 p-5 bg-card border rounded-xl shadow-sm">
          <label className="text-sm font-semibold">1. Select Subject <span className="text-destructive">*</span></label>
          <select required value={subjectId} onChange={e => handleSubjectChange(e.target.value)} disabled={loadingSubjects}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
          >
            <option value="">{loadingSubjects ? 'Loading subjects...' : '-- Choose a subject --'}</option>
            {subjects.map((s: any) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
        </div>

        {/* B. Academic Level Selector */}
        {subjectId && (
          <div className="space-y-2 p-5 bg-card border rounded-xl shadow-sm animate-in fade-in slide-in-from-top-4 duration-300">
            <label className="text-sm font-semibold">2. Academic Level</label>
            <select 
              value={academicLevel} 
              onChange={e => setAcademicLevel(e.target.value)}
              disabled={loadingLevels}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
            >
              <option value="">{loadingLevels ? 'Loading levels...' : 'Any / General'}</option>
              {academicLevels.map((lvl: string) => (
                <option key={lvl} value={lvl}>{lvl}</option>
              ))}
            </select>
          </div>
        )}

        {/* C & D. Topic and Document Selectors (Gate behind Subject) */}
        {subjectId && (
          <div className="grid md:grid-cols-2 gap-6 animate-in fade-in slide-in-from-top-4 duration-500">
            {/* C. Topic Selector */}
            <TopicSelector 
              subjectId={subjectId}
              selectedTopics={selectedTopics}
              selectedSubtopics={selectedSubtopics}
              onChange={(topics, subtopics) => {
                setSelectedTopics(topics);
                setSelectedSubtopics(subtopics);
              }}
            />

            {/* D. Document Selector */}
            <DocumentSelector 
              subjectId={subjectId}
              selectedIds={selectedDocs}
              onChange={setSelectedDocs}
              fromThisOnly={fromThisOnly}
              onFromThisOnlyChange={setFromThisOnly}
            />
          </div>
        )}

        {/* E, F, G, H. Generation Settings */}
        {subjectId && (
          <div className="space-y-6 p-5 bg-card border rounded-xl shadow-sm animate-in fade-in slide-in-from-top-4 duration-700">
            <h3 className="font-semibold border-b pb-3 text-lg">Paper Configuration</h3>
            
            {/* E. Exam Type */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Exam Type <span className="text-destructive">*</span></label>
              <select required value={examTypeId} onChange={e => setExamTypeId(e.target.value)} disabled={loadingExamTypes}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary"
              >
                <option value="">{loadingExamTypes ? 'Loading exam types...' : 'Select Exam Type format...'}</option>
                {examTypes.map((e: any) => (
                  <option key={e.id} value={e.id}>{e.name}</option>
                ))}
              </select>
            </div>

            {/* F & G. Question Counts */}
            <div className="pt-4 space-y-4">
              <label className="text-sm font-medium border-b pb-2 flex items-center justify-between">
                <span>Detailed Question Counts</span>
                <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded-md">
                  Total: {mcqCounts.easy + mcqCounts.medium + mcqCounts.hard + theoryCounts.easy + theoryCounts.medium + theoryCounts.hard}
                </span>
              </label>
              
              <div className="grid md:grid-cols-2 gap-8">
                {/* MCQ Column */}
                <div className="space-y-4 bg-muted/20 p-4 rounded-xl border">
                  <h4 className="text-sm font-semibold text-primary/80">Multiple Choice (MCQ)</h4>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="space-y-1.5">
                      <label className="text-xs font-medium text-green-600 dark:text-green-500">Easy</label>
                      <input type="number" min="0" max="50" required value={mcqCounts.easy} onChange={e => setMcqCounts({...mcqCounts, easy: parseInt(e.target.value) || 0})}
                        className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm focus:ring-2 focus:ring-green-500/20" />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-xs font-medium text-amber-500 dark:text-amber-400">Medium</label>
                      <input type="number" min="0" max="50" required value={mcqCounts.medium} onChange={e => setMcqCounts({...mcqCounts, medium: parseInt(e.target.value) || 0})}
                        className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm focus:ring-2 focus:ring-amber-500/20" />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-xs font-medium text-red-500 dark:text-red-400">Hard</label>
                      <input type="number" min="0" max="50" required value={mcqCounts.hard} onChange={e => setMcqCounts({...mcqCounts, hard: parseInt(e.target.value) || 0})}
                        className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm focus:ring-2 focus:ring-red-500/20" />
                    </div>
                  </div>
                </div>

                {/* Theory Column */}
                <div className="space-y-4 bg-muted/20 p-4 rounded-xl border">
                  <h4 className="text-sm font-semibold text-primary/80">Theory / Descriptive</h4>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="space-y-1.5">
                      <label className="text-xs font-medium text-green-600 dark:text-green-500">Easy</label>
                      <input type="number" min="0" max="50" required value={theoryCounts.easy} onChange={e => setTheoryCounts({...theoryCounts, easy: parseInt(e.target.value) || 0})}
                        className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm focus:ring-2 focus:ring-green-500/20" />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-xs font-medium text-amber-500 dark:text-amber-400">Medium</label>
                      <input type="number" min="0" max="50" required value={theoryCounts.medium} onChange={e => setTheoryCounts({...theoryCounts, medium: parseInt(e.target.value) || 0})}
                        className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm focus:ring-2 focus:ring-amber-500/20" />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-xs font-medium text-red-500 dark:text-red-400">Hard</label>
                      <input type="number" min="0" max="50" required value={theoryCounts.hard} onChange={e => setTheoryCounts({...theoryCounts, hard: parseInt(e.target.value) || 0})}
                        className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm focus:ring-2 focus:ring-red-500/20" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
          </div>
        )}

        <button type="submit" disabled={loading || !subjectId}
          className="w-full inline-flex justify-center items-center rounded-xl shadow-sm text-sm font-medium transition-colors h-12 px-8 bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Generating Paper... This may take a minute.
            </span>
          ) : (
            <span className="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2v4"/><path d="M12 18v4"/><path d="M4.93 4.93l2.83 2.83"/><path d="M16.24 16.24l2.83 2.83"/><path d="M2 12h4"/><path d="M18 12h4"/><path d="M4.93 19.07l2.83-2.83"/><path d="M16.24 7.76l2.83-2.83"/></svg>
              Generate AI Question Paper
            </span>
          )}
        </button>

      </form>
    </div>
  );
}
