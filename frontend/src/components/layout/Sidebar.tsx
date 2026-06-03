'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import {
  LayoutDashboard,
  FolderOpen,
  Wand2,
  MessagesSquare,
  FileQuestion,
  Settings,
  GraduationCap,
  ShieldAlert
} from "lucide-react";
import { cn } from "@/lib/utils";

export function Sidebar() {
  const pathname = usePathname();
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    const role = localStorage.getItem('userRole');
    if (role === 'admin') {
      setIsAdmin(true);
    }
  }, []);

  const links = [
    { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, exact: true },
    { href: '/dashboard/generate', label: 'Generate Paper', icon: Wand2 },
    { href: '/dashboard/papers', label: 'My Papers', icon: FileQuestion },
    { href: '/dashboard/documents', label: 'Documents', icon: FolderOpen },
    { href: '/dashboard/chat', label: 'Chat', icon: MessagesSquare },
    { href: '/settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="hidden h-screen w-64 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground transition-all duration-200 ease-out md:flex">
      <Link
        href="/dashboard"
        className="flex h-16 items-center gap-2 border-b border-sidebar-border px-6 transition-all duration-200"
      >
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-primary shadow-glow">
          <GraduationCap className="h-5 w-5 text-primary-foreground" />
        </div>
        <span className="font-display overflow-hidden whitespace-nowrap text-xl font-bold transition-all duration-200">
          Exam<span className="text-gradient">AI</span>
        </span>
      </Link>

      <nav className="flex-1 space-y-1 p-4">
        {links.map((link) => {
          const isActive = link.exact 
            ? pathname === link.href 
            : pathname.startsWith(link.href) && link.href !== '/dashboard' && link.href !== '/settings';
            
          return (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-smooth",
                isActive
                  ? "bg-sidebar-accent text-sidebar-accent-foreground shadow-sm"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent/60 hover:text-sidebar-foreground",
              )}
            >
              <link.icon className="h-4 w-4 shrink-0 transition-all duration-200" />
              <span className="overflow-hidden whitespace-nowrap transition-all duration-200">
                {link.label}
              </span>
            </Link>
          );
        })}

        {isAdmin && (
          <div className="mt-4 border-t border-sidebar-border pt-4">
            <Link
              href="/admin/dashboard"
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-smooth",
                pathname.startsWith('/admin')
                  ? "bg-sidebar-accent text-sidebar-accent-foreground shadow-sm"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent/60 hover:text-sidebar-foreground",
              )}
            >
              <ShieldAlert className="h-4 w-4 shrink-0 transition-all duration-200" />
              <span className="overflow-hidden whitespace-nowrap transition-all duration-200">
                Admin Panel
              </span>
            </Link>
          </div>
        )}
      </nav>
    </aside>
  );
}
