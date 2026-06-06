'use client';

import { useEffect, useState } from 'react';
import { Plus, PenTool, Trash2 } from 'lucide-react';
import { api } from '@/lib/api';
import toast from 'react-hot-toast';

export default function AdminExamTypesPage() {
  const [examTypes, setExamTypes] = useState<any[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  
  const [newName, setNewName] = useState('');
  const [newGuidelines, setNewGuidelines] = useState('{\n  "easy": {},\n  "medium": {},\n  "hard": {}\n}');

  const fetchExams = async () => {
    setIsLoading(true);
    try {
      const res = await api.get('/admin/exam-types');
      setExamTypes(res.data);
    } catch (e) {
      console.error(e);
      toast.error('Failed to load exam types');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchExams();
  }, []);

  const handleCreate = async () => {
    if (!newName.trim()) {
      toast.error('Exam name is required');
      return;
    }
    
    let parsedJSON;
    try {
      parsedJSON = JSON.parse(newGuidelines);
    } catch (e) {
      toast.error('Invalid JSON format in guidelines');
      return;
    }

    try {
      await api.post('/admin/exam-types', { name: newName, guidelines: parsedJSON });
      setIsCreating(false);
      setNewName('');
      setNewGuidelines('{\n  "easy": {},\n  "medium": {},\n  "hard": {}\n}');
      fetchExams();
      toast.success('Exam type created successfully');
    } catch (e) {
      console.error(e);
      toast.error('Failed to create exam type');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this exam type?')) return;
    try {
      await api.delete(`/admin/exam-types/${id}`);
      fetchExams();
      toast.success('Exam type deleted successfully');
    } catch (e) {
      console.error(e);
      toast.error("Failed to delete exam type");
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8 animate-in fade-in duration-500 pb-24">
      <div className="flex justify-between items-center bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-indigo-50 rounded-xl flex items-center justify-center">
            <PenTool className="w-6 h-6 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">Exam Types Management</h1>
            <p className="text-sm text-slate-500">Define exam structures and generation guidelines.</p>
          </div>
        </div>
        <button 
          onClick={() => setIsCreating(true)}
          className="flex items-center gap-2 bg-primary text-white px-5 py-2.5 rounded-xl font-bold hover:bg-primary/90 shadow-sm transition-all"
        >
          <Plus className="w-4 h-4" />
          Add Exam Type
        </button>
      </div>

      {isCreating && (
        <div className="bg-white border border-slate-200 p-6 rounded-2xl shadow-sm space-y-4 animate-in slide-in-from-top-4 duration-300">
          <h2 className="text-lg font-bold text-slate-800">Create New Exam Type</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Exam Name</label>
              <input 
                placeholder="e.g. CBSE Class 12, AP Calculus AB" 
                value={newName} onChange={e => setNewName(e.target.value)}
                className="w-full border border-slate-200 bg-slate-50 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:bg-white transition-all"
              />
            </div>
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Generation Guidelines (JSON)</label>
              <textarea 
                rows={10}
                placeholder="Guidelines JSON"
                value={newGuidelines} onChange={e => setNewGuidelines(e.target.value)}
                className="w-full border border-slate-200 bg-slate-50 rounded-xl px-4 py-3 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:bg-white transition-all custom-scrollbar"
              />
              <p className="text-xs text-slate-400 mt-2">Provide a valid JSON object detailing the generation prompt rules.</p>
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
            <button 
              onClick={() => setIsCreating(false)} 
              className="px-6 py-2.5 rounded-xl font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
            >
              Cancel
            </button>
            <button 
              onClick={handleCreate} 
              className="bg-primary text-white px-6 py-2.5 rounded-xl font-bold hover:bg-primary/90 shadow-sm transition-all"
            >
              Save Exam Type
            </button>
          </div>
        </div>
      )}

      <div className="grid gap-6">
        {isLoading ? (
          <div className="p-12 text-center text-slate-400 font-medium border border-slate-200 border-dashed rounded-2xl">
            Loading exam types...
          </div>
        ) : examTypes.length === 0 ? (
          <div className="p-12 text-center text-slate-400 font-medium border border-slate-200 border-dashed rounded-2xl bg-slate-50/50">
            No exam types found. Create one to get started.
          </div>
        ) : (
          examTypes.map(e => (
            <div key={e.id} className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden hover:shadow-md transition-shadow group">
              <div className="p-5 border-b border-slate-100 bg-slate-50 flex justify-between items-center">
                <h3 className="text-lg font-bold text-slate-900">{e.name}</h3>
                <button 
                  onClick={() => handleDelete(e.id)}
                  className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100"
                  title="Delete Exam Type"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
              <div className="p-5">
                <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-2">Guidelines Configuration</label>
                <div className="bg-slate-900 rounded-xl p-4 overflow-x-auto custom-scrollbar">
                  <pre className="text-xs text-slate-300 font-mono">
                    {JSON.stringify(e.guidelines, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
