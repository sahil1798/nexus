import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Network, ArrowLeft, Copy } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';

const ENDPOINTS = [
  { method: 'GET', path: '/api/', desc: 'Health check — verify NEXUS API is running', response: '{"message": "NEXUS API", "status": "healthy", "version": "1.0.0"}' },
  { method: 'GET', path: '/api/status', desc: 'System statistics — servers, edges, pipeline runs', response: '{"servers": 5, "edges": 14, "pipeline_runs": 3, "status": "healthy"}' },
  { method: 'GET', path: '/api/servers', desc: 'List all registered MCP servers with semantic profiles', response: '{"total": 5, "servers": [{"name": "web-fetcher", "status": "profiled", ...}]}' },
  { method: 'POST', path: '/api/servers/register', desc: 'Register a new MCP server', body: '{"name": "my-server", "command": "python", "args": ["server.py"]}', response: '{"id": "uuid", "name": "my-server", "status": "registered", ...}' },
  { method: 'DELETE', path: '/api/servers/{name}', desc: 'Unregister a server and remove its graph edges', response: '{"message": "Server removed", "success": true}' },
  { method: 'GET', path: '/api/graph', desc: 'Get all edges in the capability graph', response: '{"total_edges": 14, "edges": [{"source": "web-fetcher.fetch_url", ...}]}' },
  { method: 'POST', path: '/api/graph/rebuild', desc: 'Rebuild the capability graph from scratch', response: '{"message": "Graph rebuilt successfully", "total_edges": 14}' },
  { method: 'POST', path: '/api/discover', desc: 'Plan a pipeline from natural language (AI-powered, no execution)', body: '{"request": "Fetch example.com and summarize it"}', response: '{"request": "...", "confidence": 0.85, "steps": [...]}' },
  { method: 'POST', path: '/api/execute', desc: 'Discover AND execute a pipeline end-to-end', body: '{"request": "...", "url": "https://...", "channel": "#team"}', response: '{"success": true, "total_duration": 6.96, "steps": [...], "final_output": {...}}' },
  { method: 'GET', path: '/api/history', desc: 'Get pipeline execution history (newest first)', response: '{"total": 10, "runs": [...]}' },
];

const METHOD_COLORS = {
  GET: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  POST: 'bg-sky-500/10 text-sky-400 border-sky-500/20',
  DELETE: 'bg-red-500/10 text-red-400 border-red-500/20',
};

export default function DocsPage() {
  const copyText = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  return (
    <div className="min-h-screen bg-[#050505]" data-testid="docs-page">
      <nav className="border-b border-white/5 sticky top-0 bg-[#050505]/80 backdrop-blur-xl z-50">
        <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-sky-400 to-indigo-500 flex items-center justify-center">
                <Network className="w-3.5 h-3.5 text-white" strokeWidth={1.5} />
              </div>
              <span className="font-bold">NEXUS</span>
            </Link>
            <span className="text-white/20">/</span>
            <span className="text-sm text-white/50">API Reference</span>
          </div>
          <Button variant="outline" size="sm" className="border-white/10" asChild>
            <Link to="/dashboard"><ArrowLeft className="w-3 h-3 mr-2" strokeWidth={1.5} /> Dashboard</Link>
          </Button>
        </div>
      </nav>

      <div className="max-w-5xl mx-auto px-6 py-12">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-3xl font-bold mb-2" data-testid="docs-title">API Reference</h1>
          <p className="text-white/40 mb-8 text-base">Complete reference for the NEXUS REST API. All endpoints return JSON.</p>

          <div className="glass rounded-xl p-4 mb-8" data-testid="docs-base-url">
            <div className="text-xs text-white/40 mb-1">Base URL</div>
            <code className="text-sm text-sky-400 font-mono">{process.env.REACT_APP_BACKEND_URL}/api</code>
          </div>

          <div className="space-y-4">
            {ENDPOINTS.map((ep, i) => (
              <div key={i} className="glass rounded-xl p-5" data-testid={`api-endpoint-${i}`}>
                <div className="flex items-center gap-3 mb-2">
                  <Badge className={`${METHOD_COLORS[ep.method]} font-mono text-xs`}>{ep.method}</Badge>
                  <code className="text-sm font-mono text-white/80">{ep.path}</code>
                </div>
                <p className="text-sm text-white/40 mb-3">{ep.desc}</p>

                {ep.body && (
                  <div className="mb-3">
                    <div className="text-[10px] text-white/30 uppercase tracking-wider mb-1">Request Body</div>
                    <div className="relative group">
                      <pre className="text-xs font-mono text-white/40 bg-black/40 rounded-lg p-3 overflow-auto">{ep.body}</pre>
                      <button onClick={() => copyText(ep.body)} className="absolute top-2 right-2 text-white/20 hover:text-white/50 opacity-0 group-hover:opacity-100 transition-opacity">
                        <Copy className="w-3.5 h-3.5" strokeWidth={1.5} />
                      </button>
                    </div>
                  </div>
                )}

                <div>
                  <div className="text-[10px] text-white/30 uppercase tracking-wider mb-1">Response</div>
                  <div className="relative group">
                    <pre className="text-xs font-mono text-emerald-400/60 bg-black/40 rounded-lg p-3 overflow-auto">{ep.response}</pre>
                    <button onClick={() => copyText(ep.response)} className="absolute top-2 right-2 text-white/20 hover:text-white/50 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Copy className="w-3.5 h-3.5" strokeWidth={1.5} />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
