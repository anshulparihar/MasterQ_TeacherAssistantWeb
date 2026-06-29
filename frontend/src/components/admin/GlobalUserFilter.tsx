'use client';

import { useEffect, useState } from 'react';
import { useAdminStore } from '@/store/admin';
import { Loader2, Users } from 'lucide-react';
import { useAuthStore } from '@/store/auth';

interface User {
  id: string;
  email: string;
  role: string;
}

export function GlobalUserFilter() {
  const { selectedUserId, setSelectedUserId } = useAdminStore();
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const token = useAuthStore(state => state.token);

  useEffect(() => {
    async function fetchUsers() {
      if (!token) return;
      try {
        const res = await fetch('http://localhost:8000/admin/users', {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setUsers(data);
        }
      } catch (error) {
        console.error('Failed to fetch users:', error);
      } finally {
        setIsLoading(false);
      }
    }
    fetchUsers();
  }, [token]);

  if (isLoading) {
    return <div className="flex items-center gap-2 text-sm text-slate-500"><Loader2 className="w-4 h-4 animate-spin"/> Loading users...</div>;
  }

  return (
    <div className="flex items-center gap-2 bg-white border border-slate-200 rounded-lg p-2 shadow-sm">
      <Users className="w-4 h-4 text-slate-500" />
      <span className="text-sm font-medium text-slate-700">View Data For:</span>
      <select 
        className="text-sm border-none bg-transparent focus:ring-0 text-slate-900 cursor-pointer outline-none"
        value={selectedUserId || ''}
        onChange={(e) => setSelectedUserId(e.target.value || null)}
      >
        <option value="">All Users (Global)</option>
        {users.map(u => (
          <option key={u.id} value={u.id}>{u.email}</option>
        ))}
      </select>
    </div>
  );
}
