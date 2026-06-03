'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

export default function AdminDashboardPage() {
  const [stats, setStats] = useState({
    total_users: 0,
    total_documents: 0,
    total_questions: 0,
    active_chat_sessions: 0
  });

  useEffect(() => {
    fetch('http://localhost:8000/admin/stats', {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
    })
    .then(res => res.json())
    .then(data => setStats(data))
    .catch(console.error);
  }, []);

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <h1 className="text-3xl font-bold">Admin Dashboard</h1>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border bg-card text-card-foreground shadow-sm p-6">
          <div className="flex flex-row items-center justify-between space-y-0 pb-2">
            <h3 className="tracking-tight text-sm font-medium">Total Users</h3>
          </div>
          <div className="text-2xl font-bold">{stats.total_users}</div>
        </div>
        
        <div className="rounded-xl border bg-card text-card-foreground shadow-sm p-6">
          <div className="flex flex-row items-center justify-between space-y-0 pb-2">
            <h3 className="tracking-tight text-sm font-medium">Total Documents</h3>
          </div>
          <div className="text-2xl font-bold">{stats.total_documents}</div>
        </div>
        
        <div className="rounded-xl border bg-card text-card-foreground shadow-sm p-6">
          <div className="flex flex-row items-center justify-between space-y-0 pb-2">
            <h3 className="tracking-tight text-sm font-medium">Total Questions</h3>
          </div>
          <div className="text-2xl font-bold">{stats.total_questions}</div>
        </div>
        
        <div className="rounded-xl border bg-card text-card-foreground shadow-sm p-6">
          <div className="flex flex-row items-center justify-between space-y-0 pb-2">
            <h3 className="tracking-tight text-sm font-medium">Active Chat Sessions</h3>
          </div>
          <div className="text-2xl font-bold">{stats.active_chat_sessions}</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mt-8">
        <Link href="/admin/users" className="p-4 border rounded-lg hover:bg-muted font-medium transition-colors">
          Manage Users →
        </Link>
        <Link href="/admin/exam-types" className="p-4 border rounded-lg hover:bg-muted font-medium transition-colors">
          Manage Exam Types →
        </Link>
        <Link href="/admin/subjects" className="p-4 border rounded-lg hover:bg-muted font-medium transition-colors">
          Manage Subjects →
        </Link>
        <Link href="/admin/documents" className="p-4 border rounded-lg hover:bg-muted font-medium transition-colors">
          Manage Admin Documents →
        </Link>
      </div>
    </div>
  );
}
