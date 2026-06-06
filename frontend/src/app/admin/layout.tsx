'use client';

import { ReactNode, useEffect } from 'react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useAuthStore } from '@/store/auth';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';

export default function Layout({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;
    if (!user || !user.is_admin) {
      toast.error('Unauthorized access');
      router.push('/dashboard');
    }
  }, [user, isLoading, router]);

  if (isLoading || !user || !user.is_admin) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-slate-50">
        <Loader2 className="animate-spin h-8 w-8 text-primary" />
      </div>
    );
  }

  return <DashboardLayout>{children}</DashboardLayout>;
}
