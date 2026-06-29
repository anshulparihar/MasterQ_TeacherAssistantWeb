'use client';

import { useState, useEffect } from 'react';
import { useAuthStore } from '@/store/auth';
import { useAdminStore } from '@/store/admin';
import { Loader2, Activity } from 'lucide-react';
import toast from 'react-hot-toast';

interface UsageLog {
  id: string;
  user_id: string;
  action_type: string;
  tokens_used: number;
  timestamp: string;
}

export default function UsagePage() {
  const token = useAuthStore(state => state.token);
  const selectedUserId = useAdminStore(state => state.selectedUserId);
  const [logs, setLogs] = useState<UsageLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadLogs() {
      if (!token) return;
      setLoading(true);
      try {
        const url = new URL('http://localhost:8000/admin/usage');
        if (selectedUserId) url.searchParams.append('user_id', selectedUserId);
        
        const res = await fetch(url.toString(), {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          setLogs(await res.json());
        }
      } catch (e) {
        toast.error('Failed to load usage logs');
      } finally {
        setLoading(false);
      }
    }
    loadLogs();
  }, [token, selectedUserId]);

  const totalTokens = logs.reduce((acc, curr) => acc + curr.tokens_used, 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Token Usage & Logs</h1>
        <p className="text-slate-500">Monitor AI token consumption across the platform.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">Total Tokens Used</p>
            <p className="text-2xl font-bold text-slate-900">{totalTokens.toLocaleString()}</p>
          </div>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-primary w-8 h-8"/></div>
        ) : (
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-50 text-slate-500 font-medium border-b border-slate-200">
              <tr>
                <th className="px-6 py-4">Timestamp</th>
                <th className="px-6 py-4">User ID</th>
                <th className="px-6 py-4">Action Type</th>
                <th className="px-6 py-4">Tokens Used</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-50">
                  <td className="px-6 py-4 whitespace-nowrap">{new Date(log.timestamp).toLocaleString()}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-slate-500 font-mono text-xs">{log.user_id}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      log.action_type === 'qgen' ? 'bg-purple-50 text-purple-700' : 'bg-emerald-50 text-emerald-700'
                    }`}>
                      {log.action_type.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-4 font-mono">{log.tokens_used.toLocaleString()}</td>
                </tr>
              ))}
              {logs.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center text-slate-500">No usage logs found.</td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
