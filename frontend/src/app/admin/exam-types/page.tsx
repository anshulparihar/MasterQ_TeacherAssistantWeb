'use client';

import { useEffect, useState } from 'react';

export default function AdminExamTypesPage() {
  const [examTypes, setExamTypes] = useState<any[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [newName, setNewName] = useState('');
  const [newGuidelines, setNewGuidelines] = useState('{\n  "easy": {},\n  "medium": {},\n  "hard": {}\n}');

  const fetchExams = async () => {
    try {
      const res = await fetch('http://localhost:8000/admin/exam-types', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await res.json();
      setExamTypes(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchExams();
  }, []);

  const handleCreate = async () => {
    try {
      const parsedJSON = JSON.parse(newGuidelines);
      await fetch('http://localhost:8000/admin/exam-types', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}` 
        },
        body: JSON.stringify({ name: newName, guidelines: parsedJSON })
      });
      setIsCreating(false);
      setNewName('');
      setNewGuidelines('');
      fetchExams();
    } catch (e) {
      alert("Invalid JSON format or network error");
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Exam Types Management</h1>
        <button 
          onClick={() => setIsCreating(true)}
          className="bg-primary text-primary-foreground px-4 py-2 rounded hover:bg-primary/90"
        >
          + Add Exam Type
        </button>
      </div>

      {isCreating && (
        <div className="bg-card border p-6 rounded-lg space-y-4">
          <h2 className="font-semibold">Create New Exam Type</h2>
          <input 
            placeholder="Exam Name (e.g. CBSE Class 12)" 
            value={newName} onChange={e => setNewName(e.target.value)}
            className="w-full border rounded px-3 py-2"
          />
          <textarea 
            rows={10}
            placeholder="Guidelines JSON"
            value={newGuidelines} onChange={e => setNewGuidelines(e.target.value)}
            className="w-full border rounded px-3 py-2 font-mono text-sm"
          />
          <div className="flex gap-2">
            <button onClick={handleCreate} className="bg-primary text-primary-foreground px-4 py-2 rounded">Save</button>
            <button onClick={() => setIsCreating(false)} className="border px-4 py-2 rounded">Cancel</button>
          </div>
        </div>
      )}

      <div className="grid gap-4">
        {examTypes.map(e => (
          <div key={e.id} className="border rounded-lg p-6 bg-card">
            <h3 className="text-xl font-bold mb-4">{e.name}</h3>
            <pre className="bg-muted p-4 rounded text-sm overflow-x-auto">
              {JSON.stringify(e.guidelines, null, 2)}
            </pre>
          </div>
        ))}
      </div>
    </div>
  );
}
