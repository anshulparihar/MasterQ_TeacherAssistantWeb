'use client';

import { useEffect, useState } from 'react';

export default function SettingsPage() {
  const [tokens, setTokens] = useState(0);

  useEffect(() => {
    fetch('http://localhost:8000/admin/token-usage', { // Or a specific /users/me/tokens route
      headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
    })
    .then(res => res.json())
    .then(data => {
      // Mock parsing logic based on standard response
      if(data.usage) setTokens(data.usage);
    })
    .catch(console.error);
  }, []);

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-muted-foreground mt-1">Manage your account and view API usage.</p>
      </div>

      <div className="bg-card border rounded-xl p-6 shadow-sm">
        <h2 className="font-semibold text-lg mb-4">Profile Information</h2>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-muted-foreground">Email</label>
            <div className="font-medium mt-1">user@example.com</div>
          </div>
          <div className="pt-4 border-t">
            <button className="border px-4 py-2 rounded-md text-sm font-medium hover:bg-muted transition-colors">
              Change Password
            </button>
          </div>
        </div>
      </div>

      <div className="bg-card border rounded-xl p-6 shadow-sm">
        <h2 className="font-semibold text-lg mb-4">API Usage</h2>
        <div className="space-y-4">
          <div className="bg-muted/30 p-4 rounded-lg flex items-center justify-between border">
            <div>
              <div className="font-medium">Gemini AI Tokens</div>
              <div className="text-sm text-muted-foreground mt-1">Consumed today out of 100,000 limit</div>
            </div>
            <div className="text-2xl font-bold text-primary">
              {tokens.toLocaleString()}
            </div>
          </div>
          <div className="bg-muted/30 p-4 rounded-lg flex items-center justify-between border">
            <div>
              <div className="font-medium">Plan Status</div>
              <div className="text-sm text-muted-foreground mt-1">Free Tier Active</div>
            </div>
            <div className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-bold uppercase tracking-wider">
              Active
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
