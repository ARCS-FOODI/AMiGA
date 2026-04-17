import { useState, useEffect } from 'react';
import { snapshotSensors } from '../api';

// ─── Helpers ──────────────────────────────────────────────────────────────────
// Capacitive soil sensor: ~3.3V = dry (0%), ~1.0V = saturated (100%)
const voltageToMoisture = (v) => {
    if (v == null) return null;
    return Math.max(0, Math.min(100, ((3.3 - v) / 2.3) * 100));
};

const getSensorStatus = (v) => {
    if (v == null) return 'unknown';
    if (v > 2.5)   return 'dry';
    if (v < 1.0)   return 'wet';
    return 'ok';
};

const STATUS_COLOR = {
    dry:     '#ef4444',
    wet:     '#0ea5e9',
    ok:      '#10b981',
    unknown: 'rgba(255,255,255,0.15)',
};

const STATUS_LABEL = {
    dry:     'Dry',
    wet:     'Sat.',
    ok:      'Good',
    unknown: '—',
};

// ─── Single channel column ────────────────────────────────────────────────────
function ChannelBar({ index, voltage }) {
    const status   = getSensorStatus(voltage);
    const color    = STATUS_COLOR[status];
    const moisture = voltageToMoisture(voltage);
    // Fill visual: lower V = wetter = taller fill
    const fillPct  = voltage != null ? Math.max(0, Math.min(100, ((3.3 - voltage) / 3.3) * 100)) : 0;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.4rem' }}>
            {/* Channel label */}
            <div style={{ fontSize: '0.72rem', color: 'rgba(255,255,255,0.38)', fontFamily: 'monospace' }}>
                CH{index}
            </div>

            {/* Fill bar */}
            <div style={{
                width: '100%', height: '96px',
                background: 'rgba(0,0,0,0.35)', borderRadius: '8px',
                position: 'relative', overflow: 'hidden',
                border: `1px solid ${color}40`,
                transition: 'border-color 0.5s ease',
            }}>
                {/* Liquid fill */}
                <div style={{
                    position: 'absolute', bottom: 0, left: 0, width: '100%',
                    height: `${fillPct}%`,
                    background: color,
                    transition: 'height 0.6s ease-in-out, background 0.5s ease',
                    boxShadow: `0 0 12px ${color}55`,
                }} />
                {/* Moisture % overlay */}
                {moisture != null && (
                    <div style={{
                        position: 'absolute', top: '50%', left: '50%',
                        transform: 'translate(-50%, -50%)',
                        fontSize: '0.8rem', fontWeight: '700',
                        color: 'rgba(255,255,255,0.92)',
                        textShadow: '0 1px 4px rgba(0,0,0,0.9)',
                        fontFamily: 'monospace',
                        zIndex: 1,
                        pointerEvents: 'none',
                    }}>
                        {Math.round(moisture)}%
                    </div>
                )}
            </div>

            {/* Voltage */}
            <div style={{ fontSize: '0.78rem', fontWeight: 'bold', fontFamily: 'monospace', color }}>
                {voltage != null ? voltage.toFixed(2) : '--'}V
            </div>

            {/* Status label */}
            <div style={{
                fontSize: '0.62rem', color,
                textTransform: 'uppercase', letterSpacing: '0.4px', fontWeight: '600',
            }}>
                {STATUS_LABEL[status]}
            </div>
        </div>
    );
}

// ─── Main component ───────────────────────────────────────────────────────────
export default function SensorMonitor({ title = "Soil Sensors", addr = 0x48 }) {
    const [readings, setReadings] = useState(null);
    const [loading,  setLoading]  = useState(false);
    const [error,    setError]    = useState(null);

    const pollSensors = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await snapshotSensors({ addr, samples: 1, avg: 5 });
            setReadings(data.readings[0]);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        pollSensors();
        const interval = setInterval(pollSensors, 10000);
        return () => clearInterval(interval);
    }, []);

    // Dynamic card border based on worst sensor
    const voltages = readings?.voltages || [];
    const statuses = voltages.map(getSensorStatus);
    const hasDry   = statuses.includes('dry');
    const hasWet   = statuses.includes('wet');

    const cardBorder = hasDry
        ? 'rgba(239,68,68,0.55)'
        : hasWet
            ? 'rgba(14,165,233,0.45)'
            : voltages.length > 0
                ? 'rgba(16,185,129,0.3)'
                : 'rgba(255,255,255,0.06)';

    const cardGlow = hasDry
        ? '0 0 22px rgba(239,68,68,0.14)'
        : hasWet
            ? '0 0 22px rgba(14,165,233,0.12)'
            : 'none';

    return (
        <div className="glass-card" style={{
            border: `1px solid ${cardBorder}`,
            boxShadow: cardGlow,
            transition: 'border-color 0.5s ease, box-shadow 0.5s ease',
        }}>
            {/* ── Header ── */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ margin: 0 }}>🌡️ {title}</h3>
                <button onClick={pollSensors} disabled={loading} style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}>
                    {loading ? 'Polling...' : 'Poll Now'}
                </button>
            </div>

            {error && (
                <div style={{ color: 'var(--accent-red)', fontSize: '0.85rem', marginBottom: '1rem' }}>{error}</div>
            )}

            {/* ── Channel columns ── */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.75rem' }}>
                {readings?.voltages ? (
                    readings.voltages.map((v, i) => (
                        <ChannelBar key={i} index={i} voltage={v} />
                    ))
                ) : (
                    <div style={{ gridColumn: 'span 4', textAlign: 'center', padding: '2.5rem', color: 'var(--text-secondary)' }}>
                        No Data Available
                    </div>
                )}
            </div>

            {/* ── Legend ── */}
            {readings?.voltages && (
                <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', marginTop: '0.75rem', flexWrap: 'wrap' }}>
                    {[
                        { label: 'Dry  (>2.5V)',    color: '#ef4444' },
                        { label: 'Good (1.0–2.5V)', color: '#10b981' },
                        { label: 'Sat. (<1.0V)',    color: '#0ea5e9' },
                    ].map((z, i) => (
                        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.62rem', color: 'rgba(255,255,255,0.3)' }}>
                            <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: z.color, flexShrink: 0 }} />
                            {z.label}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
