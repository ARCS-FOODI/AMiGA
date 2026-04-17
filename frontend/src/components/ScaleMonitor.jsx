import { useState, useEffect, useRef } from 'react';
import { getScaleWeight } from '../api';
import { POLL_INTERVALS } from '../polling';

// Polling interval in ms
const HISTORY_LENGTH = 30;

// Compute trend arrow from recent history
function getTrend(history) {
    if (!history || history.length < 3) return null;
    const recent = history.slice(-5);
    const slope  = (recent[recent.length - 1] - recent[0]) / recent.length;
    if (slope >  0.05) return { symbol: '↑', color: '#10b981', label: 'Increasing' };
    if (slope < -0.05) return { symbol: '↓', color: '#eab308', label: 'Decreasing' };
    return { symbol: '→', color: 'rgba(255,255,255,0.35)', label: 'Stable' };
}

export default function ScaleMonitor() {
    const [absoluteWeight, setAbsoluteWeight] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [history, setHistory] = useState([]);
    const historyRef = useRef([]);

    // LocalStorage Reference State
    const [referenceWeight, setReferenceWeight] = useState(() => {
        const saved = localStorage.getItem('amiga_scale_ref');
        return saved !== null ? parseFloat(saved) : 0;
    });

    const pollLiveScale = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await getScaleWeight();
            const w = data.weight;
            setAbsoluteWeight(w);

            // Update history (Absolute values)
            const updated = [...historyRef.current, w].slice(-HISTORY_LENGTH);
            historyRef.current = updated;
            setHistory(updated);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleSetReference = () => {
        const newRef = absoluteWeight || 0;
        setReferenceWeight(newRef);
        localStorage.setItem('amiga_scale_ref', newRef.toString());
    };

    const handleResetReference = () => {
        setReferenceWeight(0);
        localStorage.setItem('amiga_scale_ref', '0');
    };

    useEffect(() => {
        pollLiveScale();
        const liveInterval = setInterval(pollLiveScale, POLL_INTERVALS.FAST);
        return () => clearInterval(liveInterval);
    }, []);

    const netWeight = absoluteWeight !== null ? absoluteWeight - referenceWeight : null;
    const trend = getTrend(history);

    return (
        <div className="glass-card" style={{ position: 'relative', overflow: 'hidden', minHeight: '340px' }}>
            {/* Loading indicator bar */}
            {loading && (
                <div style={{
                    position: 'absolute', top: 0, left: 0,
                    width: '100%', height: '4px',
                    background: 'var(--accent-purple)',
                    animation: 'pulse 1s infinite'
                }} />
            )}

            {/* Header row */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <h3 style={{ margin: 0 }}>⚖️ Precision Scale</h3>
                    <span 
                        style={{ 
                            fontSize: '0.65rem', 
                            background: 'rgba(255,255,255,0.05)', 
                            padding: '2px 8px', 
                            borderRadius: '10px',
                            color: 'var(--text-secondary)'
                        }}
                    >
                        LIVE 2Hz
                    </span>
                </div>
                <div className={`status-indicator ${absoluteWeight !== null && !error ? 'status-online' : 'status-neutral'}`}></div>
            </div>

            {/* Error display */}
            {error && <div style={{ color: 'var(--accent-red)', fontSize: '0.85rem', marginBottom: '1rem' }}>{error}</div>}

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '2rem' }}>
                
                {/* Main Readouts */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px' }}>Net Weight (Relative)</span>
                        <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
                            <div style={{ 
                                fontSize: '3.5rem', 
                                fontWeight: 'bold', 
                                fontFamily: 'monospace',
                                color: netWeight !== null && netWeight < 0 ? 'var(--accent-red)' : 'var(--accent-purple)',
                            }}>
                                {netWeight !== null ? netWeight.toFixed(3) : '--.---'}
                            </div>
                            <span style={{ fontSize: '1.5rem', color: 'var(--text-secondary)' }}>g</span>
                            
                            {trend && (
                                <div style={{ marginLeft: '1rem', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                                    <span style={{ fontSize: '1.5rem', color: trend.color }}>{trend.symbol}</span>
                                    <span style={{ fontSize: '0.5rem', color: 'var(--text-secondary)' }}>{trend.label}</span>
                                </div>
                            )}
                        </div>
                    </div>

                    <div style={{ display: 'flex', gap: '2rem', background: 'rgba(0,0,0,0.15)', padding: '1.25rem', borderRadius: '12px', border: '1px solid var(--glass-border)' }}>
                        <div>
                            <span style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.6)', fontWeight: '600', display: 'block', marginBottom: '4px' }}>ABS GROSS</span>
                            <span style={{ fontSize: '1.2rem', fontWeight: 'bold', fontFamily: 'monospace' }}>
                                {absoluteWeight !== null ? absoluteWeight.toFixed(3) : '--.---'}g
                            </span>
                        </div>
                        <div style={{ borderLeft: '1px solid var(--glass-border)', paddingLeft: '2rem' }}>
                            <span style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.6)', fontWeight: '600', display: 'block', marginBottom: '4px' }}>REFERENCE</span>
                            <span style={{ fontSize: '1.2rem', fontWeight: 'bold', fontFamily: 'monospace', color: 'var(--accent-teal)' }}>
                                {referenceWeight.toFixed(3)}g
                            </span>
                        </div>
                    </div>

                    <div style={{ display: 'flex', gap: '0.75rem' }}>
                        <button className="purple" onClick={handleSetReference} style={{ flex: 1 }}>Set Reference</button>
                        <button onClick={handleResetReference} style={{ padding: '0.6rem 1rem', background: 'rgba(255,255,255,0.05)' }}>Reset</button>
                    </div>
                </div>

                {/* Graph Area */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Weight Visualization</span>
                        <span style={{ fontSize: '0.6rem', color: 'var(--accent-teal)', opacity: 0.8 }}>--- Baseline At Ref</span>
                    </div>
                    <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '12px', border: '1px solid var(--glass-border)', flexGrow: 1, display: 'flex', alignItems: 'center' }}>
                        <Sparkline data={history} reference={referenceWeight} />
                    </div>
                </div>

            </div>
        </div>
    );
}

function Sparkline({ data, reference }) {
    if (!data || data.length < 2) {
        return <div style={{ height: '120px', width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Awaiting readings...</div>;
    }

    const width = 400;
    const height = 120;
    const padding = 10;

    // We want the graph to always show the reference line, so we include it in the bounds
    const allVals = [...data, reference];
    const min = Math.min(...allVals);
    const max = Math.max(...allVals);
    const range = max - min || 1;

    const getY = (val) => height - padding - ((val - min) / range) * (height - 2 * padding);

    const points = data.map((val, i) => {
        const x = padding + (i / (data.length - 1)) * (width - 2 * padding);
        const y = getY(val);
        return `${x},${y}`;
    });

    const polyline = points.join(' ');
    const refY = getY(reference);

    return (
        <svg viewBox={`0 0 ${width} ${height}`} width="100%" height="120" preserveAspectRatio="none">
            <defs>
                <linearGradient id="absFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--accent-purple)" stopOpacity="0.3" />
                    <stop offset="100%" stopColor="var(--accent-purple)" stopOpacity="0" />
                </linearGradient>
            </defs>
            
            {/* Reference Dash Line */}
            <line 
                x1={padding} y1={refY} x2={width - padding} y2={refY} 
                stroke="var(--accent-teal)" 
                strokeWidth="1" 
                strokeDasharray="4 4" 
                opacity="0.6"
            />

            {/* Area Fill */}
            <polygon
                points={`${points.join(' ')} ${padding + (data.length - 1) / (data.length-1) * (width-2*padding)},${height-padding} ${padding},${height-padding}`}
                fill="url(#absFill)"
                opacity="0.5"
            />

            {/* Line Path */}
            <polyline
                points={polyline}
                fill="none"
                stroke="var(--accent-purple)"
                strokeWidth="2.5"
                strokeLinejoin="round"
                strokeLinecap="round"
            />

            {/* Current Value Dot */}
            <circle
                cx={padding + (data.length - 1) / (data.length - 1) * (width - 2 * padding)}
                cy={getY(data[data.length - 1])}
                r="4"
                fill="var(--accent-purple)"
                style={{ filter: 'drop-shadow(0 0 5px var(--accent-purple))' }}
            />
        </svg>
    );
}
