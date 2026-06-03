'use client';

import { useEffect, useState } from 'react';

export default function AdminSubjectsPage() {
  const [subjects, setSubjects] = useState<any[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [newName, setNewName] = useState('');
  const [newLevels, setNewLevels] = useState('');

  const fetchSubjects = async () => {
    try {
      const res = await fetch('http://localhost:8000/admin/subjects', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await res.json();
      setSubjects(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchSubjects();
  }, []);

  const handleCreate = async () => {
    try {
      const levelsArray = newLevels.split(',').map(s => s.trim()).filter(Boolean);
      await fetch('http://localhost:8000/admin/subjects', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}` 
        },
        body: JSON.stringify({ name: newName, academic_levels: levelsArray })
      });
      setIsCreating(false);
      setNewName('');
      setNewLevels('');
      fetchSubjects();
    } catch (e) {
      alert("Failed to create subject");
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Subjects Management</h1>
        <button 
          onClick={() => setIsCreating(true)}
          className="bg-primary text-primary-foreground px-4 py-2 rounded hover:bg-primary/90"
        >
          + Add Subject
        </button>
      </div>

      {isCreating && (
        <div className="bg-card border p-6 rounded-lg space-y-4">
          <h2 className="font-semibold">Create New Subject</h2>
          <input 
            placeholder="Subject Name (e.g. Mathematics)" 
            value={newName} onChange={e => setNewName(e.target.value)}
            className="w-full border rounded px-3 py-2"
          />
          <input 
            placeholder="Academic Levels (comma separated: 9, 10, 11, UG)"
            value={newLevels} onChange={e => setNewLevels(e.target.value)}
            className="w-full border rounded px-3 py-2"
          />
          <div className="flex gap-2">
            <button onClick={handleCreate} className="bg-primary text-primary-foreground px-4 py-2 rounded">Save</button>
            <button onClick={() => setIsCreating(false)} className="border px-4 py-2 rounded">Cancel</button>
          </div>
        </div>
      )}

      <div className="border rounded-md">
        <table className="w-full text-sm text-left">
          <thead className="bg-muted text-muted-foreground">
            <tr>
              <th className="px-4 py-3 font-medium">Subject Name</th>
              <th className="px-4 py-3 font-medium">Academic Levels</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {subjects.map(s => (
              <tr key={s.id} className="bg-card hover:bg-muted/50 transition-colors">
                <td className="px-4 py-3 font-medium">{s.name}</td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {Array.isArray(s.academic_levels) 
                      ? s.academic_levels.map((lvl: string, idx: number) => (
                          <span key={idx} className="bg-primary/10 text-primary px-2 py-1 rounded text-xs">{lvl}</span>
                        ))
                      : typeof s.academic_levels === 'string' && s.academic_levels.startsWith('[')
                        ? JSON.parse(s.academic_levels).map((lvl: string, idx: number) => (
                            <span key={idx} className="bg-primary/10 text-primary px-2 py-1 rounded text-xs">{lvl}</span>
                          ))
                        : <span>{s.academic_levels}</span>}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
