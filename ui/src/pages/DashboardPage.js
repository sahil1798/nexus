import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Home, Server, GitBranch, Rocket, Clock, Plus,
  Network, Activity, Zap, Trash2, RefreshCw
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
  DialogDescription, DialogFooter
} from '@/components/ui/dialog';
import { toast } from 'sonner';
import Graph3D from '@/components/Graph3D';
import PipelinesTab from '@/components/PipelinesTab';
import * as api from '@/lib/api';

const TABS = [
  { id: 'overview', label: 'Overview', icon: Home },
  { id: 'servers', label: 'Servers', icon: Server },
  { id: 'graph', label: 'Graph', icon: GitBranch },
  { id: 'pipelines', label: 'Pipelines', icon: Rocket },
  { id: 'history', label: 'History', icon: Clock },
];

const DOMAIN_COLORS = {
  'NLP': { bg: 'bg-purple-500/10', text: 'text-purple-400', border: 'border-purple-500/20' },
  'Web & Information Retrieval': { bg: 'bg-sky-500/10', text: 'text-sky-400', border: 'border-sky-500/20' },
  'Communication': { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20' },
  'Custom': { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/20' },
};

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState('overview');
  const [status, setStatus] = useState(null);
  const [servers, setServers] = useState([]);
  const [history, setHistory] = useState([]);
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [registerOpen, setRegisterOpen] = useState(false);
  const [newServer, setNewServer] = useState({ name: '', command: 'python', args: '' });
  const [quickInput, setQuickInput] = useState('');

  const fetchData = useCallback(async () => {
    try {
      const [statusRes, serversRes, graphRes, historyRes] = await Promise.all([
        api.getStatus(), api.getServers(), api.getGraph(), api.getHistory(),
      ]);
      setStatus(statusRes.data);
      setServers(serversRes.data.servers || []);
      setGraphData(graphRes.data);
      setHistory(historyRes.data.runs || []);
    } catch (err) {
      console.error('Failed to fetch data', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleRegister = async () => {
    try {
      await api.registerServer({
        name: newServer.name,
        command: newServer.command,
        args: newServer.args ? newServer.args.split(',').map(a => a.trim()) : [],
      });
      toast.success(`Server "${newServer.name}" registered`);
      setRegisterOpen(false);
      setNewServer({ name: '', command: 'python', args: '' });
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to register');
    }
  };

  const handleDelete = async (name) => {
    try {
      await api.deleteServer(name);
      toast.success(`Server "${name}" removed`);
      fetchData();
    } catch (err) {
      toast.error('Failed to delete server');
    }
  };

  const handleRebuildGraph = async () => {
    try {
      await api.rebuildGraph();
      toast.success('Graph rebuilt');
      fetchData();
    } catch (err) {
      toast.error('Failed to rebuild graph');
    }
  };

  const statCards = [
    { label: 'Active Servers', value: status?.servers ?? '-', icon: Server, color: 'text-sky-400' },
    { label: 'Graph Edges', value: status?.edges ?? '-', icon: GitBranch, color: 'text-purple-400' },
    { label: 'Pipeline Runs', value: status?.pipeline_runs ?? '-', icon: Zap, color: 'text-emerald-400' },
    { label: 'Avg Confidence', value: '0.85', icon: Activity, color: 'text-amber-400' },
  ];

  return (
    <div className="min-h-screen bg-[#050505] flex" data-testid="dashboard-page">
      {/* Sidebar */}
      <aside className="w-60 border-r border-white/5 flex flex-col fixed h-screen z-20 bg-[#050505]" data-testid="sidebar">
        <div className="p-4 border-b border-white/5">
          <Link to="/" className="flex items-center gap-2" data-testid="sidebar-logo">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-sky-400 to-indigo-500 flex items-center justify-center">
              <Network className="w-4 h-4 text-white" strokeWidth={1.5} />
            </div>
            <span className="text-base font-bold">NEXUS</span>
          </Link>
        </div>

        <nav className="flex-1 p-3 space-y-1" data-testid="sidebar-nav">
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`sidebar-link w-full ${activeTab === tab.id ? 'active' : ''}`}
              data-testid={`sidebar-${tab.id}`}
            >
              <tab.icon className="w-4 h-4" strokeWidth={1.5} />
              {tab.label}
            </button>
          ))}
        </nav>

        <div className="p-3 border-t border-white/5">
          <div className="glass rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs text-white/50">System Online</span>
            </div>
            {status && (
              <div className="text-xs text-white/30 space-y-0.5">
                <div>{status.servers} servers</div>
                <div>{status.edges} edges</div>
                <div>{status.pipeline_runs} runs</div>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-60 min-h-screen">
        <header className="h-14 border-b border-white/5 flex items-center justify-between px-6 sticky top-0 bg-[#050505]/80 backdrop-blur-xl z-10" data-testid="dashboard-topbar">
          <div className="flex items-center gap-4">
            <h1 className="text-sm font-medium text-white/70 capitalize">{activeTab}</h1>
            {status && (
              <div className="flex items-center gap-3 text-xs text-white/30">
                <span>{status.servers} servers</span>
                <span className="text-white/10">|</span>
                <span>{status.edges} edges</span>
                <span className="text-white/10">|</span>
                <span>{status.pipeline_runs} runs</span>
              </div>
            )}
          </div>
          <kbd className="text-xs text-white/20 bg-white/5 px-2 py-1 rounded border border-white/10">Ctrl+K</kbd>
        </header>

        <div className="p-6">
          <AnimatePresence mode="wait">
            {/* OVERVIEW */}
            {activeTab === 'overview' && (
              <motion.div key="overview" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} data-testid="overview-tab">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                  {statCards.map((card, i) => (
                    <div key={card.label} className="glass rounded-xl p-4" data-testid={`overview-stat-${i}`}>
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-xs text-white/40">{card.label}</span>
                        <card.icon className={`w-4 h-4 ${card.color}`} strokeWidth={1.5} />
                      </div>
                      <div className="text-2xl font-bold">{card.value}</div>
                    </div>
                  ))}
                </div>

                <div className="glass rounded-xl p-6 mb-8" data-testid="quick-execute">
                  <h3 className="text-sm font-medium mb-4">Quick Execute</h3>
                  <div className="flex gap-3">
                    <Input
                      placeholder="Fetch news, summarize, analyze sentiment..."
                      value={quickInput}
                      onChange={e => setQuickInput(e.target.value)}
                      className="bg-white/5 border-white/10 flex-1"
                      data-testid="quick-execute-input"
                    />
                    <Button className="bg-sky-500 hover:bg-sky-400 text-black rounded-lg px-6" onClick={() => setActiveTab('pipelines')} data-testid="quick-execute-btn">
                      <Zap className="w-4 h-4 mr-2" strokeWidth={1.5} /> Run
                    </Button>
                  </div>
                </div>

                <div className="glass rounded-xl p-6" data-testid="recent-pipelines">
                  <h3 className="text-sm font-medium mb-4">Recent Pipeline Runs</h3>
                  {history.length === 0 ? (
                    <p className="text-sm text-white/30">No pipeline runs yet. Try executing one!</p>
                  ) : (
                    <div className="space-y-3">
                      {history.slice(0, 5).map((run, i) => (
                        <div key={run.id || i} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
                          <div className="flex items-center gap-3">
                            <div className={`w-2 h-2 rounded-full ${run.success ? 'bg-emerald-400' : 'bg-red-400'}`} />
                            <span className="text-sm text-white/70 truncate max-w-md">{run.request}</span>
                          </div>
                          <div className="flex items-center gap-4 text-xs text-white/30">
                            <span>{run.steps?.length || 0} steps</span>
                            <span>{run.total_duration}s</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </motion.div>
            )}

            {/* SERVERS */}
            {activeTab === 'servers' && (
              <motion.div key="servers" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} data-testid="servers-tab">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-lg font-semibold">Registered Servers</h2>
                  <Button className="bg-sky-500 hover:bg-sky-400 text-black rounded-lg" onClick={() => setRegisterOpen(true)} data-testid="register-server-btn">
                    <Plus className="w-4 h-4 mr-2" strokeWidth={1.5} /> Register Server
                  </Button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {servers.map((server, i) => {
                    const dc = DOMAIN_COLORS[server.domain] || DOMAIN_COLORS['Custom'];
                    return (
                      <motion.div key={server.name} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
                        className="glass rounded-xl p-5 hover:border-white/15 transition-all group" data-testid={`server-card-${server.name}`}
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div>
                            <h3 className="font-medium text-white/90">{server.name}</h3>
                            <Badge className={`${dc.bg} ${dc.text} ${dc.border} text-xs mt-1`}>{server.domain}</Badge>
                          </div>
                          <div className="flex items-center gap-1">
                            <div className={`w-2 h-2 rounded-full ${server.status === 'profiled' ? 'bg-emerald-400' : 'bg-amber-400'}`} />
                            <span className="text-xs text-white/30">{server.status}</span>
                          </div>
                        </div>
                        <p className="text-xs text-white/40 mb-3 leading-relaxed">{server.summary}</p>
                        <div className="flex flex-wrap gap-1 mb-3">
                          {(server.tags || []).slice(0, 3).map(tag => (
                            <span key={tag} className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-white/30">{tag}</span>
                          ))}
                        </div>
                        <div className="flex items-center justify-between pt-3 border-t border-white/5">
                          <div className="flex items-center gap-1 text-xs text-white/30">
                            <Zap className="w-3 h-3" strokeWidth={1.5} />
                            {(server.tools || []).map(t => t.name || t).join(', ')}
                          </div>
                          <button onClick={() => handleDelete(server.name)} className="opacity-0 group-hover:opacity-100 transition-opacity" data-testid={`delete-server-${server.name}`}>
                            <Trash2 className="w-3.5 h-3.5 text-red-400/60 hover:text-red-400" strokeWidth={1.5} />
                          </button>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>

                <Dialog open={registerOpen} onOpenChange={setRegisterOpen}>
                  <DialogContent className="bg-zinc-900 border-white/10" data-testid="register-dialog">
                    <DialogHeader>
                      <DialogTitle>Register MCP Server</DialogTitle>
                      <DialogDescription>Add a new MCP server to the NEXUS ecosystem.</DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-2">
                      <div>
                        <label className="text-xs text-white/50 mb-1 block">Server Name</label>
                        <Input placeholder="my-server" value={newServer.name} onChange={e => setNewServer(p => ({ ...p, name: e.target.value }))} className="bg-white/5 border-white/10" data-testid="register-server-name" />
                      </div>
                      <div>
                        <label className="text-xs text-white/50 mb-1 block">Command</label>
                        <Input placeholder="python" value={newServer.command} onChange={e => setNewServer(p => ({ ...p, command: e.target.value }))} className="bg-white/5 border-white/10" data-testid="register-server-command" />
                      </div>
                      <div>
                        <label className="text-xs text-white/50 mb-1 block">Args (comma separated)</label>
                        <Input placeholder="server.py, --port, 3001" value={newServer.args} onChange={e => setNewServer(p => ({ ...p, args: e.target.value }))} className="bg-white/5 border-white/10" data-testid="register-server-args" />
                      </div>
                    </div>
                    <DialogFooter>
                      <Button variant="outline" onClick={() => setRegisterOpen(false)} className="border-white/10">Cancel</Button>
                      <Button className="bg-sky-500 hover:bg-sky-400 text-black" onClick={handleRegister} data-testid="register-submit-btn">Register</Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </motion.div>
            )}

            {/* GRAPH */}
            {activeTab === 'graph' && (
              <motion.div key="graph" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} data-testid="graph-tab">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-lg font-semibold">Capability Graph</h2>
                    <p className="text-xs text-white/40 mt-1">{graphData?.total_edges || 0} connections discovered between servers</p>
                  </div>
                  <Button variant="outline" className="border-white/10" onClick={handleRebuildGraph} data-testid="rebuild-graph-btn">
                    <RefreshCw className="w-4 h-4 mr-2" strokeWidth={1.5} /> Rebuild Graph
                  </Button>
                </div>
                <Graph3D edges={graphData?.edges || []} servers={servers} />
              </motion.div>
            )}

            {/* PIPELINES */}
            {activeTab === 'pipelines' && (
              <motion.div key="pipelines" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} data-testid="pipelines-tab">
                <PipelinesTab onExecuted={fetchData} />
              </motion.div>
            )}

            {/* HISTORY */}
            {activeTab === 'history' && (
              <motion.div key="history" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} data-testid="history-tab">
                <h2 className="text-lg font-semibold mb-6">Pipeline History</h2>
                {history.length === 0 ? (
                  <div className="glass rounded-xl p-12 text-center">
                    <Clock className="w-8 h-8 text-white/20 mx-auto mb-3" strokeWidth={1.5} />
                    <p className="text-white/40">No pipeline runs yet</p>
                    <p className="text-sm text-white/20 mt-1">Execute a pipeline to see history here</p>
                  </div>
                ) : (
                  <div className="glass rounded-xl overflow-hidden">
                    <table className="w-full" data-testid="history-table">
                      <thead>
                        <tr className="border-b border-white/5">
                          <th className="text-left text-xs font-medium text-white/40 px-4 py-3">Request</th>
                          <th className="text-left text-xs font-medium text-white/40 px-4 py-3">Steps</th>
                          <th className="text-left text-xs font-medium text-white/40 px-4 py-3">Status</th>
                          <th className="text-left text-xs font-medium text-white/40 px-4 py-3">Duration</th>
                          <th className="text-left text-xs font-medium text-white/40 px-4 py-3">Confidence</th>
                        </tr>
                      </thead>
                      <tbody>
                        {history.map((run, i) => (
                          <tr key={run.id || i} className="border-b border-white/5 hover:bg-white/[0.02]" data-testid={`history-row-${i}`}>
                            <td className="px-4 py-3">
                              <span className="text-sm text-white/70 truncate block max-w-xs">{run.request}</span>
                            </td>
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-1 flex-wrap">
                                {(run.steps || []).map((step, j) => (
                                  <span key={j} className="text-[10px] px-1.5 py-0.5 rounded bg-sky-500/10 text-sky-400">{step.server}</span>
                                ))}
                              </div>
                            </td>
                            <td className="px-4 py-3">
                              <Badge className={run.success ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'}>
                                {run.success ? 'Success' : 'Failed'}
                              </Badge>
                            </td>
                            <td className="px-4 py-3 text-sm text-white/40">{run.total_duration}s</td>
                            <td className="px-4 py-3 text-sm text-white/40">{((run.confidence || 0) * 100).toFixed(0)}%</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
