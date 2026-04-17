import { useState, useEffect } from 'react';
import { snapshotSIS } from '../api';

// ─── Arc Gauge (same geometry as SCD41Monitor) ────────────────────────────────
function ArcGauge({ value, min = 0, max, unit, label, size = 130, zones }) {
    const cx  = size * 0.5;
    const cy  = Math.round(size * 0.55);
    const r   = Math.round(size * 0.36);
    const sw  = Math.round(size * 0.085);

    const toRad = (d) => ((d - 90) * Math.PI) / 180;
    const pt    = (d) => ({
        x: +(cx + r * Math.cos(toRad(d))).toFixed(2),
        y: +(cy + r * Math.sin(toRad(d))).toFixed(2),
    });
    const arc = (from, to) => {
        const s = pt(from), e = pt(to);
        const sweep = ((to - from) + 360) % 360;
        return `M ${s.x} ${s.y} A ${r} ${r} 0 ${sweep > 180 ? 1 : 0} 1 ${e.x} ${e.y}`;
    };

    const START = 225, BG_END = 135;
    const pct   = value != null ? Math.max(0, Math.min(0.9999, (value - min) / (max - min))) : 0;
    const valDeg = (START + pct * 270) % 360;

    let color = '#10b981';
    if (zones && value != null) {
        for (const z of zones) {
            if (value <= z.max) { color = z.color; break; }
        }
    }

    const displayVal = value != null
        ? (typeof value === 'number' ? value.toFixed(1) : value)
        : '--';

    const viewH = Math.round(size * 0.88);
    return (
        <svg
            viewBox={`0 0 ${size} ${viewH}`}
            width={size} height={viewH}
            style={{ overflow: 'visible', display: 'block' }}
        >
            <path d={arc(START, BG_END)} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={sw} strokeLinecap="round" />
            {value != null && pct > 0.001 && (
                <path
                    d={arc(START, valDeg)}
                    fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round"
                    style={{ filter: `drop-shadow(0 0 6px ${color}bb)`, transition: 'stroke 0.5s ease' }}
                />
            )}
            <text x={cx} y={cy + 4} textAnchor="middle" fill="white"
                fontSize={size * 0.175} fontWeight="bold" fontFamily="monospace">
                {displayVal}
            </text>
            <text x={cx} y={cy + size * 0.145} textAnchor="middle"
                fill="rgba(255,255,255,0.4)" fontSize={size * 0.096} fontFamily="Inter, sans-serif">
                {unit}
            </text>
            <text x={cx} y={Math.round(size * 0.77)} textAnchor="middle"
                fill="rgba(255,255,255,0.28)" fontSize={size * 0.086} fontFamily="Inter, sans-serif">
                {label}
            </text>
        </svg>
    );
}

// ─── NPK horizontal bar ───────────────────────────────────────────────────────
function NPKBar({ label, value, max, color, unit = 'mg/kg' }) {
    const pct = value != null ? Math.min(100, (value / max) * 100) : 0;
    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
            <span style={{
                width: '16px', textAlign: 'center',
                fontSize: '0.82rem', fontWeight: 'bold',
                color, fontFamily: 'monospace', flexShrink: 0,
            }}>{label}</span>

            <div style={{
                flex: 1, position: 'relative', height: '13px',
                background: 'rgba(0,0,0,0.35)', borderRadius: '7px',
                overflow: 'hidden', border: '1px solid rgba(255,255,255,0.06)',
            }}>
                <div style={{
                    position: 'absolute', top: 0, left: 0, height: '100%',
                    width: `${pct}%`,
                    background: color,
                    borderRadius: '7px',
                    transition: 'width 0.9s ease',
                    boxShadow: `0 0 8px ${color}80`,
                }} />
            </div>

            <span style={{
                width: '90px', textAlign: 'right', flexShrink: 0,
                fontFamily: 'monospace', fontSize: '0.82rem',
                color: 'rgba(255,255,255,0.65)',
            }}>
                {value != null ? `${value} ${unit}` : '--'}
            </span>
        </div>
    );
}

// ─── Zone-dot status indicator ────────────────────────────────────────────────
function ZoneDot({ value, zones }) {
    if (value == null) return (
        <div style={{ width: '7px', height: '7px', borderRadius: '50%', background: 'rgba(255,255,255,0.12)', flexShrink: 0 }} />
    );
    let color = '#10b981';
    for (const z of zones) { if (value <= z.max) { color = z.color; break; } }
    return (
        <div style={{ width: '7px', height: '7px', borderRadius: '50%', background: color, boxShadow: `0 0 5px ${color}`, flexShrink: 0 }} />
    );
}

// ─── Metric tile with zone dot ────────────────────────────────────────────────
function MetricTile({ label, value, unit, zones }) {
    const displayVal = value != null
        ? (typeof value === 'number' ? value.toFixed(1) : value)
        : '--';

    return (
        <div style={{
            display: 'flex', flexDirection: 'column',
            background: 'rgba(255,255,255,0.04)',
            padding: '0.7rem', borderRadius: '8px',
            border: '1px solid rgba(255,255,255,0.06)',
            gap: '0.3rem',
        }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                {zones && <ZoneDot value={value} zones={zones} />}
                <span style={{
                    fontSize: '0.68rem', color: 'rgba(255,255,255,0.38)',
                    textTransform: 'uppercase', letterSpacing: '0.4px',
                }}>{label}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.3rem' }}>
                <span style={{ fontFamily: 'monospace', fontSize: '1.05rem', fontWeight: 'bold', color: 'white' }}>
                    {displayVal}
                </span>
                <span style={{ fontSize: '0.68rem', color: 'rgba(255,255,255,0.38)' }}>{unit}</span>
            </div>
        </div>
    );
}

// ─── Legend dot row ───────────────────────────────────────────────────────────
const LegendRow = ({ items }) => (
    <div style={{ display: 'flex', gap: '0.55rem', flexWrap: 'wrap', justifyContent: 'center' }}>
        {items.map((z, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '2px', fontSize: '0.58rem', color: 'rgba(255,255,255,0.28)' }}>
                <div style={{ width: '5px', height: '5px', borderRadius: '50%', background: z.color, flexShrink: 0 }} />
                {z.label}
            </div>
        ))}
    </div>
);

// ─── Zone configs ─────────────────────────────────────────────────────────────
const PH_ZONES = [
    { max: 5.5,      color: '#ef4444' }, // too acidic
    { max: 6.0,      color: '#eab308' }, // borderline
    { max: 7.0,      color: '#10b981' }, // optimal
    { max: 7.5,      color: '#eab308' }, // borderline alkaline
    { max: Infinity, color: '#ef4444' }, // too alkaline
];

const MOISTURE_ZONES = [
    { max: 30,       color: '#ef4444' },
    { max: 70,       color: '#10b981' },
    { max: Infinity, color: '#0ea5e9' },
];

const TEMP_ZONES = [
    { max: 15,       color: '#0ea5e9' },
    { max: 28,       color: '#10b981' },
    { max: Infinity, color: '#ef4444' },
];

const EC_ZONES = [
    { max: 200,      color: '#0ea5e9' },
    { max: 2000,     color: '#10b981' },
    { max: Infinity, color: '#eab308' },
];

// ─── Main component ───────────────────────────────────────────────────────────
export default function SISMonitor({ title = "SIS - Soil Integrated Sensor", port = null, slaveId = null }) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const pollSensor = async () => {
        setLoading(true);
        setError(null);
        try {
            const result = await snapshotSIS({ port, slave_id: slaveId });
            setData(result);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        let timeoutId;
        let isMounted = true;
        const routine = async () => {
            if (!isMounted) return;
            await pollSensor();
            if (isMounted) timeoutId = setTimeout(routine, 10000);
        };
        routine();
        return () => { isMounted = false; clearTimeout(timeoutId); };
    }, []);

    return (
        <div className="glass-card" style={{ gridColumn: 'span 2' }}>
            {/* ── Header ── */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
                    <div style={{
                        width: '10px', height: '10px', borderRadius: '50%',
                        background: data?.simulated ? 'var(--accent-yellow)' : 'var(--accent-green)',
                        boxShadow: '0 0 8px var(--accent-green)',
                    }} />
                    <h3 style={{ margin: 0 }}>🌱 {title}</h3>
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

            {/* ── Top row: pH gauge + secondary metrics ── */}
            <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', alignItems: 'center', marginBottom: '1.5rem' }}>

                {/* pH Arc Gauge */}
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.25rem' }}>
                    <ArcGauge
                        value={data?.ph}
                        min={4} max={9}
                        unit="pH" label="Acidity"
                        size={135}
                        zones={PH_ZONES}
                    />
                    <LegendRow items={[
                        { label: 'Acid',    color: '#ef4444' },
                        { label: 'Low',     color: '#eab308' },
                        { label: 'Optimal', color: '#10b981' },
                        { label: 'High',    color: '#eab308' },
                        { label: 'Base',    color: '#ef4444' },
                    ]} />
                </div>

                {/* Moisture / Temp / EC tiles */}
                <div style={{
                    flex: 1, display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))',
                    gap: '0.7rem', minWidth: '220px',
                }}>
                    <MetricTile label="Moisture"    value={data?.moisture}    unit="%"     zones={MOISTURE_ZONES} />
                    <MetricTile label="Temperature" value={data?.temperature} unit="°C"    zones={TEMP_ZONES} />
                    <MetricTile label="Conductivity" value={data?.ec}          unit="μS/cm" zones={EC_ZONES} />
                </div>
            </div>

            {/* ── NPK Macronutrient bars ── */}
            <div style={{
                background: 'rgba(0,0,0,0.22)', borderRadius: '10px',
                border: '1px solid rgba(255,255,255,0.05)',
                padding: '1rem',
                display: 'flex', flexDirection: 'column', gap: '0.8rem',
            }}>
                <div style={{ fontSize: '0.68rem', color: 'rgba(255,255,255,0.32)', textTransform: 'uppercase', letterSpacing: '1px' }}>
                    Macronutrient Profile (NPK)
                </div>
                <NPKBar label="N" value={data?.nitrogen}   max={300} color="#10b981" />
                <NPKBar label="P" value={data?.phosphorus} max={200} color="#0ea5e9" />
                <NPKBar label="K" value={data?.potassium}  max={400} color="var(--accent-orange)" />
            </div>

            {/* ── Footer ── */}
            <div style={{ marginTop: '1rem', textAlign: 'right', fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
                Last update: <span style={{ color: 'var(--text-primary)' }}>{data?.timestamp?.split(' ')[1] || '--:--:--'}</span>
            </div>
        </div>
    );
}
