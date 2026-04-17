import { useState, useEffect } from 'react';
import { snapshotTSL2561 } from '../api';
import { POLL_INTERVALS } from '../polling';

const LUX_MAX = 10000; // Reference ceiling for the intensity bar

// ─── Lux intensity bar ────────────────────────────────────────────────────────
function LuxBar({ lux }) {
    const pct = lux != null ? Math.min(100, (lux / LUX_MAX) * 100) : 0;

    // Derive a contextual label for the current intensity
    const getContext = (lx) => {
        if (lx == null) return '';
        if (lx < 100)   return 'Very Dark';
        if (lx < 500)   return 'Dim / Dusk';
        if (lx < 1000)  return 'Indoor Office';
        if (lx < 5000)  return 'Bright Interior';
        if (lx < 10000) return 'Overcast Outdoors';
        return 'Full Sunlight';
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
            {/* Label + value */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                    <span style={{ fontSize: '0.72rem', color: 'rgba(255,255,255,0.38)', textTransform: 'uppercase', letterSpacing: '1px' }}>
                        ☀️ Lux Intensity
                    </span>
                    <span style={{ fontSize: '0.68rem', color: '#d97706', fontStyle: 'italic' }}>
                        {getContext(lux)}
                    </span>
                </div>
                <span style={{
                    fontFamily: 'monospace', fontSize: '1.8rem', fontWeight: 'bold',
                    color: '#eab308', textShadow: '0 0 18px rgba(234,179,8,0.6)',
                    lineHeight: 1,
                }}>
                    {lux != null ? lux.toLocaleString() : '--'}
                    <span style={{ fontSize: '0.85rem', color: 'rgba(255,255,255,0.38)', marginLeft: '4px' }}>lx</span>
                </span>
            </div>

            {/* Gradient fill bar — taller for more visual weight */}
            <div style={{
                position: 'relative', height: '26px',
                background: 'rgba(0,0,0,0.32)', borderRadius: '13px',
                overflow: 'hidden', border: '1px solid rgba(255,255,255,0.06)',
            }}>
                <div style={{
                    position: 'absolute', top: 0, left: 0, height: '100%',
                    width: `${pct}%`,
                    background: 'linear-gradient(90deg, #78350f, #b45309, #d97706, #eab308, #fef08a)',
                    borderRadius: '13px',
                    transition: 'width 1s ease',
                    boxShadow: lux > 0 ? '0 0 14px rgba(234,179,8,0.5)' : 'none',
                }} />
                {/* Glow shimmer overlay */}
                <div style={{
                    position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'linear-gradient(180deg, rgba(255,255,255,0.08) 0%, transparent 60%)',
                    borderRadius: '13px', pointerEvents: 'none',
                }} />
                {/* Percentage label */}
                <div style={{
                    position: 'absolute', right: '0.75rem', top: '50%', transform: 'translateY(-50%)',
                    fontSize: '0.72rem', fontWeight: 'bold',
                    color: pct > 50 ? 'rgba(0,0,0,0.7)' : 'rgba(255,255,255,0.5)',
                }}>
                    {lux != null ? `${Math.round(pct)}%` : ''}
                </div>
            </div>

            {/* Scale ticks */}
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.59rem', color: 'rgba(255,255,255,0.2)' }}>
                <span>0</span>
                <span>Office · 500lx</span>
                <span>Overcast · 5k</span>
                <span>Full Sun · 10k</span>
            </div>
        </div>
    );
}

// ─── Broadband / IR spectrum split bar ───────────────────────────────────────
function SpectrumBar({ broadband, infrared }) {
    const total = (broadband ?? 0) + (infrared ?? 0);
    const bbPct = total > 0 ? (broadband / total) * 100 : 50;
    const irPct = 100 - bbPct;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.55rem' }}>
            <span style={{ fontSize: '0.72rem', color: 'rgba(255,255,255,0.38)', textTransform: 'uppercase', letterSpacing: '1px' }}>
                Light Spectrum Split
            </span>

            {/* Split bar */}
            <div style={{
                position: 'relative', height: '18px', borderRadius: '9px',
                overflow: 'hidden', display: 'flex',
                border: '1px solid rgba(255,255,255,0.06)',
            }}>
                {/* Broadband (visible) */}
                <div style={{
                    width: `${bbPct}%`,
                    background: 'linear-gradient(90deg, #0369a1, #0ea5e9, #38bdf8)',
                    transition: 'width 1s ease',
                }} />
                {/* Infrared */}
                <div style={{
                    width: `${irPct}%`,
                    background: 'linear-gradient(90deg, #dc2626, #ef4444, #f87171)',
                    transition: 'width 1s ease',
                }} />
                {/* Center divider line */}
                <div style={{
                    position: 'absolute', left: `${bbPct}%`, top: 0, bottom: 0,
                    width: '2px', background: 'rgba(0,0,0,0.4)', transform: 'translateX(-50%)',
                    transition: 'left 1s ease',
                }} />
            </div>

            {/* Labels row */}
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <div style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#38bdf8', flexShrink: 0 }} />
                    <span style={{ color: 'rgba(255,255,255,0.45)' }}>Broadband</span>
                    <span style={{ fontFamily: 'monospace', color: '#38bdf8', fontWeight: 'bold' }}>
                        {broadband ?? '--'}
                    </span>
                    <span style={{ fontSize: '0.62rem', color: 'rgba(255,255,255,0.25)' }}>
                        ({broadband != null ? Math.round(bbPct) : '--'}%)
                    </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <span style={{ fontSize: '0.62rem', color: 'rgba(255,255,255,0.25)' }}>
                        ({infrared != null ? Math.round(irPct) : '--'}%)
                    </span>
                    <span style={{ fontFamily: 'monospace', color: '#f87171', fontWeight: 'bold' }}>
                        {infrared ?? '--'}
                    </span>
                    <span style={{ color: 'rgba(255,255,255,0.45)' }}>Infrared</span>
                    <div style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#f87171', flexShrink: 0 }} />
                </div>
            </div>
        </div>
    );
}

// ─── Main component ───────────────────────────────────────────────────────────
export default function TSL2561Monitor({ title = "Luminosity (TSL2561)" }) {
    const [data,    setData]    = useState(null);
    const [loading, setLoading] = useState(false);
    const [error,   setError]   = useState(null);

    const pollSensor = async () => {
        setLoading(true);
        setError(null);
        try {
            const result = await snapshotTSL2561();
            setData(result);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        pollSensor();
        const interval = setInterval(pollSensor, POLL_INTERVALS.NORMAL);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="glass-card" style={{ gridColumn: 'span 2' }}>
            {/* ── Header ── */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
                    <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#eab308', boxShadow: '0 0 8px #eab308' }} />
                    <h3 style={{ margin: 0 }}>☀️ {title}</h3>
                    <span style={{ fontSize: '0.65rem', background: 'rgba(255,255,255,0.05)', padding: '2px 8px', borderRadius: '10px', color: 'var(--text-secondary)' }}>
                        LIVE 0.5Hz
                    </span>
                    {data?.simulated && (
                        <span style={{
                            fontSize: '0.65rem', fontWeight: 'bold', padding: '2px 8px', borderRadius: '20px',
                            background: 'rgba(234,179,8,0.15)', color: 'var(--accent-yellow)',
                            border: '1px solid rgba(234,179,8,0.4)',
                        }}>SIMULATED</span>
                    )}
                </div>
                <button onClick={pollSensor} disabled={loading} className="btn-secondary">
                    {loading ? 'Reading...' : 'Refresh'}
                </button>
            </div>

            {error && (
                <div style={{ color: 'var(--accent-red)', fontSize: '0.85rem', marginBottom: '1rem', padding: '0.5rem', background: 'rgba(239,68,68,0.1)', borderRadius: '4px' }}>⚠️ {error}</div>
            )}

            {/* ── Visuals ── */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.6rem' }}>
                <LuxBar lux={data?.lux} />
                <hr style={{ border: 'none', borderTop: '1px solid rgba(255,255,255,0.05)', margin: '0' }} />
                <SpectrumBar broadband={data?.broadband} infrared={data?.infrared} />
            </div>

            {/* ── Footer ── */}
            <div style={{ marginTop: '1.2rem', textAlign: 'right', fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
                Last update: <span style={{ color: 'var(--text-primary)' }}>{data?.timestamp?.split(' ')[1] || '--:--:--'}</span>
            </div>
        </div>
    );
}
