'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Activity, FileText, MessageSquare, HelpCircle, Filter, Users, LayoutList, BookOpen, PenTool } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';
import { api } from '@/lib/api';
import toast from 'react-hot-toast';

export default function AdminDashboardPage() {
  const [stats, setStats] = useState({
    total_users: 0,
    total_documents: 0,
    total_questions: 0,
    active_chat_sessions: 0
  });

  const [activities, setActivities] = useState<any[]>([]);
  const [chartData, setChartData] = useState<any[]>([]);
  const [filterUser, setFilterUser] = useState('');
  const [filterType, setFilterType] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [hiddenLines, setHiddenLines] = useState<Record<string, boolean>>({});

  useEffect(() => {
    fetchStats();
    fetchActivities();
  }, []);

  const fetchStats = async () => {
    try {
      const res = await api.get('/admin/stats');
      setStats(res.data);
    } catch (e) {
      console.error(e);
      toast.error('Failed to load admin stats');
    }
  };

  const fetchActivities = async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams();
      if (filterUser) params.append('user_email', filterUser);
      if (filterType) params.append('activity_type', filterType);
      
      const res = await api.get(`/admin/activity?${params.toString()}`);
      setActivities(res.data);
      processChartData(res.data);
    } catch (e) {
      console.error(e);
      toast.error('Failed to load activity feed');
    } finally {
      setIsLoading(false);
    }
  };

  const processChartData = (data: any[]) => {
    const dateMap: Record<string, any> = {};
    const sorted = [...data].sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
    
    sorted.forEach(act => {
      const dateStr = new Date(act.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
      if (!dateMap[dateStr]) {
        dateMap[dateStr] = { date: dateStr, Documents: 0, Questions: 0, Chats: 0 };
      }
      
      if (act.type === 'document') dateMap[dateStr].Documents += 1;
      if (act.type === 'question') dateMap[dateStr].Questions += 1;
      if (act.type === 'chat') dateMap[dateStr].Chats += 1;
    });

    setChartData(Object.values(dateMap));
  };

  const handleFilterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchActivities();
  };

  const toggleLine = (dataKey: string) => {
    setHiddenLines(prev => ({ ...prev, [dataKey]: !prev[dataKey] }));
  };

  const getActivityIcon = (type: string) => {
    switch(type) {
      case 'document': return <FileText className="w-4 h-4 text-emerald-500" />;
      case 'chat': return <MessageSquare className="w-4 h-4 text-blue-500" />;
      case 'question': return <HelpCircle className="w-4 h-4 text-indigo-500" />;
      default: return <Activity className="w-4 h-4 text-slate-500" />;
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-500 pb-24">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">System Administration</h1>
        <p className="text-sm text-slate-500 mt-1">Platform overview and management dashboard.</p>
      </div>
      
      {/* Stats Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 hover:shadow-md transition-shadow">
          <div className="flex flex-row items-center justify-between pb-2">
            <h3 className="tracking-tight text-sm font-semibold text-slate-500">Total Users</h3>
            <div className="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center">
              <Users className="w-4 h-4 text-primary" />
            </div>
          </div>
          <div className="text-3xl font-bold text-slate-900">{stats.total_users}</div>
        </div>
        
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 hover:shadow-md transition-shadow">
          <div className="flex flex-row items-center justify-between pb-2">
            <h3 className="tracking-tight text-sm font-semibold text-slate-500">Total Documents</h3>
            <div className="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center">
              <FileText className="w-4 h-4 text-primary" />
            </div>
          </div>
          <div className="text-3xl font-bold text-slate-900">{stats.total_documents}</div>
        </div>
        
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 hover:shadow-md transition-shadow">
          <div className="flex flex-row items-center justify-between pb-2">
            <h3 className="tracking-tight text-sm font-semibold text-slate-500">Total Questions</h3>
            <div className="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center">
              <HelpCircle className="w-4 h-4 text-primary" />
            </div>
          </div>
          <div className="text-3xl font-bold text-slate-900">{stats.total_questions}</div>
        </div>
        
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 hover:shadow-md transition-shadow">
          <div className="flex flex-row items-center justify-between pb-2">
            <h3 className="tracking-tight text-sm font-semibold text-slate-500">Chat Sessions</h3>
            <div className="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center">
              <MessageSquare className="w-4 h-4 text-primary" />
            </div>
          </div>
          <div className="text-3xl font-bold text-slate-900">{stats.active_chat_sessions}</div>
        </div>
      </div>

      {/* Quick Links */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
        <Link href="/admin/users" className="group p-5 bg-white border border-slate-200 rounded-2xl shadow-sm hover:border-primary/50 hover:shadow-md transition-all flex flex-col items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-slate-50 group-hover:bg-indigo-50 flex items-center justify-center transition-colors">
            <Users className="w-5 h-5 text-slate-500 group-hover:text-primary transition-colors" />
          </div>
          <span className="font-semibold text-slate-700 text-sm">Manage Users</span>
        </Link>
        <Link href="/admin/exam-types" className="group p-5 bg-white border border-slate-200 rounded-2xl shadow-sm hover:border-primary/50 hover:shadow-md transition-all flex flex-col items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-slate-50 group-hover:bg-indigo-50 flex items-center justify-center transition-colors">
            <PenTool className="w-5 h-5 text-slate-500 group-hover:text-primary transition-colors" />
          </div>
          <span className="font-semibold text-slate-700 text-sm">Manage Exams</span>
        </Link>
        <Link href="/admin/subjects" className="group p-5 bg-white border border-slate-200 rounded-2xl shadow-sm hover:border-primary/50 hover:shadow-md transition-all flex flex-col items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-slate-50 group-hover:bg-indigo-50 flex items-center justify-center transition-colors">
            <BookOpen className="w-5 h-5 text-slate-500 group-hover:text-primary transition-colors" />
          </div>
          <span className="font-semibold text-slate-700 text-sm">Manage Subjects</span>
        </Link>
        <Link href="/admin/documents" className="group p-5 bg-white border border-slate-200 rounded-2xl shadow-sm hover:border-primary/50 hover:shadow-md transition-all flex flex-col items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-slate-50 group-hover:bg-indigo-50 flex items-center justify-center transition-colors">
            <FileText className="w-5 h-5 text-slate-500 group-hover:text-primary transition-colors" />
          </div>
          <span className="font-semibold text-slate-700 text-sm">Admin Documents</span>
        </Link>
      </div>

      <div className="grid lg:grid-cols-3 gap-8 mt-8">
        {/* Chart Section */}
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
          <h2 className="text-xl font-bold flex items-center gap-2 mb-8 text-slate-900">
            <Activity className="w-5 h-5 text-primary" />
            System Activity Trends
          </h2>
          <div className="h-[320px] w-full">
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="date" fontSize={12} tickLine={false} axisLine={false} tick={{ fill: '#64748b' }} dy={10} />
                  <YAxis fontSize={12} tickLine={false} axisLine={false} tick={{ fill: '#64748b' }} dx={-10} allowDecimals={false} />
                  <Tooltip 
                    contentStyle={{ borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)', fontWeight: 500 }} 
                  />
                  <Legend 
                    verticalAlign="top" 
                    height={40} 
                    onClick={(e) => {
                      if (typeof e.dataKey === 'string') {
                        toggleLine(e.dataKey);
                      }
                    }}
                    wrapperStyle={{ cursor: 'pointer', fontSize: '13px', fontWeight: 500 }}
                  />
                  <Line type="monotone" dataKey="Documents" stroke="#10b981" strokeWidth={3} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6 }} hide={hiddenLines['Documents']} />
                  <Line type="monotone" dataKey="Questions" stroke="#6366f1" strokeWidth={3} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6 }} hide={hiddenLines['Questions']} />
                  <Line type="monotone" dataKey="Chats" stroke="#3b82f6" strokeWidth={3} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6 }} hide={hiddenLines['Chats']} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 bg-slate-50/50 rounded-xl border border-dashed border-slate-200">
                <Activity className="h-8 w-8 mb-2 opacity-20" />
                <span>Not enough data to graph trends.</span>
              </div>
            )}
          </div>
        </div>

        {/* Activity Feed Section */}
        <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm flex flex-col h-[420px]">
          <div className="p-5 border-b border-slate-100 bg-slate-50 shrink-0">
            <h2 className="text-lg font-bold flex items-center gap-2 text-slate-900">
              <LayoutList className="w-5 h-5 text-primary" />
              Live Feed
            </h2>
            
            <form onSubmit={handleFilterSubmit} className="mt-4 flex flex-col gap-2">
              <input 
                type="text" 
                placeholder="Filter by Email..." 
                value={filterUser}
                onChange={e => setFilterUser(e.target.value)}
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-xs bg-white focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all"
              />
              <div className="flex gap-2">
                <select 
                  value={filterType}
                  onChange={e => setFilterType(e.target.value)}
                  className="flex-1 border border-slate-200 rounded-lg px-2 py-2 text-xs bg-white focus:outline-none focus:ring-2 focus:ring-primary transition-all"
                >
                  <option value="">All Types</option>
                  <option value="document">Uploads</option>
                  <option value="chat">Chats</option>
                  <option value="question">Generations</option>
                </select>
                <button type="submit" className="bg-primary text-white px-4 py-2 rounded-lg text-xs font-bold hover:bg-primary/90 shadow-sm transition-colors">
                  Filter
                </button>
              </div>
            </form>
          </div>

          <div className="divide-y divide-slate-100 overflow-y-auto flex-1 custom-scrollbar">
            {isLoading ? (
              <div className="p-8 text-center text-xs text-slate-400 font-medium">Loading feed...</div>
            ) : activities.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-400 font-medium">No recent activity found.</div>
            ) : (
              activities.map((act) => (
                <div key={act.id} className="p-4 flex items-start gap-3 hover:bg-slate-50 transition-colors">
                  <div className="mt-0.5 p-2 bg-white border border-slate-100 rounded-full shrink-0 shadow-sm">
                    {getActivityIcon(act.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-start gap-2">
                      <p className="text-xs font-bold text-slate-700 truncate">
                        {act.user_email}
                      </p>
                      <span className="text-[10px] text-slate-400 whitespace-nowrap shrink-0 font-medium">
                        {new Date(act.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 mt-1 truncate">
                      {act.title}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

    </div>
  );
}
