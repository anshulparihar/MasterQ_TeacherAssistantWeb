'use client';

import { useRouter } from 'next/navigation';
import { LogOut, Bell } from 'lucide-react';

export function Header() {
  const router = useRouter();

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('userRole');
    router.push('/login');
  };

  return (
    <header className="flex h-16 items-center justify-between border-b border-sidebar-border bg-background px-6">
      <div className="font-display text-lg font-medium text-foreground">
        AI Question Generation Platform
      </div>
      
      <div className="flex items-center gap-4">
        <button className="rounded-full p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground">
          <Bell className="h-5 w-5" />
        </button>
        
        <div className="flex items-center gap-3 border-l border-border pl-4">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-primary text-sm font-semibold text-primary-foreground shadow-sm">
            T
          </div>
          <div className="hidden flex-col md:flex">
            <span className="text-sm font-medium leading-none">Teacher</span>
            <span className="text-xs text-muted-foreground mt-1">MasterQ Institute</span>
          </div>
          <button 
            onClick={handleLogout}
            className="ml-2 rounded-full p-2 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
            aria-label="Logout"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
