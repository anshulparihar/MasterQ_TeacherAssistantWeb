'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { useAuthStore } from '@/store/auth';
import Link from 'next/link';
import { GraduationCap, Loader2, CheckCircle2 } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';

const registerSchema = z.object({
  full_name: z.string().min(2, { message: 'Full name must be at least 2 characters' }),
  email: z.string().email({ message: 'Invalid email address' }),
  password: z.string().min(8, { message: 'Password must be at least 8 characters' }),
});

type RegisterFormValues = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const router = useRouter();
  const { login } = useAuthStore();
  const [error, setError] = useState<string | null>(null);

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterFormValues) => {
    try {
      setError(null);
      // 1. Register User
      const registerRes = await api.post('/auth/register', data);
      const { access_token } = registerRes.data;
      
      // 2. Fetch User Profile
      const userRes = await api.get('/auth/me', {
        headers: { Authorization: `Bearer ${access_token}` }
      });
      
      // 3. Login and redirect
      login(access_token, userRes.data);
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'An error occurred during registration.');
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-50">
      {/* Left Panel */}
      <aside className="relative hidden w-1/2 flex-col justify-between overflow-hidden bg-primary p-12 text-primary-foreground lg:flex">
        <div className="absolute inset-0 bg-gradient-to-br from-primary via-primary to-indigo-900 opacity-90" aria-hidden />
        <div className="relative flex flex-col h-full z-10">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/20 backdrop-blur-sm shadow-sm">
              <GraduationCap className="h-6 w-6 text-white" />
            </div>
            <span className="font-sans text-2xl font-bold tracking-tight text-white">MasterQ</span>
          </Link>
          
          <div className="mt-auto mb-auto">
            <h2 className="text-4xl font-bold leading-tight tracking-tight text-white mb-6">
              Create your assessment workspace.
            </h2>
            <ul className="space-y-5 text-white/90">
              <li className="flex items-start gap-3">
                <CheckCircle2 className="h-6 w-6 text-indigo-300 shrink-0" />
                <span className="text-lg">Join forward-thinking institutes and start automating</span>
              </li>
              <li className="flex items-start gap-3">
                <CheckCircle2 className="h-6 w-6 text-indigo-300 shrink-0" />
                <span className="text-lg">Generate exam-ready question papers instantly</span>
              </li>
              <li className="flex items-start gap-3">
                <CheckCircle2 className="h-6 w-6 text-indigo-300 shrink-0" />
                <span className="text-lg">Grounded entirely in your own curriculum</span>
              </li>
            </ul>
          </div>

          <p className="text-sm text-indigo-200">© {new Date().getFullYear()} MasterQ Educational Systems</p>
        </div>
      </aside>

      {/* Right Panel */}
      <div className="flex w-full items-center justify-center p-6 lg:w-1/2">
        <Card className="w-full max-w-md border border-slate-200 p-8 shadow-sm rounded-2xl bg-white">
          <div className="mb-8">
            <h1 className="text-3xl font-bold tracking-tight text-slate-900">Create an account</h1>
            <p className="mt-2 text-sm text-slate-500">Enter your details to get started.</p>
          </div>
          
          <form className="space-y-5" onSubmit={handleSubmit(onSubmit)}>
            {error && (
              <div className="rounded-lg bg-red-50 p-4 text-sm text-red-600 border border-red-100 flex items-start">
                <div className="font-medium">{error}</div>
              </div>
            )}
            
            <div className="space-y-2">
              <Label htmlFor="full_name" className="font-medium text-slate-700">Full Name</Label>
              <Input 
                id="full_name" 
                type="text" 
                placeholder="Dr. John Doe" 
                className="h-11 rounded-xl"
                {...register('full_name')}
              />
              {errors.full_name && <p className="text-sm text-red-500 font-medium">{errors.full_name.message}</p>}
            </div>

            <div className="space-y-2">
              <Label htmlFor="email" className="font-medium text-slate-700">Work email</Label>
              <Input 
                id="email" 
                type="email" 
                placeholder="you@institute.edu" 
                className="h-11 rounded-xl"
                {...register('email')}
              />
              {errors.email && <p className="text-sm text-red-500 font-medium">{errors.email.message}</p>}
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="password" className="font-medium text-slate-700">Password</Label>
              <Input 
                id="password" 
                type="password" 
                placeholder="••••••••" 
                className="h-11 rounded-xl"
                {...register('password')}
              />
              {errors.password && <p className="text-sm text-red-500 font-medium">{errors.password.message}</p>}
            </div>

            <Button 
              type="submit" 
              className="w-full h-11 text-base font-semibold rounded-xl bg-primary hover:bg-primary/90 text-white shadow-sm" 
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Registering...
                </>
              ) : (
                'Register'
              )}
            </Button>
          </form>
          
          <p className="mt-8 text-center text-sm text-slate-500">
            Already have an account? <Link href="/login" className="font-semibold text-primary hover:underline">Sign in</Link>
          </p>
        </Card>
      </div>
    </div>
  );
}
