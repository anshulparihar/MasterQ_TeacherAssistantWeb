import Link from 'next/link';
import Image from 'next/image';
import { ArrowRight, FileText, Sparkles, MessageSquareText, FileCheck2, ShieldCheck, Wand2, Upload, Layers, BarChart3 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { SiteHeader } from '@/components/site/SiteHeader';
import { SiteFooter } from '@/components/site/SiteFooter';

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />
      <main className="flex-1">
        <Hero />
        <LogoStrip />
        <Features />
        <Workflow />
        <CTA />
      </main>
      <SiteFooter />
    </div>
  );
}

function Hero() {
  return (
    <section className="relative overflow-hidden bg-background">
      <div className="absolute inset-0 bg-grid-primary/5 [mask-image:linear-gradient(0deg,white,rgba(255,255,255,0.6))] dark:bg-grid-primary/10" aria-hidden />
      <div className="mx-auto grid max-w-7xl gap-12 px-6 py-20 md:grid-cols-2 md:py-28">
        <div className="flex flex-col justify-center">
          <div className="inline-flex w-fit items-center gap-1.5 rounded-full border border-accent/30 bg-accent/10 px-2.5 py-0.5 text-xs font-semibold text-accent-foreground transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2">
            <Sparkles className="h-3 w-3" /> Built for academic institutes
          </div>
          <h1 className="mt-5 text-4xl font-bold leading-[1.05] md:text-6xl text-foreground">
            Generate exam papers from <span className="text-primary">your own curriculum</span>.
          </h1>
          <p className="mt-5 max-w-xl text-lg text-muted-foreground">
            Upload syllabi, textbooks, and past papers. MasterQ crafts question papers that stay strictly within your material — and grades student answers automatically.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button asChild size="lg" className="bg-primary hover:bg-primary/90 shadow-sm transition-smooth">
              <Link href="/register">Start free trial <ArrowRight className="h-4 w-4 ml-2" /></Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <Link href="/features">Explore features</Link>
            </Button>
          </div>
          <div className="mt-8 flex items-center gap-6 text-sm text-muted-foreground">
            <div className="flex items-center gap-2"><ShieldCheck className="h-4 w-4 text-accent" /> No data leakage</div>
            <div className="flex items-center gap-2"><FileCheck2 className="h-4 w-4 text-accent" /> Source-grounded</div>
          </div>
        </div>
        <div className="relative">
          <div className="absolute -inset-4 rounded-3xl bg-primary/5 opacity-50 blur-2xl" aria-hidden />
          <Image
            src="/assets/hero.jpg"
            alt="AI knowledge graph connecting uploaded documents to generated questions"
            width={1536}
            height={1024}
            className="relative w-full rounded-2xl border border-border/60 shadow-elegant"
            priority
          />
        </div>
      </div>
    </section>
  );
}

function LogoStrip() {
  const logos = ["Cambridge Tech", "Riverdale University", "Northpoint Institute", "Oakridge Academy", "Beacon College"];
  return (
    <section className="border-y border-border/60 bg-muted/30 py-10">
      <div className="mx-auto max-w-7xl px-6">
        <p className="text-center text-xs font-medium uppercase tracking-widest text-muted-foreground">
          Trusted by forward-thinking institutes
        </p>
        <div className="mt-6 flex flex-wrap items-center justify-center gap-x-12 gap-y-4 opacity-70">
          {logos.map((l) => (
            <span key={l} className="font-display text-sm font-semibold tracking-tight text-muted-foreground">{l}</span>
          ))}
        </div>
      </div>
    </section>
  );
}

const FEATURES = [
  { icon: Upload, title: "Smart document ingestion", desc: "PDF, DOCX, TXT, and Markdown. Organize by subject, topic, and exam type." },
  { icon: Wand2, title: "Custom paper generation", desc: "Pick MCQ vs theory counts, easy/medium/hard split, topics, and exam style." },
  { icon: ShieldCheck, title: "Source-grounded", desc: "Questions never venture outside the documents you uploaded." },
  { icon: MessageSquareText, title: "Document chatbot", desc: "Chat with selected documents — or all of them — to clarify and explore." },
  { icon: BarChart3, title: "Auto answer scoring", desc: "Upload student answers and get instant scores with rationale." },
  { icon: FileText, title: "Export anywhere", desc: "Download papers as polished PDF or DOCX, ready to print." },
];

function Features() {
  return (
    <section className="py-24">
      <div className="mx-auto max-w-7xl px-6">
        <div className="mx-auto max-w-2xl text-center">
          <div className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80">Platform</div>
          <h2 className="mt-4 text-3xl font-bold md:text-4xl">Everything an exam cell needs</h2>
          <p className="mt-3 text-muted-foreground">From ingestion to grading — one workspace for the entire assessment lifecycle.</p>
        </div>
        <div className="mt-14 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f) => (
            <Card key={f.title} className="interactive-card p-6 bg-card">
              <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <f.icon className="h-5 w-5" />
              </div>
              <h3 className="font-display text-lg font-semibold">{f.title}</h3>
              <p className="mt-2 text-sm text-muted-foreground">{f.desc}</p>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}

const STEPS = [
  { n: "01", title: "Upload your library", desc: "Drag in syllabus PDFs, textbooks, and past papers. MasterQ indexes everything." },
  { n: "02", title: "Configure the paper", desc: "Choose subject, topics, exam type, MCQ vs theory ratio, and difficulty split." },
  { n: "03", title: "Generate & export", desc: "Review, regenerate sections, then export to PDF or DOCX in one click." },
];

function Workflow() {
  return (
    <section className="border-t border-border/60 bg-muted/30 py-24">
      <div className="mx-auto max-w-7xl px-6">
        <div className="mx-auto max-w-2xl text-center">
          <div className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80">Workflow</div>
          <h2 className="mt-4 text-3xl font-bold md:text-4xl">Three steps to a ready paper</h2>
        </div>
        <div className="mt-14 grid gap-6 md:grid-cols-3">
          {STEPS.map((s) => (
            <Card key={s.n} className="interactive-card p-7 bg-card">
              <div className="font-sans text-5xl font-bold text-primary/80">{s.n}</div>
              <h3 className="mt-4 font-display text-lg font-semibold">{s.title}</h3>
              <p className="mt-2 text-sm text-muted-foreground">{s.desc}</p>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}

function CTA() {
  return (
    <section className="py-24">
      <div className="mx-auto max-w-5xl px-6">
        <div className="relative overflow-hidden rounded-[2rem] bg-primary p-12 text-center shadow-lg md:p-16">
          <div className="absolute inset-0 bg-primary/90 opacity-80" aria-hidden />
          <div className="relative">
            <Layers className="mx-auto h-10 w-10 text-primary-foreground/90" />
            <h2 className="mt-4 font-display text-3xl font-bold text-primary-foreground md:text-4xl">
              Ready to redesign your exam workflow?
            </h2>
            <p className="mx-auto mt-3 max-w-xl text-primary-foreground/80">
              Join institutes saving hours every week. Free for the first 30 days.
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-3">
              <Button asChild size="lg" className="bg-white text-primary hover:bg-white/90 shadow-sm">
                <Link href="/register">Create your workspace</Link>
              </Button>
              <Button asChild variant="outline" size="lg" className="border-white/30 bg-white/10 text-primary-foreground hover:bg-white/20 hover:text-primary-foreground">
                <Link href="/contact">Talk to sales</Link>
              </Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
