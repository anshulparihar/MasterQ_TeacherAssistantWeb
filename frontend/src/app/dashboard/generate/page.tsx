'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useQuestionGeneration } from '@/lib/hooks/useQuestionGeneration';
import { DocumentSelector } from '@/components/DocumentSelector';
import { TopicSelector } from '@/components/TopicSelector';
import { BackButton } from '@/components/ui/BackButton';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Sparkles, Loader2, BookOpen, Layers, FileSearch, Settings2 } from 'lucide-react';

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

  const totalQuestions = mcqCounts.easy + mcqCounts.medium + mcqCounts.hard + theoryCounts.easy + theoryCounts.medium + theoryCounts.hard;

  return (
    <div className="animate-in fade-in slide-in-from-top-4 duration-300 pb-24">
      <BackButton />
      
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Generate Paper</h1>
        <p className="text-sm text-slate-500 mt-1">
          Configure your paper requirements.
        </p>
      </div>

      <form onSubmit={handleGenerate} className="space-y-6 max-w-4xl">
        
        {/* Step 1 */}
        <Card className="p-6 border border-slate-200 shadow-sm rounded-2xl bg-white relative overflow-hidden">
          <div className="absolute top-0 left-0 w-1 h-full bg-primary/20" />
          <div className="flex items-center gap-3 mb-6">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-white font-bold text-sm">
              1
            </div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-slate-400" />
              Select Subject & Level
            </h2>
          </div>
          
          <div className="grid md:grid-cols-2 gap-6 pl-11">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-700">Subject <span className="text-red-500">*</span></label>
              <select required value={subjectId} onChange={e => handleSubjectChange(e.target.value)} disabled={loadingSubjects}
                className="flex h-11 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-slate-900"
              >
                <option value="">{loadingSubjects ? 'Loading subjects...' : '-- Choose a subject --'}</option>
                {subjects.map((s: any) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-700">Academic Level</label>
              <select 
                value={academicLevel} 
                onChange={e => setAcademicLevel(e.target.value)}
                disabled={loadingLevels || !subjectId}
                className="flex h-11 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-slate-900 disabled:opacity-50"
              >
                <option value="">{loadingLevels ? 'Loading levels...' : 'Any / General'}</option>
                {academicLevels.map((lvl: string) => (
                  <option key={lvl} value={lvl}>{lvl}</option>
                ))}
              </select>
            </div>
          </div>
        </Card>

        {/* Step 2 */}
        <Card className={`p-6 border border-slate-200 shadow-sm rounded-2xl bg-white relative overflow-hidden transition-all duration-500 ${!subjectId ? 'opacity-50 grayscale pointer-events-none' : ''}`}>
          <div className="absolute top-0 left-0 w-1 h-full bg-primary/20" />
          <div className="flex items-center gap-3 mb-6">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-white font-bold text-sm">
              2
            </div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Layers className="h-5 w-5 text-slate-400" />
              Select Topics & Subtopics
            </h2>
          </div>
          <div className="pl-11">
            <TopicSelector 
              subjectId={subjectId}
              selectedTopics={selectedTopics}
              selectedSubtopics={selectedSubtopics}
              onChange={(topics, subtopics) => {
                setSelectedTopics(topics);
                setSelectedSubtopics(subtopics);
              }}
            />
          </div>
        </Card>

        {/* Step 3 */}
        <Card className={`p-6 border border-slate-200 shadow-sm rounded-2xl bg-white relative overflow-hidden transition-all duration-500 ${!subjectId ? 'opacity-50 grayscale pointer-events-none' : ''}`}>
          <div className="absolute top-0 left-0 w-1 h-full bg-primary/20" />
          <div className="flex items-center gap-3 mb-6">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-white font-bold text-sm">
              3
            </div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <FileSearch className="h-5 w-5 text-slate-400" />
              Source Material
            </h2>
          </div>
          <div className="pl-11">
            <DocumentSelector 
              subjectId={subjectId}
              selectedIds={selectedDocs}
              onChange={setSelectedDocs}
              fromThisOnly={fromThisOnly}
              onFromThisOnlyChange={setFromThisOnly}
            />
            {/* Added extra toggle to ensure explicit strict text as requested */}
            <div className="mt-4 pt-4 border-t border-slate-100 flex items-center gap-3">
              <input 
                type="checkbox" 
                id="strict-toggle"
                checked={fromThisOnly}
                onChange={e => setFromThisOnly(e.target.checked)}
                className="w-4 h-4 rounded border-slate-300 text-primary focus:ring-primary"
              />
              <label htmlFor="strict-toggle" className="text-sm font-medium text-slate-700 cursor-pointer">
                Use strictly selected documents only (Do not use general AI knowledge)
              </label>
            </div>
          </div>
        </Card>

        {/* Step 4 */}
        <Card className={`p-6 border border-slate-200 shadow-sm rounded-2xl bg-white relative overflow-hidden transition-all duration-500 ${!subjectId ? 'opacity-50 grayscale pointer-events-none' : ''}`}>
          <div className="absolute top-0 left-0 w-1 h-full bg-primary/20" />
          <div className="flex items-center gap-3 mb-6">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-white font-bold text-sm">
              4
            </div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Settings2 className="h-5 w-5 text-slate-400" />
              Paper Configuration
            </h2>
          </div>
          <div className="pl-11 space-y-6">
            
            <div className="space-y-2 max-w-sm">
              <label className="text-sm font-semibold text-slate-700">Exam Type <span className="text-red-500">*</span></label>
              <select required value={examTypeId} onChange={e => setExamTypeId(e.target.value)} disabled={loadingExamTypes}
                className="flex h-11 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary text-slate-900"
              >
                <option value="">{loadingExamTypes ? 'Loading exam types...' : 'Select Exam Type format...'}</option>
                {examTypes.map((e: any) => (
                  <option key={e.id} value={e.id}>{e.name}</option>
                ))}
              </select>
            </div>

            <div className="pt-4">
              <div className="flex items-center justify-between mb-4">
                <label className="text-sm font-semibold text-slate-700">Question Counts</label>
                <span className="text-xs font-bold text-primary bg-primary/10 px-3 py-1 rounded-full">
                  Total Questions: {totalQuestions}
                </span>
              </div>
              
              <div className="grid md:grid-cols-2 gap-6">
                {/* MCQ Column */}
                <div className="space-y-4 bg-slate-50 p-5 rounded-2xl border border-slate-200">
                  <h4 className="text-sm font-bold text-slate-900">Multiple Choice (MCQ)</h4>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-1.5">
                      <label className="text-xs font-semibold text-green-600">Easy</label>
                      <input type="number" min="0" max="50" required value={mcqCounts.easy} onChange={e => setMcqCounts({...mcqCounts, easy: parseInt(e.target.value) || 0})}
                        className="flex h-10 w-full rounded-lg border border-slate-200 bg-white px-3 py-1 text-sm focus:ring-2 focus:ring-green-500/20" />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-xs font-semibold text-amber-600">Medium</label>
                      <input type="number" min="0" max="50" required value={mcqCounts.medium} onChange={e => setMcqCounts({...mcqCounts, medium: parseInt(e.target.value) || 0})}
                        className="flex h-10 w-full rounded-lg border border-slate-200 bg-white px-3 py-1 text-sm focus:ring-2 focus:ring-amber-500/20" />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-xs font-semibold text-red-600">Hard</label>
                      <input type="number" min="0" max="50" required value={mcqCounts.hard} onChange={e => setMcqCounts({...mcqCounts, hard: parseInt(e.target.value) || 0})}
                        className="flex h-10 w-full rounded-lg border border-slate-200 bg-white px-3 py-1 text-sm focus:ring-2 focus:ring-red-500/20" />
                    </div>
                  </div>
                </div>

                {/* Theory Column */}
                <div className="space-y-4 bg-slate-50 p-5 rounded-2xl border border-slate-200">
                  <h4 className="text-sm font-bold text-slate-900">Theory / Descriptive</h4>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-1.5">
                      <label className="text-xs font-semibold text-green-600">Easy</label>
                      <input type="number" min="0" max="50" required value={theoryCounts.easy} onChange={e => setTheoryCounts({...theoryCounts, easy: parseInt(e.target.value) || 0})}
                        className="flex h-10 w-full rounded-lg border border-slate-200 bg-white px-3 py-1 text-sm focus:ring-2 focus:ring-green-500/20" />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-xs font-semibold text-amber-600">Medium</label>
                      <input type="number" min="0" max="50" required value={theoryCounts.medium} onChange={e => setTheoryCounts({...theoryCounts, medium: parseInt(e.target.value) || 0})}
                        className="flex h-10 w-full rounded-lg border border-slate-200 bg-white px-3 py-1 text-sm focus:ring-2 focus:ring-amber-500/20" />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-xs font-semibold text-red-600">Hard</label>
                      <input type="number" min="0" max="50" required value={theoryCounts.hard} onChange={e => setTheoryCounts({...theoryCounts, hard: parseInt(e.target.value) || 0})}
                        className="flex h-10 w-full rounded-lg border border-slate-200 bg-white px-3 py-1 text-sm focus:ring-2 focus:ring-red-500/20" />
                    </div>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </Card>

        {/* Sticky Footer */}
        <div className="fixed bottom-0 left-0 right-0 lg:left-64 p-4 bg-white/80 backdrop-blur-md border-t border-slate-200 z-40 flex justify-end px-8">
          <Button 
            type="submit" 
            disabled={loading || !subjectId}
            size="lg"
            className="rounded-xl px-8 bg-primary hover:bg-primary/90 text-white shadow-md transition-all h-12 text-base font-semibold"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Generating Paper... This may take a minute.
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-5 w-5" />
                Generate AI Question Paper
              </>
            )}
          </Button>
        </div>

      </form>
    </div>
  );
}
