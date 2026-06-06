'use client';

import { useEffect, useState } from 'react';
import { Users, Shield, ShieldAlert, Trash2 } from 'lucide-react';
import { api } from '@/lib/api';
import toast from 'react-hot-toast';

export default function AdminUsersPage() {
  const [users, setUsers] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchUsers = async () => {
    setIsLoading(true);
    try {
      const res = await api.get('/admin/users');
      setUsers(res.data);
    } catch (e) {
      console.error(e);
      toast.error('Failed to load users');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const changeRole = async (userId: string, newRole: string) => {
    try {
      await api.put(`/admin/users/${userId}/role`, { role: newRole });
      fetchUsers();
      toast.success('User role updated successfully');
    } catch (e) {
      console.error(e);
      toast.error('Failed to update role');
    }
  };

  const deleteUser = async (userId: string) => {
    if (!confirm('Are you sure you want to deactivate this user?')) return;
    try {
      await api.delete(`/admin/users/${userId}`);
      fetchUsers();
      toast.success('User deactivated successfully');
    } catch (e) {
      console.error(e);
      toast.error('Failed to deactivate user');
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8 animate-in fade-in duration-500 pb-24">
      <div className="flex justify-between items-center bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-indigo-50 rounded-xl flex items-center justify-center">
            <Users className="w-6 h-6 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">User Management</h1>
            <p className="text-sm text-slate-500">Manage user roles and account statuses.</p>
          </div>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
        <table className="w-full text-sm text-left">
          <thead className="bg-slate-50 border-b border-slate-100">
            <tr>
              <th className="px-6 py-4 font-bold text-slate-700">Email</th>
              <th className="px-6 py-4 font-bold text-slate-700">Role</th>
              <th className="px-6 py-4 font-bold text-slate-700">Joined</th>
              <th className="px-6 py-4 font-bold text-slate-700 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {isLoading ? (
              <tr>
                <td colSpan={4} className="px-6 py-12 text-center text-slate-400 font-medium">
                  Loading users...
                </td>
              </tr>
            ) : users.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-6 py-12 text-center text-slate-400 font-medium bg-slate-50/50">
                  No users found.
                </td>
              </tr>
            ) : (
              users.map(u => (
                <tr key={u.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4 font-semibold text-slate-800">{u.email}</td>
                  <td className="px-6 py-4">
                    <div className="relative inline-flex items-center">
                      {u.role === 'admin' ? <ShieldAlert className="absolute left-3 w-3 h-3 text-red-500" /> : <Shield className="absolute left-3 w-3 h-3 text-slate-400" />}
                      <select 
                        value={u.role}
                        onChange={(e) => changeRole(u.id, e.target.value)}
                        className={`pl-8 pr-4 py-1.5 rounded-lg text-xs font-bold transition-all border ${u.role === 'admin' ? 'bg-red-50 text-red-700 border-red-200 focus:ring-red-500' : 'bg-slate-50 text-slate-700 border-slate-200 focus:ring-primary'} focus:outline-none focus:ring-2`}
                      >
                        <option value="user">User</option>
                        <option value="admin">Admin</option>
                      </select>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-slate-500 font-medium">{new Date(u.created_at).toLocaleDateString()}</td>
                  <td className="px-6 py-4 text-right">
                    <button 
                      onClick={() => deleteUser(u.id)}
                      className="px-3 py-1.5 text-red-500 hover:text-red-700 hover:bg-red-50 font-semibold rounded-lg text-xs transition-colors"
                    >
                      Deactivate
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
