import { useState } from 'react';
import { useRouter } from 'next/navigation';

export function useQuestionGeneration() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generate = async (payload: any) => {
    setLoading(true);
    setError(null);
    
    try {
      const res = await fetch('http://localhost:8000/questions/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(payload)
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.detail || "Failed to generate question paper");
      }
      
      if (data.paper_id) {
        // Simple native toast simulation
        alert("Success! Question paper generated successfully.");
        router.push(`/dashboard/papers/${data.paper_id}`);
      }
      
      return data;
    } catch (err: any) {
      console.error(err);
      setError(err.message);
      alert(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return { generate, loading, error };
}
