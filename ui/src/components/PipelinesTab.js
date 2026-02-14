import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Zap, ArrowDown, CheckCircle2, XCircle, Loader2,
  ChevronRight, Search
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import * as api from '@/lib/api';

const EXAMPLES = [
  "Fetch example.com, summarize it, analyze sentiment, post to Slack",
  "Fetch CNN.com news, translate to Spanish, post summary to #team",
  "Analyze the sentiment of a product review and summarize findings",
  "Fetch a blog post, summarize key points, send to #engineering",
];

export default function PipelinesTab({ onExecuted }) {
  const [request, setRequest] = useState('');
  const [url, setUrl] = useState('');
  const [channel, setChannel] = useState('#team-updates');
  const [targetLanguage, setTargetLanguage] = useState('es');
  const [plan, setPlan] = useState(null);
  const [executing, setExecuting] = useState(false);
  const [discovering, setDiscovering] = useState(false);
  const [result, setResult] = useState(null);

  const handleDiscover = async () => {
    if (!request.trim()) return;
    setDiscovering(true);
    setPlan(null);
    setResult(null);
    try {
      const res = await api.discoverPipeline({ request });
      setPlan(res.data);
    } catch (err) {
      toast.error('Failed to discover pipeline');
    } finally {
      setDiscovering(false);
    }
  };

  const handleExecute = async () => {
    if (!request.trim()) return;
    setExecuting(true);
    setResult(null);
    setPlan(null);
    try {
      const res = await api.executePipeline({ request, url, channel, source_language: 'auto', target_language: targetLanguage });
      setResult(res.data);
      toast.success('Pipeline executed successfully!');
      onExecuted?.();
    } catch (err) {
      toast.error('Pipeline execution failed');
    } finally {
      setExecuting(false);
    }
  };

  const displaySteps = result?.steps || plan?.steps || [];

  return (
    <div data-testid="pipelines-tab-content">
      <h2 className="text-lg font-semibold mb-2">Pipeline Builder</h2>
      <p className="text-xs text-white/40 mb-6">
        Describe what you want to do in natural language, and NEXUS will plan and execute the pipeline using Gemini 3 Flash.
      </p>

      {/* Input Section */}
      <div className="glass rounded-xl p-6 mb-6" data-testid="pipeline-input-section">
        <textarea
          className="w-full bg-white/5 border border-white/10 rounded-lg p-4 text-sm text-white placeholder:text-white/30 focus:border-sky-500/50 focus:ring-1 focus:ring-sky-500/20 resize-none h-24 outline-none mb-4"
          placeholder='Describe your pipeline... e.g., "Fetch example.com, summarize it, analyze sentiment, post to Slack"'
          value={request}
          onChange={e => setRequest(e.target.value)}
          data-testid="pipeline-request-input"
        />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
          <div>
            <label className="text-[10px] text-white/40 mb-1 block uppercase tracking-wider">URL (optional)</label>
            <Input placeholder="https://example.com" value={url} onChange={e => setUrl(e.target.value)} className="bg-white/5 border-white/10 text-sm" data-testid="pipeline-url-input" />
          </div>
          <div>
            <label className="text-[10px] text-white/40 mb-1 block uppercase tracking-wider">Slack Channel</label>
            <Input placeholder="#general" value={channel} onChange={e => setChannel(e.target.value)} className="bg-white/5 border-white/10 text-sm" data-testid="pipeline-channel-input" />
          </div>
          <div>
            <label className="text-[10px] text-white/40 mb-1 block uppercase tracking-wider">Target Language</label>
            <Input placeholder="es" value={targetLanguage} onChange={e => setTargetLanguage(e.target.value)} className="bg-white/5 border-white/10 text-sm" data-testid="pipeline-language-input" />
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button variant="outline" className="border-white/10" onClick={handleDiscover} disabled={discovering || !request.trim()} data-testid="discover-btn">
            {discovering ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Search className="w-4 h-4 mr-2" strokeWidth={1.5} />}
            Discover Plan
          </Button>
          <Button className="bg-sky-500 hover:bg-sky-400 text-black font-medium" onClick={handleExecute} disabled={executing || !request.trim()} data-testid="execute-btn">
            {executing ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Zap className="w-4 h-4 mr-2" strokeWidth={1.5} />}
            Execute Pipeline
          </Button>
        </div>
      </div>

      {/* Examples */}
      {!plan && !result && (
        <div className="mb-6" data-testid="pipeline-examples">
          <p className="text-[10px] text-white/30 uppercase tracking-wider mb-3">Try an example</p>
          <div className="flex flex-wrap gap-2">
            {EXAMPLES.map((ex, i) => (
              <button key={i} onClick={() => setRequest(ex)}
                className="text-xs text-white/40 bg-white/5 px-3 py-1.5 rounded-full hover:bg-white/10 hover:text-white/60 transition-colors"
                data-testid={`example-${i}`}
              >
                {ex.length > 55 ? ex.slice(0, 55) + '...' : ex}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Pipeline Visualization */}
      {displaySteps.length > 0 && (
        <div className="glass rounded-xl p-6" data-testid="pipeline-visualization">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-medium">Pipeline Steps</h3>
              <p className="text-xs text-white/30 mt-0.5">
                Confidence: {(((result?.confidence || plan?.confidence || 0)) * 100).toFixed(0)}%
                {result?.total_duration ? ` — Total: ${result.total_duration}s` : ''}
              </p>
            </div>
            {result?.success !== undefined && (
              <Badge className={result.success ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'}>
                {result.success ? 'Success' : 'Failed'}
              </Badge>
            )}
          </div>

          <div className="space-y-3">
            {displaySteps.map((step, i) => (
              <motion.div key={i} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.12 }}>
                <div className={`flex items-center gap-4 p-4 rounded-lg border ${step.success !== undefined
                  ? step.success ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-red-500/5 border-red-500/20'
                  : 'bg-white/[0.02] border-white/5'
                  }`} data-testid={`pipeline-step-${i}`}>
                  <div className="flex-shrink-0">
                    {step.success !== undefined ? (
                      step.success
                        ? <CheckCircle2 className="w-5 h-5 text-emerald-400" strokeWidth={1.5} />
                        : <XCircle className="w-5 h-5 text-red-400" strokeWidth={1.5} />
                    ) : (
                      <div className="w-5 h-5 rounded-full border border-white/20 flex items-center justify-center text-[10px] text-white/40">
                        {step.step}
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-white/80">{step.server}</span>
                      <ChevronRight className="w-3 h-3 text-white/20" strokeWidth={1.5} />
                      <code className="text-xs text-sky-400 font-mono">{step.tool}</code>
                    </div>
                    {step.reason && <p className="text-[11px] text-white/30 mt-0.5">{step.reason}</p>}
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <Badge variant="outline" className="text-[10px] border-white/10">{step.connection_type}</Badge>
                    {step.duration != null && <span className="text-xs text-white/30">{step.duration}s</span>}
                  </div>
                </div>
                {i < displaySteps.length - 1 && (
                  <div className="flex justify-center py-1">
                    <ArrowDown className="w-4 h-4 text-white/10" strokeWidth={1.5} />
                  </div>
                )}
              </motion.div>
            ))}
          </div>

          {/* Final Output */}
          {result?.final_output && (
            <div className="mt-4 pt-4 border-t border-white/5" data-testid="pipeline-output">
              <h4 className="text-xs font-medium text-white/50 mb-2">Final Output</h4>
              <pre className="text-xs font-mono text-white/40 bg-black/40 rounded-lg p-3 overflow-auto max-h-40">
                {JSON.stringify(result.final_output, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* Loading state */}
      {executing && displaySteps.length === 0 && (
        <div className="glass rounded-xl p-12 text-center" data-testid="pipeline-loading">
          <Loader2 className="w-8 h-8 text-sky-400 animate-spin mx-auto mb-3" strokeWidth={1.5} />
          <p className="text-white/40">Executing pipeline...</p>
          <p className="text-xs text-white/20 mt-1">Gemini 3 Flash is planning and executing your workflow</p>
        </div>
      )}
    </div>
  );
}
