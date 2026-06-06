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

const loginSchema = z.object({
  email: z.string().email({ message: 'Invalid email address' }),
  password: z.string().min(1, { message: 'Password is required' }),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuthStore();
  const [error, setError] = useState<string | null>(null);

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormValues) => {
    try {
      setError(null);
      const formData = new URLSearchParams();
      formData.append('username', data.email);
      formData.append('password', data.password);
      
      const response = await api.post('/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      
      const { access_token } = response.data;
      
      const userResponse = await api.get('/auth/me', {
        headers: { Authorization: `Bearer ${access_token}` }
      });
      
      login(access_token, userResponse.data);
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'An error occurred during login.');
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
              AI-Powered Curriculum & Assessment Automation
            </h2>
            <ul className="space-y-5 text-white/90">
              <li className="flex items-start gap-3">
                <CheckCircle2 className="h-6 w-6 text-indigo-300 shrink-0" />
                <span className="text-lg">Generate curriculum-grounded question papers in seconds</span>
              </li>
              <li className="flex items-start gap-3">
                <CheckCircle2 className="h-6 w-6 text-indigo-300 shrink-0" />
                <span className="text-lg">Review and swap questions with intelligent AI recommendations</span>
              </li>
              <li className="flex items-start gap-3">
                <CheckCircle2 className="h-6 w-6 text-indigo-300 shrink-0" />
                <span className="text-lg">Export print-ready papers with complete marking schemes</span>
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
            <h1 className="text-3xl font-bold tracking-tight text-slate-900">Sign In</h1>
            <p className="mt-2 text-sm text-slate-500">Welcome back! Please enter your details.</p>
          </div>
          
          <form className="space-y-5" onSubmit={handleSubmit(onSubmit)}>
            {error && (
              <div className="rounded-lg bg-red-50 p-4 text-sm text-red-600 border border-red-100 flex items-start">
                <div className="font-medium">{error}</div>
              </div>
            )}
            
            <div className="space-y-2">
              <Label htmlFor="email" className="font-medium text-slate-700">Email Address</Label>
              <Input 
                id="email" 
                type="email" 
                placeholder="teacher@school.edu" 
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

            <div className="flex items-center justify-between pt-1">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input type="checkbox" className="w-4 h-4 rounded border-slate-300 text-primary focus:ring-primary" />
                <span className="text-sm text-slate-600 font-medium">Remember me</span>
              </label>
              <Link href="#" className="text-sm font-medium text-primary hover:text-primary/80">
                Forgot Password?
              </Link>
            </div>
            
            <Button 
              type="submit" 
              className="w-full h-11 text-base font-semibold rounded-xl bg-primary hover:bg-primary/90 text-white shadow-sm" 
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Signing in...
                </>
              ) : (
                'Sign In'
              )}
            </Button>
          </form>
          
          <p className="mt-8 text-center text-sm text-slate-500">
            Don't have an account? <Link href="/register" className="font-semibold text-primary hover:underline">Sign up.</Link>
          </p>
        </Card>
      </div>
    </div>
  );
}
