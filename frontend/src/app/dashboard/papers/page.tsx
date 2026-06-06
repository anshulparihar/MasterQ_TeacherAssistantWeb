'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { useAuthStore } from '@/store/auth';
import { BackButton } from '@/components/ui/BackButton';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileText, Sparkles, Trash2, AlertTriangle, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';

export default function MyPapersPage() {
  const [papers, setPapers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showDeleteModal, setShowDeleteModal] = useState<string | null>(null);
  const { user } = useAuthStore();

  const fetchPapers = async () => {
    try {
      setLoading(true);
      const res = await api.get('/questions/papers/me');
      setPapers(res.data || []);
    } catch (e) {
      console.error(e);
      toast.error('Failed to load papers');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      fetchPapers();
    }
  }, [user]);

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/questions/papers/${id}`);
      setPapers(papers.filter(p => p.id !== id));
      setShowDeleteModal(null);
      toast.success('Paper deleted successfully');
    } catch (err) {
      console.error(err);
      toast.error('Failed to delete paper');
    }
  };

  return (
    <div className="animate-in fade-in slide-in-from-top-4 duration-300 pb-12">
      <BackButton />
      
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Papers Archive</h1>
          <p className="text-sm text-slate-500 mt-1">
            View, edit and export your generated question papers.
          </p>
        </div>
        <Button asChild className="bg-primary hover:bg-primary/90 shadow-sm rounded-xl px-5 h-11">
          <Link href="/dashboard/generate">
            <Sparkles className="h-4 w-4 mr-2" />
            New Paper
          </Link>
        </Button>
      </div>

      <Card className="border border-slate-200 shadow-sm bg-white rounded-2xl overflow-hidden">
        {loading ? (
          <div className="flex justify-center items-center h-48">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : papers.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
            <FileText className="h-12 w-12 text-slate-300 mb-4" />
            <h3 className="text-lg font-semibold text-slate-900">No papers generated yet</h3>
            <p className="text-slate-500 text-sm mt-1 max-w-sm">
              You haven't generated any question papers. Get started by creating your first AI paper.
            </p>
            <Button asChild variant="outline" className="mt-6 rounded-xl">
              <Link href="/dashboard/generate">
                <Sparkles className="h-4 w-4 mr-2" />
                Generate your first paper
              </Link>
            </Button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-4 font-semibold">Title</th>
                  <th className="px-6 py-4 font-semibold">Subject</th>
                  <th className="px-6 py-4 font-semibold">Date</th>
                  <th className="px-6 py-4 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {papers.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50/50 transition-colors group">
                    <td className="px-6 py-4">
                      <Link href={`/dashboard/papers/${p.id}`} className="flex items-center gap-3 w-fit">
                        <FileText className="h-5 w-5 text-slate-400 shrink-0 group-hover:text-primary transition-colors" />
                        <span className="font-medium text-slate-900 group-hover:text-primary transition-colors">
                          {p.title || `Question Paper ${p.id.split('-')[0]}`}
                        </span>
                      </Link>
                    </td>
                    <td className="px-6 py-4 text-slate-500">
                      {p.subject?.name || 'Uncategorized'}
                    </td>
                    <td className="px-6 py-4 text-slate-500">
                      {new Date(p.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button 
                        onClick={() => setShowDeleteModal(p.id)}
                        className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        title="Delete Paper"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-white w-full max-w-sm rounded-2xl shadow-2xl p-6 text-center animate-in zoom-in-95 duration-200">
            <div className="mx-auto w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mb-4">
              <AlertTriangle className="h-6 w-6 text-red-600" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 mb-2">Delete Paper?</h3>
            <p className="text-sm text-slate-500 mb-6">This action cannot be undone. This will permanently delete the question paper.</p>
            <div className="flex gap-3 justify-center">
              <Button variant="outline" onClick={() => setShowDeleteModal(null)} className="rounded-xl h-11 px-6 flex-1">
                Cancel
              </Button>
              <Button variant="destructive" onClick={() => handleDelete(showDeleteModal)} className="rounded-xl h-11 px-6 flex-1 bg-red-600 hover:bg-red-700">
                Delete
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
