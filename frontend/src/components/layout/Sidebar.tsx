'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useState } from 'react';
import {
  LayoutDashboard,
  FolderOpen,
  Wand2,
  MessageSquare,
  FileText,
  Settings,
  GraduationCap,
  ShieldAlert,
  ChevronLeft,
  ChevronRight,
  LogOut
} from "lucide-react";
import { cn } from "@/lib/utils";

import { useAuthStore } from '@/store/auth';
import { Button } from '@/components/ui/button';

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const user = useAuthStore(state => state.user);
  const isAdmin = user?.is_admin || false;
  const [isCollapsed, setIsCollapsed] = useState(false);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('userRole');
    router.push('/login');
  };

  const links = [
    { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, exact: true },
    { href: '/dashboard/documents', label: 'Documents', icon: FolderOpen },
    { href: '/dashboard/generate', label: 'Generate Paper', icon: Wand2 },
    { href: '/dashboard/papers', label: 'My Papers', icon: FileText },
    { href: '/dashboard/chat', label: 'AI Chatbot', icon: MessageSquare },
  ];

  return (
    <aside className={cn(
      "hidden h-screen flex-col border-r border-slate-200 bg-white transition-all duration-300 ease-in-out md:flex sticky top-0",
      isCollapsed ? "w-20" : "w-64"
    )}>
      <div className="flex h-16 items-center justify-between border-b border-slate-100 px-4 transition-all duration-300">
        <Link
          href="/dashboard"
          className={cn("flex items-center gap-2 transition-all duration-300 overflow-hidden", isCollapsed ? "w-0 opacity-0" : "w-auto opacity-100")}
        >
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm">
            <GraduationCap className="h-5 w-5" />
          </div>
          <span className="font-sans whitespace-nowrap text-lg font-bold text-slate-900 tracking-tight">
            MasterQ
          </span>
        </Link>
        {isCollapsed && (
          <Link href="/dashboard" className="mx-auto flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm">
            <GraduationCap className="h-5 w-5" />
          </Link>
        )}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="h-8 w-8 shrink-0 rounded-full hover:bg-slate-100 absolute -right-4 top-4 border bg-white shadow-sm z-10 text-slate-500 hover:text-slate-900"
        >
          {isCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </Button>
      </div>

      <nav className="flex-1 space-y-1 p-3 overflow-y-auto">
        {links.map((link) => {
          const isActive = link.exact 
            ? pathname === link.href 
            : pathname.startsWith(link.href) && link.href !== '/dashboard' && link.href !== '/settings';
            
          return (
            <Link
              key={link.href}
              href={link.href}
              title={isCollapsed ? link.label : undefined}
              className={cn(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200",
                isActive
                  ? "bg-primary text-primary-foreground shadow-sm shadow-primary/20"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
                isCollapsed ? "justify-center" : "justify-start"
              )}
            >
              <link.icon className={cn("h-5 w-5 shrink-0", isActive ? "text-primary-foreground" : "text-slate-500")} />
              {!isCollapsed && (
                <span className="overflow-hidden whitespace-nowrap">
                  {link.label}
                </span>
              )}
            </Link>
          );
        })}

        {isAdmin && (
          <div className="mt-6">
            {!isCollapsed && <div className="px-3 mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">Administration</div>}
            <Link
              href="/admin/dashboard"
              title={isCollapsed ? "Admin Panel" : undefined}
              className={cn(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200",
                pathname.startsWith('/admin')
                  ? "bg-primary text-primary-foreground shadow-sm shadow-primary/20"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
                isCollapsed ? "justify-center" : "justify-start"
              )}
            >
              <ShieldAlert className={cn("h-5 w-5 shrink-0", pathname.startsWith('/admin') ? "text-primary-foreground" : "text-slate-500")} />
              {!isCollapsed && (
                <span className="overflow-hidden whitespace-nowrap">
                  Admin Panel
                </span>
              )}
            </Link>
            <Link
              href="/admin/config"
              title={isCollapsed ? "System Config" : undefined}
              className={cn(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200 mt-1",
                pathname.startsWith('/admin/config')
                  ? "bg-primary text-primary-foreground shadow-sm shadow-primary/20"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
                isCollapsed ? "justify-center" : "justify-start"
              )}
            >
              <Settings className={cn("h-5 w-5 shrink-0", pathname.startsWith('/admin/config') ? "text-primary-foreground" : "text-slate-500")} />
              {!isCollapsed && (
                <span className="overflow-hidden whitespace-nowrap">
                  System Config
                </span>
              )}
            </Link>
            <Link
              href="/admin/usage"
              title={isCollapsed ? "Usage Logs" : undefined}
              className={cn(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200 mt-1",
                pathname.startsWith('/admin/usage')
                  ? "bg-primary text-primary-foreground shadow-sm shadow-primary/20"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
                isCollapsed ? "justify-center" : "justify-start"
              )}
            >
              <FileText className={cn("h-5 w-5 shrink-0", pathname.startsWith('/admin/usage') ? "text-primary-foreground" : "text-slate-500")} />
              {!isCollapsed && (
                <span className="overflow-hidden whitespace-nowrap">
                  Usage Logs
                </span>
              )}
            </Link>
          </div>
        )}
      </nav>

      <div className="border-t border-slate-100 p-3 space-y-1">
        <Link
          href="/settings"
          title={isCollapsed ? "Settings" : undefined}
          className={cn(
            "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200",
            pathname === '/settings'
              ? "bg-primary text-primary-foreground shadow-sm shadow-primary/20"
              : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
            isCollapsed ? "justify-center" : "justify-start"
          )}
        >
          <Settings className={cn("h-5 w-5 shrink-0", pathname === '/settings' ? "text-primary-foreground" : "text-slate-500")} />
          {!isCollapsed && (
            <span className="overflow-hidden whitespace-nowrap">
              Settings
            </span>
          )}
        </Link>
        
        <div className={cn(
          "flex items-center justify-between p-2 mt-2 rounded-xl border border-slate-100 bg-slate-50/50",
          isCollapsed ? "flex-col gap-2" : "flex-row gap-3"
        )}>
          <div className={cn("flex items-center gap-3", isCollapsed && "justify-center")}>
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary font-bold text-sm">
              {user?.email?.charAt(0).toUpperCase() || 'U'}
            </div>
            {!isCollapsed && (
              <div className="flex flex-col overflow-hidden">
                <span className="text-sm font-medium text-slate-900 truncate">{user?.email?.split('@')[0] || 'User'}</span>
                <span className="text-xs text-slate-500 truncate">{user?.email || 'user@example.com'}</span>
              </div>
            )}
          </div>
          <button
            onClick={handleLogout}
            title="Sign Out"
            className="p-2 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors shrink-0"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
