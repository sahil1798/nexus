import { useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Search, Zap, Link2, RefreshCw, Database, Globe,
  ArrowRight, Activity, ChevronRight,
  Brain, Network, Cpu
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

const FEATURES = [
  { icon: Search, title: "Semantic Discovery", desc: "AI reads server metadata and understands what each tool truly does, beyond simple descriptions" },
  { icon: Link2, title: "Auto-Connection", desc: "Discovers non-obvious tool chains by analyzing compatibility between input and output schemas" },
  { icon: RefreshCw, title: "Schema Translation", desc: "Automatically bridges incompatible data formats between different MCP servers" },
  { icon: Zap, title: "Pipeline Execution", desc: "Runs multi-step workflows with intelligent retries and data aggregation between steps" },
  { icon: Database, title: "Persistent Memory", desc: "Capability graph survives restarts and learns new connections over time automatically" },
  { icon: Globe, title: "REST API", desc: "Clean REST interface makes it easy to integrate NEXUS with any existing system or workflow" },
];

const STATS = [
  { value: "5", label: "MCP Servers", suffix: "connected" },
  { value: "14", label: "Connections", suffix: "discovered" },
  { value: "O(N)", label: "Discovery", suffix: "complexity" },
  { value: "<3s", label: "Pipeline", suffix: "planning" },
];

const ARCH_STEPS = [
  { icon: Globe, label: "MCP Servers", desc: "5 independent microservices" },
  { icon: Brain, label: "NEXUS Core", desc: "Registry + Semantic Profiler" },
  { icon: Network, label: "Capability Graph", desc: "Vector embeddings + edges" },
  { icon: Zap, label: "Pipeline Engine", desc: "Discovery + execution" },
];

function NetworkCanvas() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animId;

    const resize = () => {
      canvas.width = canvas.offsetWidth * window.devicePixelRatio;
      canvas.height = canvas.offsetHeight * window.devicePixelRatio;
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    };
    resize();

    const nodes = Array.from({ length: 50 }, () => ({
      x: Math.random() * canvas.offsetWidth,
      y: Math.random() * canvas.offsetHeight,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      r: Math.random() * 2 + 1,
    }));

    const draw = () => {
      ctx.clearRect(0, 0, canvas.offsetWidth, canvas.offsetHeight);
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x;
          const dy = nodes[i].y - nodes[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 120) {
            ctx.beginPath();
            ctx.moveTo(nodes[i].x, nodes[i].y);
            ctx.lineTo(nodes[j].x, nodes[j].y);
            ctx.strokeStyle = `rgba(56, 189, 248, ${0.12 * (1 - dist / 120)})`;
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        }
      }
      nodes.forEach(n => {
        n.x += n.vx;
        n.y += n.vy;
        if (n.x < 0 || n.x > canvas.offsetWidth) n.vx *= -1;
        if (n.y < 0 || n.y > canvas.offsetHeight) n.vy *= -1;
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(56, 189, 248, 0.5)';
        ctx.fill();
      });
      animId = requestAnimationFrame(draw);
    };
    draw();

    const onResize = () => {
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      resize();
    };
    window.addEventListener('resize', onResize);
    return () => { cancelAnimationFrame(animId); window.removeEventListener('resize', onResize); };
  }, []);

  return <canvas ref={canvasRef} className="absolute inset-0 w-full h-full" />;
}

const fadeUp = {
  initial: { opacity: 0, y: 30 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true },
  transition: { duration: 0.6 },
};

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#050505]" data-testid="landing-page">
      {/* Navbar */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass" data-testid="navbar">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2" data-testid="logo-link">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-sky-400 to-indigo-500 flex items-center justify-center">
              <Network className="w-4 h-4 text-white" strokeWidth={1.5} />
            </div>
            <span className="text-lg font-bold tracking-tight">NEXUS</span>
          </Link>
          <div className="flex items-center gap-4">
            <Link to="/docs" className="text-sm text-white/50 hover:text-white/80 transition-colors hidden md:block" data-testid="nav-docs">Docs</Link>
            <Button variant="outline" size="sm" className="border-white/10 text-white/70 hover:text-white hidden md:flex" onClick={() => navigate('/dashboard')} data-testid="nav-dashboard">
              Dashboard
            </Button>
            <Button size="sm" className="bg-sky-500 hover:bg-sky-400 text-black font-medium rounded-full px-6" onClick={() => navigate('/dashboard')} data-testid="nav-get-started">
              Get Started
            </Button>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative min-h-screen flex items-center pt-16" data-testid="hero-section">
        <NetworkCanvas />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-[#050505]" />
        <div className="relative max-w-7xl mx-auto px-6 py-32">
          <motion.div {...fadeUp} className="max-w-3xl">
            <Badge className="bg-sky-500/10 text-sky-400 border-sky-500/20 mb-6" data-testid="hero-badge">
              <Activity className="w-3 h-3 mr-1" strokeWidth={1.5} /> AI-Powered MCP Orchestration
            </Badge>
            <h1 className="text-5xl md:text-7xl font-bold tracking-tight leading-none mb-6" data-testid="hero-title">
              <span className="text-white">NEXUS</span>
              <br />
              <span className="glow-text">The Intelligent</span>
              <br />
              <span className="glow-text">MCP Broker</span>
            </h1>
            <p className="text-lg md:text-xl text-white/50 max-w-xl mb-10 leading-relaxed" data-testid="hero-subtitle">
              MCP servers are powerful alone. NEXUS makes them powerful{' '}
              <span className="text-sky-400 font-medium">together</span>. Transform isolated tools into a unified, composable ecosystem.
            </p>
            <div className="flex flex-wrap gap-4">
              <Button size="lg" className="bg-white text-black hover:bg-white/90 rounded-full px-8 font-medium" onClick={() => navigate('/dashboard')} data-testid="hero-try-demo">
                Try Demo <ArrowRight className="w-4 h-4 ml-2" strokeWidth={1.5} />
              </Button>
              <Button size="lg" variant="outline" className="border-white/20 text-white hover:bg-white/5 rounded-full px-8" onClick={() => navigate('/docs')} data-testid="hero-view-docs">
                View Docs
              </Button>
            </div>
          </motion.div>

          {/* Terminal Preview */}
          <motion.div {...fadeUp} transition={{ delay: 0.3, duration: 0.6 }} className="mt-16 max-w-2xl">
            <div className="glass rounded-xl overflow-hidden" data-testid="hero-terminal">
              <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5">
                <div className="w-3 h-3 rounded-full bg-red-500/60" />
                <div className="w-3 h-3 rounded-full bg-yellow-500/60" />
                <div className="w-3 h-3 rounded-full bg-green-500/60" />
                <span className="ml-2 text-xs text-white/30 font-mono">nexus-cli</span>
              </div>
              <div className="p-4 font-mono text-sm space-y-1">
                <div className="text-white/40">$ nexus execute</div>
                <div className="text-sky-400">&gt; "Fetch CNN.com, summarize, analyze sentiment, post to #team"</div>
                <div className="text-white/30 mt-2">Planning pipeline...</div>
                <div className="text-emerald-400">Step 1: web-fetcher.fetch_url <span className="text-white/30">1.7s</span></div>
                <div className="text-emerald-400">Step 2: summarizer.summarize_text <span className="text-white/30">3.9s</span></div>
                <div className="text-emerald-400">Step 3: sentiment-analyzer.analyze_sentiment <span className="text-white/30">0.8s</span></div>
                <div className="text-emerald-400">Step 4: slack-sender.send_slack_message <span className="text-white/30">1.2s</span></div>
                <div className="text-green-400 mt-2 font-semibold">Pipeline completed in 7.6s</div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Problem / Solution */}
      <section className="py-20 md:py-32" data-testid="problem-solution-section">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div {...fadeUp} className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-semibold tracking-tight mb-4" data-testid="problem-solution-title">
              What if AI could <span className="text-sky-400">figure out</span> how to combine tools?
            </h2>
            <p className="text-white/40 max-w-2xl mx-auto text-base md:text-lg">
              Traditional MCP servers work in isolation. NEXUS reads their metadata, understands their capabilities, and automatically discovers how they can work together.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <motion.div {...fadeUp} className="glass rounded-2xl p-8" data-testid="problem-card">
              <div className="text-red-400 text-sm font-semibold uppercase tracking-wider mb-4">The Problem</div>
              <h3 className="text-xl font-semibold mb-4">Isolated Tool Islands</h3>
              <div className="grid grid-cols-3 gap-3">
                {['web-fetcher', 'summarizer', 'translator', 'sentiment', 'slack'].map((s) => (
                  <div key={s} className="bg-white/5 rounded-lg p-3 text-center">
                    <div className="w-8 h-8 rounded-full bg-red-500/10 border border-red-500/20 mx-auto mb-2 flex items-center justify-center">
                      <Cpu className="w-4 h-4 text-red-400" strokeWidth={1.5} />
                    </div>
                    <div className="text-xs text-white/40 truncate">{s}</div>
                  </div>
                ))}
              </div>
              <p className="text-white/30 text-sm mt-4">Each server exists in isolation. No knowledge of other servers.</p>
            </motion.div>

            <motion.div {...fadeUp} transition={{ delay: 0.15 }} className="glass rounded-2xl p-8 glow-border" data-testid="solution-card">
              <div className="text-sky-400 text-sm font-semibold uppercase tracking-wider mb-4">The Solution</div>
              <h3 className="text-xl font-semibold mb-4">Connected Ecosystem</h3>
              <div className="grid grid-cols-3 gap-3">
                {['web-fetcher', 'summarizer', 'translator', 'sentiment', 'slack'].map((s) => (
                  <div key={s} className="bg-sky-500/5 rounded-lg p-3 text-center border border-sky-500/10">
                    <div className="w-8 h-8 rounded-full bg-sky-500/10 border border-sky-500/30 mx-auto mb-2 flex items-center justify-center">
                      <Cpu className="w-4 h-4 text-sky-400" strokeWidth={1.5} />
                    </div>
                    <div className="text-xs text-white/60 truncate">{s}</div>
                  </div>
                ))}
              </div>
              <p className="text-white/30 text-sm mt-4">NEXUS discovers 14 connections automatically via semantic analysis.</p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 md:py-32" data-testid="features-section">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div {...fadeUp} className="mb-16">
            <h2 className="text-3xl md:text-4xl font-semibold tracking-tight mb-4" data-testid="features-title">
              Built for the <span className="text-sky-400">next generation</span> of tool orchestration
            </h2>
            <p className="text-white/40 max-w-xl text-base">
              Six core capabilities that transform how MCP servers interact.
            </p>
          </motion.div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map((f, i) => (
              <motion.div key={f.title} {...fadeUp} transition={{ delay: i * 0.08 }}
                className="glass rounded-2xl p-6 hover:bg-white/[0.03] transition-all duration-300 group cursor-default"
                data-testid={`feature-card-${i}`}
              >
                <div className="w-10 h-10 rounded-xl bg-sky-500/10 flex items-center justify-center mb-4 group-hover:bg-sky-500/20 transition-colors">
                  <f.icon className="w-5 h-5 text-sky-400" strokeWidth={1.5} />
                </div>
                <h3 className="font-semibold mb-2 text-white/90">{f.title}</h3>
                <p className="text-sm text-white/40 leading-relaxed">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Architecture */}
      <section className="py-20 md:py-32" data-testid="architecture-section">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div {...fadeUp} className="mb-16">
            <h2 className="text-3xl md:text-4xl font-semibold tracking-tight mb-4" data-testid="architecture-title">
              How <span className="text-sky-400">NEXUS</span> works
            </h2>
            <p className="text-white/40 max-w-xl text-base">From registration to execution in four intelligent steps.</p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {ARCH_STEPS.map((step, i) => (
              <motion.div key={step.label} {...fadeUp} transition={{ delay: i * 0.12 }} className="relative">
                <div className="glass rounded-2xl p-6" data-testid={`arch-step-${i}`}>
                  <div className="text-sky-400/20 text-5xl font-bold absolute top-4 right-4 select-none">
                    {String(i + 1).padStart(2, '0')}
                  </div>
                  <div className="w-12 h-12 rounded-xl bg-sky-500/10 flex items-center justify-center mb-4">
                    <step.icon className="w-6 h-6 text-sky-400" strokeWidth={1.5} />
                  </div>
                  <h3 className="font-semibold mb-1">{step.label}</h3>
                  <p className="text-sm text-white/40">{step.desc}</p>
                </div>
                {i < ARCH_STEPS.length - 1 && (
                  <div className="hidden md:flex justify-center py-3">
                    <ChevronRight className="w-5 h-5 text-sky-400/20" />
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-20 md:py-32" data-testid="stats-section">
        <div className="max-w-7xl mx-auto px-6">
          <div className="glass rounded-3xl p-8 md:p-12">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
              {STATS.map((s, i) => (
                <motion.div key={s.label} {...fadeUp} transition={{ delay: i * 0.1 }} className="text-center" data-testid={`stat-${i}`}>
                  <div className="text-4xl md:text-5xl font-bold glow-text mb-2">{s.value}</div>
                  <div className="text-sm font-medium text-white/70">{s.label}</div>
                  <div className="text-xs text-white/30">{s.suffix}</div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 md:py-32" data-testid="cta-section">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <motion.div {...fadeUp}>
            <h2 className="text-3xl md:text-4xl font-semibold tracking-tight mb-4" data-testid="cta-title">
              Ready to orchestrate?
            </h2>
            <p className="text-white/40 max-w-lg mx-auto mb-8 text-base">
              Start building intelligent pipelines with NEXUS. Connect your MCP servers and let AI handle the rest.
            </p>
            <Button size="lg" className="bg-white text-black hover:bg-white/90 rounded-full px-8 font-medium" onClick={() => navigate('/dashboard')} data-testid="cta-launch">
              Launch Dashboard <ArrowRight className="w-4 h-4 ml-2" strokeWidth={1.5} />
            </Button>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8" data-testid="footer">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-gradient-to-br from-sky-400 to-indigo-500 flex items-center justify-center">
              <Network className="w-3 h-3 text-white" strokeWidth={1.5} />
            </div>
            <span className="text-sm font-semibold">NEXUS</span>
            <span className="text-xs text-white/30">v1.0.0</span>
          </div>
          <div className="flex items-center gap-6 text-xs text-white/30">
            <Link to="/docs" className="hover:text-white/60 transition-colors">API Docs</Link>
            <Link to="/dashboard" className="hover:text-white/60 transition-colors">Dashboard</Link>
            <span>Powered by Gemini 3 Flash</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
