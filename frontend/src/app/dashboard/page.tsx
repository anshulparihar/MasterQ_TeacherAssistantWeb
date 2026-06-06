'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileText, Wand2, MessageSquare, ClipboardCheck, ArrowRight, FolderOpen, Sparkles, BookOpen, BarChart3, ClipboardList } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const QUICK = [
  { to: "/dashboard/documents", title: "Upload Documents", desc: "Add syllabi, textbooks and past papers.", icon: FolderOpen, soon: false },
  { to: "/dashboard/generate", title: "Generate a Paper", desc: "Configure topics, MCQ/theory mix and difficulty.", icon: Wand2, soon: false },
  { to: "/dashboard/chat", title: "Ask Chatbot", desc: "Query your library or specific documents.", icon: MessageSquare, soon: false },
  { to: "#", title: "Score Answers", desc: "Upload student answers for instant scoring.", icon: ClipboardCheck, soon: true },
];

export default function DashboardHomePage() {
  const [allPapers, setAllPapers] = useState<any[]>([]);
  const [allDocs, setAllDocs] = useState<any[]>([]);
  const [recentPapers, setRecentPapers] = useState<any[]>([]);
  const [chartData, setChartData] = useState<any[]>([]);
  const [selectedSubject, setSelectedSubject] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const token = localStorage.getItem('token');
        if (!token) return;

        // Fetch Papers
        const resPapers = await fetch('http://localhost:8000/questions/papers/me', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const papersData = await resPapers.json();
        
        // Fetch Documents
        const resDocs = await fetch('http://localhost:8000/documents/user/me', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const docsData = await resDocs.json();

        setAllPapers(papersData || []);
        setAllDocs(docsData || []);
        setRecentPapers((papersData || []).slice(0, 5));

        // Group by subject for chart
        const subjectCount: Record<string, number> = {};
        papersData.forEach((p: any) => {
          const sName = p.subject?.name || 'Uncategorized';
          subjectCount[sName] = (subjectCount[sName] || 0) + 1;
        });

        const cData = Object.entries(subjectCount).map(([name, count]) => ({
          name,
          Papers: count
        }));
        setChartData(cData);
      } catch (err) {
        console.error(err);
      }
    }
    fetchData();
  }, []);

  const filteredPapers = selectedSubject 
    ? allPapers.filter(p => (p.subject?.name || 'Uncategorized') === selectedSubject)
    : allPapers;

  const filteredDocs = selectedSubject
    ? allDocs.filter(d => (d.subject?.name || 'Uncategorized') === selectedSubject)
    : allDocs;

  const currentStats = {
    papers: filteredPapers.length,
    questions: filteredPapers.reduce((acc, p) => acc + (p.questions?.length || 0), 0),
    documents: filteredDocs.length
  };

  const displayStats = [
    { label: "Total Documents", value: currentStats.documents.toString(), icon: FolderOpen },
    { label: "Papers Generated", value: currentStats.papers.toString(), icon: FileText },
    { label: "Questions Tracked", value: currentStats.questions.toString(), icon: ClipboardList },
  ];

  return (
    <div className="flex-1 animate-in fade-in slide-in-from-top-4 duration-300">
      <header className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-slate-900">Welcome back, Educator 👋</h1>
            <p className="text-sm text-slate-500 mt-1">Here's your workspace at a glance.</p>
          </div>
          <Button asChild size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm transition-all duration-200">
            <Link href="/dashboard/generate"><Sparkles className="h-4 w-4 mr-2" /> New Paper</Link>
          </Button>
        </div>
      </header>

      <div className="space-y-8">
        <div className="grid gap-4 md:grid-cols-3">
          {displayStats.map((s) => (
            <Card key={s.label} className="p-6 bg-white border border-slate-200 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 rounded-2xl">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-500">{s.label} {selectedSubject ? <span className="text-primary font-semibold">({selectedSubject})</span> : ''}</p>
                  <p className="mt-2 text-3xl font-bold text-slate-900">{s.value}</p>
                </div>
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
                  <s.icon className="h-6 w-6" />
                </div>
              </div>
            </Card>
          ))}
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {/* Interactive Chart */}
          <Card className="p-6 border border-slate-200 shadow-sm rounded-2xl bg-white">
            <h2 className="font-sans text-lg font-bold mb-4 text-slate-900 flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-primary" />
              Papers by Subject
            </h2>
            {chartData.length > 0 ? (
              <div className="h-[250px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} onClick={(data) => {
                    if (data && data.activeLabel) {
                      const label = String(data.activeLabel);
                      setSelectedSubject(selectedSubject === label ? null : label);
                    }
                  }}>
                    <XAxis dataKey="name" fontSize={12} tickLine={false} axisLine={false} tick={{fill: '#64748b'}} />
                    <YAxis fontSize={12} tickLine={false} axisLine={false} allowDecimals={false} tick={{fill: '#64748b'}} />
                    <Tooltip cursor={{fill: 'transparent'}} contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }} />
                    <Bar dataKey="Papers" radius={[4, 4, 0, 0]}>
                      {chartData.map((entry, index) => (
                        <Cell 
                          cursor="pointer"
                          fill={entry.name === selectedSubject ? 'hsl(var(--primary))' : 'hsl(var(--primary) / 0.5)'}
                          className="transition-all duration-200"
                          key={`cell-${index}`} 
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-[250px] flex flex-col items-center justify-center text-sm text-slate-500 bg-slate-50 border border-dashed border-slate-200 rounded-xl">
                <BarChart3 className="h-8 w-8 text-slate-400 mb-2" />
                No papers yet.
              </div>
            )}
            <p className="text-xs text-slate-400 mt-4 text-center">Click a bar to filter metrics.</p>
          </Card>

          {/* Quick Actions */}
          <div>
            <h2 className="font-sans text-lg font-bold mb-4 text-slate-900">Quick Actions</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              {QUICK.map((q) => (
                <Link key={q.title} href={q.to} className={q.soon ? "pointer-events-none opacity-80" : ""}>
                  <Card className="group h-full p-5 bg-white border border-slate-200 shadow-sm hover:shadow-md hover:-translate-y-0.5 hover:border-primary/30 transition-all duration-200 rounded-2xl relative">
                    {q.soon && (
                      <span className="absolute top-4 right-4 bg-slate-100 text-slate-600 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full">Soon</span>
                    )}
                    <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                      <q.icon className="h-5 w-5" />
                    </div>
                    <h3 className="font-semibold text-sm text-slate-900">{q.title}</h3>
                    <p className="mt-1 text-xs text-slate-500 line-clamp-2">{q.desc}</p>
                    <div className="mt-4 inline-flex items-center gap-1 text-xs font-semibold text-primary">
                      Open <ArrowRight className="h-3 w-3 transition-transform duration-200 group-hover:translate-x-1" />
                    </div>
                  </Card>
                </Link>
              ))}
            </div>
          </div>
        </div>

        <div>
          <h2 className="font-sans text-lg font-bold mb-4 text-slate-900 flex items-center justify-between">
            Recent Papers
            <Button variant="ghost" size="sm" asChild className="text-primary hover:text-primary/80 hover:bg-primary/5">
              <Link href="/dashboard/papers">View all <ArrowRight className="ml-1 h-4 w-4" /></Link>
            </Button>
          </h2>
          <Card className="border border-slate-200 shadow-sm bg-white rounded-2xl overflow-hidden">
            {recentPapers.length > 0 ? (
              <div className="divide-y divide-slate-100">
                {recentPapers.map((r) => (
                  <div key={r.id} className="flex items-center justify-between p-4 hover:bg-slate-50 transition-colors duration-200">
                    <div className="flex items-center gap-4">
                      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                        <FileText className="h-5 w-5" />
                      </div>
                      <div>
                        <Link href={`/dashboard/papers/${r.id}`} className="text-sm font-semibold hover:text-primary transition-colors text-slate-900">
                          {r.title || 'Untitled Paper'}
                        </Link>
                        <p className="text-xs text-slate-500 mt-0.5">{new Date(r.created_at).toLocaleDateString()} • {r.subject?.name || 'Uncategorized'}</p>
                      </div>
                    </div>
                    <Button variant="outline" size="sm" asChild className="h-8 rounded-lg border-slate-200 hover:bg-slate-50 hover:text-slate-900">
                       <Link href={`/dashboard/papers/${r.id}`}>Open</Link>
                    </Button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-12 text-center flex flex-col items-center">
                <FileText className="h-8 w-8 text-slate-300 mb-3" />
                <p className="text-sm font-medium text-slate-900">No papers generated yet</p>
                <p className="text-sm text-slate-500 mt-1">Generate your first paper to get started.</p>
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
