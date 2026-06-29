'use client';

import { useState, useEffect } from 'react';
import { useAuthStore } from '@/store/auth';
import { Button } from '@/components/ui/button';
import toast from 'react-hot-toast';
import { Loader2, Save } from 'lucide-react';

interface SystemConfig {
  key: string;
  value: any;
  description: string | null;
}

export default function ConfigPage() {
  const token = useAuthStore(state => state.token);
  const [configs, setConfigs] = useState<SystemConfig[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Local states for specific keys we want to manage easily
  const [dedupThreshold, setDedupThreshold] = useState(0.9);
  const [maintenanceMode, setMaintenanceMode] = useState(false);
  const [systemPrompt, setSystemPrompt] = useState("");

  const loadConfigs = async () => {
    try {
      const res = await fetch('http://localhost:8000/admin/config', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setConfigs(data);
        
        const dedup = data.find((c: any) => c.key === 'dedup_threshold');
        if (dedup) setDedupThreshold(dedup.value.threshold || 0.9);
        
        const maint = data.find((c: any) => c.key === 'maintenance_mode');
        if (maint) setMaintenanceMode(maint.value.enabled || false);
        
        const prompt = data.find((c: any) => c.key === 'qgen_system_prompt');
        if (prompt) setSystemPrompt(prompt.value.prompt || "");
      }
    } catch (e) {
      toast.error('Failed to load configs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) loadConfigs();
  }, [token]);

  const handleSave = async (key: string, value: any, description: string) => {
    try {
      const res = await fetch('http://localhost:8000/admin/config', {
        method: 'PUT',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ key, value, description })
      });
      if (res.ok) {
        toast.success(`${key} saved!`);
        loadConfigs();
      } else {
        toast.error('Failed to save');
      }
    } catch (e) {
      toast.error('Failed to save');
    }
  };

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin w-8 h-8 text-primary"/></div>;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">System Configuration</h1>
        <p className="text-slate-500">Manage global settings, AI prompts, and feature flags.</p>
      </div>

      <div className="grid gap-6">
        {/* Maintenance Mode */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <h2 className="text-lg font-semibold">Maintenance Mode</h2>
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-600">Toggle site-wide maintenance screen for non-admin users.</span>
            <div className="flex items-center gap-4">
              <input 
                type="checkbox" 
                checked={maintenanceMode}
                onChange={e => setMaintenanceMode(e.target.checked)}
                className="w-5 h-5 rounded text-primary"
              />
              <Button onClick={() => handleSave('maintenance_mode', { enabled: maintenanceMode }, 'Site maintenance flag')}>
                <Save className="w-4 h-4 mr-2" /> Save
              </Button>
            </div>
          </div>
        </div>

        {/* Deduplication Threshold */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <h2 className="text-lg font-semibold">Question Deduplication Threshold</h2>
          <div className="flex items-center gap-4">
            <input 
              type="range" min="0.5" max="1.0" step="0.01" 
              value={dedupThreshold}
              onChange={e => setDedupThreshold(parseFloat(e.target.value))}
              className="w-full max-w-xs"
            />
            <span className="font-mono text-sm bg-slate-100 px-2 py-1 rounded">{dedupThreshold.toFixed(2)}</span>
          </div>
          <p className="text-xs text-slate-500">Higher values mean questions must be extremely similar to be flagged as duplicates (0.9 recommended).</p>
          <Button onClick={() => handleSave('dedup_threshold', { threshold: dedupThreshold }, 'Semantic similarity threshold')}>
            <Save className="w-4 h-4 mr-2" /> Save Threshold
          </Button>
        </div>

        {/* System Prompt */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <h2 className="text-lg font-semibold">QGen Global System Prompt</h2>
          <p className="text-sm text-slate-600">This prompt is prepended to all Question Generation LLM calls.</p>
          <textarea
            value={systemPrompt}
            onChange={e => setSystemPrompt(e.target.value)}
            className="w-full h-48 p-3 border border-slate-200 rounded-lg text-sm font-mono focus:ring-2 focus:ring-primary outline-none"
            placeholder="You are an expert teacher..."
          />
          <Button onClick={() => handleSave('qgen_system_prompt', { prompt: systemPrompt }, 'Global prompt for question generation')}>
            <Save className="w-4 h-4 mr-2" /> Save Prompt
          </Button>
        </div>
      </div>
    </div>
  );
}
