'use client';

import { useState, useEffect } from 'react';

export default function Home() {
  const [backendStatus, setBackendStatus] = useState<'checking' | 'connected' | 'failed'>('checking');

  useEffect(() => {
    const checkBackendHealth = async () => {
      try {
        const response = await fetch('http://localhost:8001/health');
        if (response.ok) {
          setBackendStatus('connected');
        } else {
          setBackendStatus('failed');
        }
      } catch (error) {
        console.error('Backend health check failed:', error);
        setBackendStatus('failed');
      }
    };

    checkBackendHealth();
  }, []);

  const getStatusDisplay = () => {
    switch (backendStatus) {
      case 'checking':
        return <span className="text-yellow-400">Checking...</span>;
      case 'connected':
        return <span className="text-green-400">✓ Connected</span>;
      case 'failed':
        return <span className="text-red-400">✗ Failed</span>;
      default:
        return <span className="text-yellow-400">Unknown</span>;
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-black text-green-400 font-mono">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-8">ADVENTURE ENGINE</h1>
        <div className="max-w-2xl text-left">
          <p className="mb-4">&gt; Initializing Adventure Engine...</p>
          <p className="mb-4">&gt; Loading multi-agent system...</p>
          <p className="mb-4">&gt; Connecting to vector database...</p>
          <p className="mb-8">&gt; Ready for adventure!</p>

          <div className="border border-green-400 p-4 mb-4">
            <h2 className="text-xl mb-2">System Status</h2>
            <p>&gt; Backend API: {getStatusDisplay()}</p>
            <p>&gt; Agent Network: <span className="text-blue-400">Standby</span></p>
            <p>&gt; Memory Systems: <span className="text-green-400">Ready</span></p>
          </div>

          <div className="border border-green-400 p-4">
            <h2 className="text-xl mb-2">Available Commands</h2>
            <p>&gt; START - Begin new adventure</p>
            <p>&gt; LOAD - Continue saved game</p>
            <p>&gt; HELP - Show all commands</p>
          </div>
        </div>

        <div className="mt-8">
          <input
            type="text"
            placeholder="Enter command..."
            className="bg-black border border-green-400 text-green-400 p-2 w-96"
          />
          <button className="bg-green-400 text-black px-4 py-2 ml-2">
            Execute
          </button>
        </div>
      </div>
    </main>
  );
}
