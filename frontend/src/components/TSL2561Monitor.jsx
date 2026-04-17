import { useState, useEffect } from 'react';
import { snapshotTSL2561 } from '../api';

const LUX_MAX = 10000; // Reference ceiling for the intensity bar

// ─── Lux intensity bar ────────────────────────────────────────────────────────
function LuxBar({ lux }) {
    const pct = lux != null ? Math.min(100, (lux / LUX_MAX) * 100) : 0;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {/* Label + value */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <span style={{ fontSize: '0.72rem', color: 'rgba(255,255,255,0.38)', textTransform: 'uppercase', letterSpacing: '1px' }}>
                    ☀️ Lux Intensity
                </span>
                <span style={{
                    fontFamily: 'monospace', fontSize: '1.35rem', fontWeight: 'bold',
                    color: '#eab308', textShadow: '0 0 14px rgba(234,179,8,0.55)',
                }}>
                    {lux != null ? lux.toLocaleString() : '--'}
                    <span style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.38)', marginLeft: '4px' }}>lx</span>
                </span>
            </div>

            {/* Gradient fill bar */}
            <div style={{
                position: 'relative', height: '20px',
                background: 'rgba(0,0,0,0.32)', borderRadius: '10px',
                overflow: 'hidden', border: '1px solid rgba(255,255,255,0.06)',
            }}>
                <div style={{
                    position: 'absolute', top: 0, left: 0, height: '100%',
                    width: `${pct}%`,
                    background: 'linear-gradient(90deg, #78350f, #b45309, #d97706, #eab308, #fde68a)',
                    borderRadius: '10px',
                    transition: 'width 0.9s ease',
                    boxShadow: lux > 0 ? '0 0 10px rgba(234,179,8,0.45)' : 'none',
                }} />
                {/* Percentage label */}
                <div style={{
                    position: 'absolute', right: '0.6rem', top: '50%', transform: 'translateY(-50%)',
                    fontSize: '0.65rem', fontWeight: 'bold',
                    color: pct > 55 ? 'rgba(0,0,0,0.65)' : 'rgba(255,255,255,0.45)',
                }}>
                    {lux != null ? `${Math.round(pct)}%` : ''}
                </div>
            </div>

            {/* Scale ticks */}
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.6rem', color: 'rgba(255,255,255,0.22)', paddingTop: '1px' }}>
                <span>Dark</span>
                <span>Office</span>
                <span>Overcast</span>
                <span>Full Sun →</span>
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
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.72rem', color: 'rgba(255,255,255,0.38)', textTransform: 'uppercase', letterSpacing: '1px' }}>
                Light Spectrum Split
            </span>

            {/* Split bar */}
            <div style={{
                position: 'relative', height: '16px', borderRadius: '8px',
                overflow: 'hidden', display: 'flex',
                border: '1px solid rgba(255,255,255,0.06)',
            }}>
                {/* Broadband (visible) slice */}
                <div style={{
                    width: `${bbPct}%`,
                    background: 'linear-gradient(90deg, #0369a1, #0ea5e9, #38bdf8)',
                    transition: 'width 0.9s ease',
                }} />
                {/* Infrared slice */}
                <div style={{
                    width: `${irPct}%`,
                    background: 'linear-gradient(90deg, #dc2626, #ef4444, #f87171)',
                    transition: 'width 0.9s ease',
                }} />
            </div>

            {/* Labels */}
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <div style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#38bdf8', flexShrink: 0 }} />
                    <span style={{ color: 'rgba(255,255,255,0.5)' }}>Broadband</span>
                    <span style={{ fontFamily: 'monospace', color: '#38bdf8', fontWeight: 'bold' }}>
                        {broadband ?? '--'}
                    </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <span style={{ fontFamily: 'monospace', color: '#f87171', fontWeight: 'bold' }}>
                        {infrared ?? '--'}
                    </span>
                    <span style={{ color: 'rgba(255,255,255,0.5)' }}>Infrared</span>
                    <div style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#f87171', flexShrink: 0 }} />
                </div>
            </div>
        </div>
    );
}

// ─── Main component ───────────────────────────────────────────────────────────
export default function TSL2561Monitor({ title = "Luminosity (TSL2561)" }) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

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
        const interval = setInterval(pollSensor, 10000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="glass-card" style={{ gridColumn: 'span 2' }}>
            {/* ── Header ── */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
                    <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#eab308', boxShadow: '0 0 8px #eab308' }} />
                    <h3 style={{ margin: 0 }}>☀️ {title}</h3>
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
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.4rem' }}>
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
