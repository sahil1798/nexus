import { useRef, useMemo, useEffect, useState } from 'react';
import ForceGraph3D from 'react-force-graph-3d';

const SERVER_COLORS = {
  'web-fetcher': '#38bdf8',
  'summarizer': '#a78bfa',
  'translator': '#34d399',
  'sentiment-analyzer': '#f472b6',
  'slack-sender': '#fbbf24',
};

export default function Graph3D({ edges = [], servers = [] }) {
  const graphRef = useRef();
  const containerRef = useRef();
  const [dimensions, setDimensions] = useState({ width: 800, height: 500 });

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const update = () => {
      const rect = container.getBoundingClientRect();
      setDimensions({ width: rect.width, height: Math.max(rect.height, 500) });
    };
    update();
    const observer = new ResizeObserver(update);
    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  const graphData = useMemo(() => {
    const nodeMap = new Map();
    servers.forEach(s => {
      nodeMap.set(s.name, {
        id: s.name,
        name: s.name,
        domain: s.domain,
        tools: (s.tools || []).map(t => t.name || t),
        color: SERVER_COLORS[s.name] || '#94a3b8',
        val: 10,
      });
    });

    edges.forEach(e => {
      const src = e.source.split('.')[0];
      const tgt = e.target.split('.')[0];
      if (!nodeMap.has(src)) nodeMap.set(src, { id: src, name: src, color: '#94a3b8', val: 6 });
      if (!nodeMap.has(tgt)) nodeMap.set(tgt, { id: tgt, name: tgt, color: '#94a3b8', val: 6 });
    });

    const links = edges.map(e => ({
      source: e.source.split('.')[0],
      target: e.target.split('.')[0],
      type: e.type,
      confidence: e.confidence,
      hint: e.hint,
      color: e.type === 'direct' ? 'rgba(34, 197, 94, 0.6)' : 'rgba(56, 189, 248, 0.35)',
    }));

    return { nodes: Array.from(nodeMap.values()), links };
  }, [edges, servers]);

  return (
    <div ref={containerRef} className="glass rounded-xl overflow-hidden relative" style={{ height: '500px' }} data-testid="graph-3d-container">
      <ForceGraph3D
        ref={graphRef}
        graphData={graphData}
        width={dimensions.width}
        height={500}
        backgroundColor="#0a0a0a"
        nodeLabel={node =>
          `<div style="background:rgba(0,0,0,0.85);color:#fff;padding:6px 10px;border-radius:6px;font-size:12px;border:1px solid rgba(255,255,255,0.1);font-family:Plus Jakarta Sans,sans-serif"><strong>${node.name}</strong>${node.tools ? '<br/><span style="color:#38bdf8;font-size:10px">' + node.tools.join(', ') + '</span>' : ''}</div>`
        }
        nodeColor={node => node.color}
        nodeOpacity={0.95}
        nodeResolution={20}
        linkColor={link => link.color}
        linkWidth={link => link.confidence * 2.5}
        linkOpacity={0.7}
        linkDirectionalParticles={3}
        linkDirectionalParticleSpeed={0.004}
        linkDirectionalParticleWidth={1.5}
        linkDirectionalParticleColor={() => '#38bdf8'}
        enableNodeDrag={true}
        enableNavigationControls={true}
        warmupTicks={100}
        cooldownTicks={0}
        autoRotate={false}
      />

      {/* Legend */}
      <div className="absolute bottom-4 left-4 glass rounded-lg p-3 z-10" data-testid="graph-legend">
        <div className="text-[10px] text-white/40 mb-2 font-medium uppercase tracking-wider">Servers</div>
        <div className="space-y-1.5">
          {Object.entries(SERVER_COLORS).map(([name, color]) => (
            <div key={name} className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: color }} />
              <span className="text-[11px] text-white/50">{name}</span>
            </div>
          ))}
        </div>
        <div className="mt-2 pt-2 border-t border-white/5 space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-emerald-500/60 rounded" />
            <span className="text-[10px] text-white/40">Direct</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-sky-500/40 rounded" />
            <span className="text-[10px] text-white/40">Translatable</span>
          </div>
        </div>
      </div>

      {/* Controls hint */}
      <div className="absolute top-4 right-4 text-[10px] text-white/20 glass rounded-lg px-3 py-2 z-10" data-testid="graph-controls-hint">
        Drag to rotate / Scroll to zoom / Click to select
      </div>
    </div>
  );
}
