import { ChevronLeft } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';

interface BackButtonProps {
  label?: string;
  fallbackUrl?: string;
  className?: string;
}

export function BackButton({ label = 'Back', fallbackUrl = '/dashboard', className = '' }: BackButtonProps) {
  const router = useRouter();

  return (
    <Button 
      variant="ghost" 
      size="sm" 
      onClick={() => router.back()} 
      className={`mb-6 -ml-2 text-muted-foreground hover:text-foreground hover:bg-muted ${className}`}
    >
      <ChevronLeft className="h-4 w-4 mr-1" />
      {label}
    </Button>
  );
}
