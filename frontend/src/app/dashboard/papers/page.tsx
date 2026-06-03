'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

export default function MyPapersPage() {
  const [papers, setPapers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchPapers = async () => {
    try {
      const res = await fetch('http://localhost:8000/questions/papers/me', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await res.json();
      setPapers(data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPapers();
  }, []);

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.preventDefault(); // Prevent navigating to the link
    if (!confirm('Are you sure you want to delete this paper?')) return;
    
    // In production we would map a DELETE /questions/papers/{id} router
    // Assuming it is implemented:
    try {
      await fetch(`http://localhost:8000/questions/papers/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      fetchPapers();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">My Generated Papers</h1>
        <Link href="/dashboard/generate" className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm font-medium hover:bg-primary/90">
          + New Paper
        </Link>
      </div>

      <div className="border rounded-xl bg-card shadow-sm overflow-hidden">
        <table className="w-full text-sm text-left">
          <thead className="bg-muted/50 text-muted-foreground">
            <tr>
              <th className="px-6 py-4 font-medium">Title</th>
              <th className="px-6 py-4 font-medium">Date</th>
              <th className="px-6 py-4 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {loading ? (
              <tr><td colSpan={3} className="p-8 text-center text-muted-foreground animate-pulse">Loading papers...</td></tr>
            ) : papers.length === 0 ? (
              <tr><td colSpan={3} className="p-8 text-center text-muted-foreground">No question papers found.</td></tr>
            ) : (
              papers.map(p => (
                <tr key={p.id} className="hover:bg-muted/30 transition-colors group relative cursor-pointer">
                  <td className="px-6 py-4">
                    <Link href={`/dashboard/papers/${p.id}`} className="absolute inset-0 z-0"></Link>
                    <div className="font-semibold relative z-10">{p.title || `Question Paper ${p.id.split('-')[0]}`}</div>
                  </td>
                  <td className="px-6 py-4 text-muted-foreground relative z-10">
                    {new Date(p.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 text-right relative z-10">
                    <button 
                      onClick={(e) => handleDelete(e, p.id)}
                      className="text-red-500 hover:text-red-700 font-medium px-3 py-1 rounded hover:bg-red-50 transition-colors"
                    >
                      Delete
                    </button>
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
