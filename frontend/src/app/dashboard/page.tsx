'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileText, Wand2, MessagesSquare, ClipboardCheck, ArrowRight, FolderOpen, Sparkles } from 'lucide-react';

const QUICK = [
  { to: "/dashboard/documents", title: "Upload documents", desc: "Add syllabi, textbooks and past papers.", icon: FolderOpen },
  { to: "/dashboard/generate", title: "Generate a paper", desc: "Configure topics, MCQ/theory mix and difficulty.", icon: Wand2 },
  { to: "/dashboard/chat", title: "Ask the chatbot", desc: "Query your library or specific documents.", icon: MessagesSquare },
  { to: "/dashboard/score", title: "Score answers", desc: "Upload student answers for instant scoring.", icon: ClipboardCheck },
];

const RECENT = [
  { name: "Mid-term Physics — Class XII", type: "Paper", date: "Today, 10:42 AM" },
  { name: "Organic Chemistry chatbot session", type: "Chat", date: "Yesterday" },
  { name: "Mathematics unit test scoring", type: "Score", date: "2 days ago" },
];

export default function DashboardHomePage() {
  const [stats, setStats] = useState({ papers: 0, questions: 0, documents: 0 });
  const [recentPapers, setRecentPapers] = useState<any[]>([]);

  useEffect(() => {
    // Mocking an aggregation endpoint since we didn't build a user-specific stats API in the backend yet.
    setStats({ papers: 128, questions: 1204, documents: 42 });
    
    // Attempt to fetch real papers if available
    fetch('http://localhost:8000/questions/papers/me', {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
    })
    .then(res => res.json())
    .then(data => {
      setRecentPapers((data || []).slice(0, 5));
    })
    .catch(console.error);
  }, []);

  const STATS = [
    { label: "Documents", value: stats.documents.toString(), icon: FolderOpen },
    { label: "Papers generated", value: stats.papers.toString(), icon: FileText },
    { label: "Answers scored", value: stats.questions.toString(), icon: ClipboardCheck },
    { label: "Chat sessions", value: "87", icon: MessagesSquare },
  ];

  return (
    <div className="flex-1">
      <header className="border-b border-border/60 bg-background px-8 py-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-display text-2xl font-bold">Welcome back, Teacher</h1>
            <p className="text-sm text-muted-foreground">Here's what's happening in your workspace.</p>
          </div>
          <Button asChild variant="hero">
            <Link href="/dashboard/generate"><Sparkles className="h-4 w-4" /> New paper</Link>
          </Button>
        </div>
      </header>

      <div className="space-y-8 p-8">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {STATS.map((s) => (
            <Card key={s.label} className="border-border/60 p-5 shadow-card">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">{s.label}</p>
                  <p className="mt-2 font-display text-3xl font-bold">{s.value}</p>
                </div>
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent/10 text-accent">
                  <s.icon className="h-5 w-5" />
                </div>
              </div>
            </Card>
          ))}
        </div>

        <div>
          <h2 className="font-display text-lg font-semibold">Quick actions</h2>
          <div className="mt-4 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {QUICK.map((q) => (
              <Link key={q.to} href={q.to}>
                <Card className="group h-full border-border/60 p-5 shadow-card transition-smooth hover:-translate-y-1 hover:shadow-elegant">
                  <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-primary text-primary-foreground shadow-glow">
                    <q.icon className="h-5 w-5" />
                  </div>
                  <h3 className="font-semibold">{q.title}</h3>
                  <p className="mt-1 text-sm text-muted-foreground">{q.desc}</p>
                  <div className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-accent">
                    Open <ArrowRight className="h-3.5 w-3.5 transition-smooth group-hover:translate-x-1" />
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        </div>

        <div>
          <h2 className="font-display text-lg font-semibold">Recent activity</h2>
          <Card className="mt-4 divide-y divide-border/60 border-border/60 shadow-card">
            {RECENT.map((r) => (
              <div key={r.name} className="flex items-center justify-between p-5">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-muted">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">{r.name}</p>
                    <p className="text-xs text-muted-foreground">{r.date}</p>
                  </div>
                </div>
                <div className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80">
                  {r.type}
                </div>
              </div>
            ))}
          </Card>
        </div>
      </div>
    </div>
  );
}
