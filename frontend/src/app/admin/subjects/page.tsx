'use client';

import { useEffect, useState } from 'react';
import { Edit, Trash2, Plus, BookOpen } from 'lucide-react';
import { api } from '@/lib/api';
import toast from 'react-hot-toast';

export default function AdminSubjectsPage() {
  const [subjects, setSubjects] = useState<any[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [isEditing, setIsEditing] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  const [nameInput, setNameInput] = useState('');
  const [levelsInput, setLevelsInput] = useState('');

  const fetchSubjects = async () => {
    setIsLoading(true);
    try {
      const res = await api.get('/admin/subjects');
      setSubjects(res.data);
    } catch (e) {
      console.error(e);
      toast.error('Failed to load subjects');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSubjects();
  }, []);

  const handleCreate = async () => {
    try {
      const levelsArray = levelsInput.split(',').map(s => s.trim()).filter(Boolean);
      await api.post('/admin/subjects', { name: nameInput, academic_levels: levelsArray });
      setIsCreating(false);
      setNameInput('');
      setLevelsInput('');
      fetchSubjects();
      toast.success('Subject created successfully');
    } catch (e) {
      console.error(e);
      toast.error("Failed to create subject");
    }
  };

  const handleUpdate = async (id: string) => {
    try {
      const levelsArray = levelsInput.split(',').map(s => s.trim()).filter(Boolean);
      await api.put(`/admin/subjects/${id}`, { name: nameInput, academic_levels: levelsArray });
      setIsEditing(null);
      setNameInput('');
      setLevelsInput('');
      fetchSubjects();
      toast.success('Subject updated successfully');
    } catch (e) {
      console.error(e);
      toast.error("Failed to update subject");
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this subject? All related topics and question papers will be deleted.')) return;
    try {
      await api.delete(`/admin/subjects/${id}`);
      fetchSubjects();
      toast.success('Subject deleted successfully');
    } catch (e) {
      console.error(e);
      toast.error("Failed to delete subject");
    }
  };

  const startEdit = (subject: any) => {
    let lvlString = "";
    if (Array.isArray(subject.academic_levels)) {
      lvlString = subject.academic_levels.join(', ');
    } else if (typeof subject.academic_levels === 'string' && subject.academic_levels.startsWith('[')) {
      lvlString = JSON.parse(subject.academic_levels).join(', ');
    } else {
      lvlString = subject.academic_levels || '';
    }
    setNameInput(subject.name);
    setLevelsInput(lvlString);
    setIsEditing(subject.id);
    setIsCreating(false);
  };

  const startCreate = () => {
    setNameInput('');
    setLevelsInput('');
    setIsCreating(true);
    setIsEditing(null);
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8 animate-in fade-in duration-500 pb-24">
      <div className="flex justify-between items-center bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-indigo-50 rounded-xl flex items-center justify-center">
            <BookOpen className="w-6 h-6 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">Subjects Management</h1>
            <p className="text-sm text-slate-500">Add, edit, or remove subjects for the platform.</p>
          </div>
        </div>
        <button 
          onClick={startCreate}
          className="flex items-center gap-2 bg-primary text-white px-5 py-2.5 rounded-xl font-bold hover:bg-primary/90 shadow-sm transition-all"
        >
          <Plus className="w-4 h-4" />
          Add Subject
        </button>
      </div>

      {(isCreating || isEditing) && (
        <div className="bg-white border border-slate-200 p-6 rounded-2xl shadow-sm space-y-4 animate-in slide-in-from-top-4 duration-300">
          <h2 className="text-lg font-bold text-slate-800">{isEditing ? 'Edit Subject' : 'Create New Subject'}</h2>
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Subject Name</label>
              <input 
                placeholder="e.g. Mathematics" 
                value={nameInput} onChange={e => setNameInput(e.target.value)}
                className="w-full border border-slate-200 bg-slate-50 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:bg-white transition-all"
              />
            </div>
            <div className="flex-1">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Academic Levels (comma separated)</label>
              <input 
                placeholder="e.g. 9, 10, 11, UG"
                value={levelsInput} onChange={e => setLevelsInput(e.target.value)}
                className="w-full border border-slate-200 bg-slate-50 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:bg-white transition-all"
              />
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
            <button 
              onClick={() => { setIsCreating(false); setIsEditing(null); }} 
              className="px-6 py-2.5 rounded-xl font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
            >
              Cancel
            </button>
            <button 
              onClick={() => isEditing ? handleUpdate(isEditing) : handleCreate()} 
              className="bg-primary text-white px-6 py-2.5 rounded-xl font-bold hover:bg-primary/90 shadow-sm transition-all"
            >
              Save Subject
            </button>
          </div>
        </div>
      )}

      <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
        <table className="w-full text-sm text-left">
          <thead className="bg-slate-50 border-b border-slate-100">
            <tr>
              <th className="px-6 py-4 font-bold text-slate-700">Subject Name</th>
              <th className="px-6 py-4 font-bold text-slate-700">Academic Levels</th>
              <th className="px-6 py-4 font-bold text-slate-700 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {isLoading ? (
              <tr>
                <td colSpan={3} className="px-6 py-12 text-center text-slate-400 font-medium">
                  Loading subjects...
                </td>
              </tr>
            ) : subjects.length === 0 ? (
              <tr>
                <td colSpan={3} className="px-6 py-12 text-center text-slate-400 font-medium bg-slate-50/50">
                  No subjects found. Add a subject to get started.
                </td>
              </tr>
            ) : (
              subjects.map(s => (
                <tr key={s.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4 font-semibold text-slate-800">{s.name}</td>
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-2">
                      {Array.isArray(s.academic_levels) 
                        ? s.academic_levels.map((lvl: string, idx: number) => (
                            <span key={idx} className="bg-primary/10 text-primary px-2.5 py-1 rounded-md text-xs font-bold">{lvl}</span>
                          ))
                        : typeof s.academic_levels === 'string' && s.academic_levels.startsWith('[')
                          ? JSON.parse(s.academic_levels).map((lvl: string, idx: number) => (
                              <span key={idx} className="bg-primary/10 text-primary px-2.5 py-1 rounded-md text-xs font-bold">{lvl}</span>
                            ))
                          : <span className="bg-primary/10 text-primary px-2.5 py-1 rounded-md text-xs font-bold">{s.academic_levels}</span>}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex justify-end gap-2">
                      <button 
                        onClick={() => startEdit(s)}
                        className="p-2 text-slate-400 hover:text-primary hover:bg-primary/5 rounded-lg transition-colors"
                        title="Edit Subject"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button 
                        onClick={() => handleDelete(s.id)}
                        className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        title="Delete Subject"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
