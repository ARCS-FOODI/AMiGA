import { useState, useEffect, useRef } from 'react';

let logIdCounter = 0;

export default function DiagnosticConsole() {
    const [logs, setLogs] = useState([]);
    const [isOpen, setIsOpen] = useState(false);
    const [perfStats, setPerfStats] = useState({ domNodes: 0, jsHeapMb: 'N/A' });
    const [activePoints, setActivePoints] = useState({ total: 0, details: {} });
    const [cumulativeKb, setCumulativeKb] = useState(0);
    const [totalEvents, setTotalEvents] = useState(0);
    const bottomRef = useRef(null);

    // Track Chart Data Size
    useEffect(() => {
        const handleChartSize = (e) => {
            setActivePoints(prev => {
                const newDetails = { ...prev.details, [e.detail.chartId]: e.detail.points };
                const total = Object.values(newDetails).reduce((sum, val) => sum + val, 0);
                return { total, details: newDetails };
            });
        };
        window.addEventListener('chart-data-size', handleChartSize);
        return () => window.removeEventListener('chart-data-size', handleChartSize);
    }, []);

    // Track performance metrics
    useEffect(() => {
        const interval = setInterval(() => {
            setPerfStats({
                domNodes: document.getElementsByTagName('*').length,
                jsHeapMb: window.performance?.memory ? (window.performance.memory.usedJSHeapSize / (1024 * 1024)).toFixed(1) : 'N/A'
            });
        }, 1000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        const handleLog = (e) => {
            if (e.detail.kbSize) {
                setCumulativeKb(prev => prev + parseFloat(e.detail.kbSize));
            }
            setTotalEvents(prev => prev + 1);
            setLogs(prev => {
                const newLog = { ...e.detail, id: ++logIdCounter };
                const newLogs = [...prev, newLog];
                // Keep only the last 100 logs to prevent memory leaks
                if (newLogs.length > 100) return newLogs.slice(newLogs.length - 100);
                return newLogs;
            });
        };
        window.addEventListener('telemetry-metric', handleLog);
        return () => window.removeEventListener('telemetry-metric', handleLog);
    }, []);

    // Scroll throttle to prevent layout thrashing
    const scrollTimeout = useRef(null);
    useEffect(() => {
        if (isOpen && bottomRef.current) {
            if (scrollTimeout.current) clearTimeout(scrollTimeout.current);
            scrollTimeout.current = setTimeout(() => {
                bottomRef.current?.scrollIntoView({ behavior: 'auto' });
            }, 100);
        }
    }, [logs, isOpen]);

    return (
        <div style={{
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            width: isOpen ? '500px' : 'auto',
            background: 'rgba(15, 15, 20, 0.85)',
            border: isOpen ? '1px solid var(--accent-blue)' : '1px solid var(--glass-border)',
            borderRadius: '8px',
            backdropFilter: 'blur(10px)',
            zIndex: 9999,
            display: 'flex',
            flexDirection: 'column',
            boxShadow: isOpen ? '0 0 20px rgba(59, 130, 246, 0.2)' : '0 4px 20px rgba(0, 0, 0, 0.5)',
            transition: 'all 0.2s ease',
            color: 'var(--text-primary)'
        }}>
           {/* Header Toggle */}
           <div 
               onClick={() => setIsOpen(!isOpen)}
               style={{
                   padding: '10px 15px',
                   cursor: 'pointer',
                   display: 'flex',
                   justifyContent: 'space-between',
                   alignItems: 'center',
                   borderBottom: isOpen ? '1px solid rgba(255,255,255,0.1)' : 'none',
                   fontWeight: 'bold',
               }}
           >
               <span style={{ fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px', color: isOpen ? 'var(--accent-blue)' : 'var(--text-primary)' }}>
                   {isOpen ? '▼' : '▲'} API Diagnostics Terminal
               </span>
               <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                   {/* Performance Badges */}
                   <span title="Total Chart Data Points Held in Client Array Memory" style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)', padding: '2px 8px', borderRadius: '12px', fontSize: '0.7rem', color: 'var(--accent-green)' }}>
                       📊 {activePoints.total} PTS
                   </span>
                   <span title="Cumulative Network Payload Extracted" style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', padding: '2px 8px', borderRadius: '12px', fontSize: '0.7rem', color: 'var(--accent-red)' }}>
                       🌐 {(cumulativeKb / 1024).toFixed(2)} MB Rx
                   </span>
                   {perfStats.jsHeapMb !== 'N/A' && (
                       <span title="JS Heap Memory" style={{ background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.3)', padding: '2px 8px', borderRadius: '12px', fontSize: '0.7rem', color: 'var(--accent-blue)' }}>
                           🧠 {perfStats.jsHeapMb}MB
                       </span>
                   )}
                   <span title="Total DOM Nodes" style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', padding: '2px 8px', borderRadius: '12px', fontSize: '0.7rem', color: 'var(--accent-red)' }}>
                       📄 {perfStats.domNodes} DOM
                   </span>
                   
                   {logs.some(l => l.level === 'warn' || l.level === 'error') && !isOpen && (
                       <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-yellow)', boxShadow: '0 0 8px var(--accent-yellow)', animation: 'pulse-live 2s infinite' }}></span>
                   )}
                   <span style={{ background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)', padding: '2px 8px', borderRadius: '12px', fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
                       {totalEvents} total events tracked
                   </span>
               </div>
           </div>

           {/* Console Body */}
           {isOpen && (
               <div style={{ 
                   height: '350px', 
                   overflowY: 'auto', 
                   padding: '12px', 
                   display: 'flex', 
                   flexDirection: 'column', 
                   gap: '6px', 
                   fontSize: '0.75rem', 
                   fontFamily: 'monospace',
                   background: 'rgba(0,0,0,0.5)',
                   borderRadius: '0 0 8px 8px'
               }}>
                   {logs.length === 0 ? (
                       <div style={{ color: 'var(--text-secondary)', textAlign: 'center', marginTop: 'auto', marginBottom: 'auto' }}>
                           Monitoring API payload metrics...
                       </div>
                   ) : (
                       logs.map((log) => (
                           <div key={log.id} style={{
                               color: log.level === 'error' ? 'var(--accent-red)' : log.level === 'warn' ? 'var(--accent-yellow)' : '#A3A3A3',
                               borderBottom: '1px solid rgba(255,255,255,0.03)',
                               paddingBottom: '4px',
                               display: 'flex',
                               gap: '8px',
                               alignItems: 'baseline'
                           }}>
                               <span style={{ color: 'var(--text-secondary)', fontSize: '0.65rem', flexShrink: 0 }}>[{log.time}]</span>
                               <span style={{ wordBreak: 'break-all' }}>{log.message}</span>
                           </div>
                       ))
                   )}
                   <div ref={bottomRef} />
               </div>
           )}
        </div>
    );
}
