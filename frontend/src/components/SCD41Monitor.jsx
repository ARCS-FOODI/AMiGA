import { useState, useEffect } from 'react';
import { snapshotSCD41 } from '../api';

// ─── Arc Gauge — pure SVG ────────────────────────────────────────────────────
// Opens 7-o'clock → 5-o'clock (225°→135° CW from top), sweeping 270° through 12.
function ArcGauge({ value, min = 0, max, unit, label, size = 140, zones }) {
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

    const START  = 225;
    const BG_END = 135;
    const pct    = value != null ? Math.max(0, Math.min(0.9999, (value - min) / (max - min))) : 0;
    const valDeg = (START + pct * 270) % 360;

    let color = '#10b981';
    if (zones && value != null) {
        for (const z of zones) { if (value <= z.max) { color = z.color; break; } }
    }

    const displayVal = value != null
        ? (Number.isInteger(value) ? value : value.toFixed(1))
        : '--';

    const viewH = Math.round(size * 0.88);

    return (
        <svg
            viewBox={`0 0 ${size} ${viewH}`}
            width={size} height={viewH}
            style={{ overflow: 'visible', display: 'block' }}
        >
            {/* Track */}
            <path d={arc(START, BG_END)} fill="none"
                stroke="rgba(255,255,255,0.08)" strokeWidth={sw} strokeLinecap="round" />
            {/* Value arc */}
            {value != null && pct > 0.001 && (
                <path d={arc(START, valDeg)} fill="none"
                    stroke={color} strokeWidth={sw} strokeLinecap="round"
                    style={{ filter: `drop-shadow(0 0 7px ${color}cc)`, transition: 'stroke 0.5s ease' }}
                />
            )}
            {/* Value */}
            <text x={cx} y={cy + 4} textAnchor="middle" fill="white"
                fontSize={size * 0.175} fontWeight="bold" fontFamily="monospace">
                {displayVal}
            </text>
            {/* Unit */}
            <text x={cx} y={cy + size * 0.148} textAnchor="middle"
                fill="rgba(255,255,255,0.42)" fontSize={size * 0.096} fontFamily="Inter, sans-serif">
                {unit}
            </text>
            {/* Label */}
            <text x={cx} y={Math.round(size * 0.78)} textAnchor="middle"
                fill="rgba(255,255,255,0.26)" fontSize={size * 0.085} fontFamily="Inter, sans-serif">
                {label}
            </text>
        </svg>
    );
}

// ─── Zone configs ─────────────────────────────────────────────────────────────
const CO2_ZONES = [
    { max: 500,      color: '#14b8a6' }, // ambient — teal
    { max: 900,      color: '#10b981' }, // optimal — green
    { max: 1400,     color: '#eab308' }, // elevated — amber
    { max: Infinity, color: '#ef4444' }, // alert — red
];

const TEMP_ZONES_C = [
    { max: 15,       color: '#0ea5e9' },
    { max: 28,       color: '#10b981' },
    { max: Infinity, color: '#ef4444' },
];
const TEMP_ZONES_F = [
    { max: 59,       color: '#0ea5e9' }, // <15 °C
    { max: 82.4,     color: '#10b981' }, // 15–28 °C
    { max: Infinity, color: '#ef4444' },
];

const HUM_ZONES = [
    { max: 30,       color: '#ef4444' },
    { max: 70,       color: '#10b981' },
    { max: Infinity, color: '#0ea5e9' },
];

// ─── Legend dot row ───────────────────────────────────────────────────────────
const LegendRow = ({ items }) => (
    <div style={{ display: 'flex', gap: '0.55rem', flexWrap: 'wrap', justifyContent: 'center' }}>
        {items.map((z, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.59rem', color: 'rgba(255,255,255,0.3)' }}>
                <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: z.color, flexShrink: 0 }} />
                {z.label}
            </div>
        ))}
    </div>
);

// ─── °C / °F segmented toggle ────────────────────────────────────────────────
const UnitToggle = ({ useFahrenheit, onToggle }) => (
    <div style={{
        display: 'inline-flex', borderRadius: '20px',
        background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)',
        overflow: 'hidden',
    }}>
        {['°C', '°F'].map((u) => {
            const active = (u === '°F') === useFahrenheit;
            return (
                <button key={u} onClick={onToggle} style={{
                    padding: '3px 10px', border: 'none', cursor: 'pointer',
                    background: active ? 'rgba(14,165,233,0.3)' : 'transparent',
                    color: active ? '#38bdf8' : 'rgba(255,255,255,0.35)',
                    fontFamily: 'monospace', fontWeight: 'bold', fontSize: '0.66rem',
                    transition: 'all 0.2s ease',
                }}>{u}</button>
            );
        })}
    </div>
);

// ─── Main component ───────────────────────────────────────────────────────────
export default function SCD41Monitor({ title = "Environmental Condition (SCD41)" }) {
    const [data,          setData]         = useState(null);
    const [loading,       setLoading]      = useState(false);
    const [error,         setError]        = useState(null);
    const [useFahrenheit, setFahrenheit]   = useState(false);

    const pollSensor = async () => {
        setLoading(true);
        setError(null);
        try {
            const result = await snapshotSCD41();
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

    // ── Temperature conversion ──
    const tempC       = data?.temperature;
    const tempDisplay = useFahrenheit && tempC != null ? +(tempC * 9 / 5 + 32).toFixed(1) : tempC;
    const tempMin     = useFahrenheit ? 32   : 0;
    const tempMax     = useFahrenheit ? 113  : 45;
    const tempZones   = useFahrenheit ? TEMP_ZONES_F : TEMP_ZONES_C;
    const tempUnit    = useFahrenheit ? '°F' : '°C';

    // ── Card background tint based on CO2 alert level ──
    const co2Tint = data?.co2 > 1400 ? 'rgba(239,68,68,0.04)'
                  : data?.co2 > 900  ? 'rgba(234,179,8,0.03)'
                  : 'transparent';

    return (
        <div className="glass-card" style={{ gridColumn: 'span 2', background: `rgba(22,22,28,0.6)`, backgroundImage: `radial-gradient(ellipse at top, ${co2Tint}, transparent 70%)`, transition: 'background-image 1s ease' }}>

            {/* ── Header ── */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
                    <div style={{
                        width: '10px', height: '10px', borderRadius: '50%',
                        background: data?.simulated ? 'var(--accent-yellow)' : 'var(--accent-blue)',
                        boxShadow: '0 0 8px var(--accent-blue)',
                    }} />
                    <h3 style={{ margin: 0 }}>☁️ {title}</h3>
                    {data?.simulated && (
                        <span style={{
                            fontSize: '0.65rem', fontWeight: 'bold', padding: '2px 8px', borderRadius: '20px',
                            background: 'rgba(234,179,8,0.15)', color: 'var(--accent-yellow)',
                            border: '1px solid rgba(234,179,8,0.4)',
                        }}>SIMULATED</span>
                    )}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.7rem' }}>
                    <UnitToggle useFahrenheit={useFahrenheit} onToggle={() => setFahrenheit(f => !f)} />
                    <button onClick={pollSensor} disabled={loading} className="btn-secondary">
                        {loading ? 'Reading...' : 'Refresh'}
                    </button>
                </div>
            </div>

            {error && (
                <div style={{ color: 'var(--accent-red)', fontSize: '0.85rem', marginBottom: '1rem', padding: '0.5rem', background: 'rgba(239,68,68,0.1)', borderRadius: '4px' }}>⚠️ {error}</div>
            )}

            {/* ── Gauge Row: Temp | ── CO₂ ── | Humidity ── */}
            <div style={{
                display: 'flex',
                alignItems: 'flex-end',
                justifyContent: 'space-evenly',
                gap: '0.75rem',
                flexWrap: 'wrap',
                paddingBottom: '0.5rem',
            }}>

                {/* Temperature */}
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.35rem' }}>
                    <span style={{ fontSize: '0.66rem', color: 'rgba(255,255,255,0.3)', textTransform: 'uppercase', letterSpacing: '0.8px' }}>
                        Temperature
                    </span>
                    <ArcGauge
                        value={tempDisplay}
                        min={tempMin} max={tempMax}
                        unit={tempUnit} label=""
                        size={135}
                        zones={tempZones}
                    />
                    <LegendRow items={[
                        { label: 'Cold', color: '#0ea5e9' },
                        { label: 'Good', color: '#10b981' },
                        { label: 'Hot',  color: '#ef4444' },
                    ]} />
                </div>

                {/* CO₂ — large focal gauge */}
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.3rem' }}>
                    <span style={{ fontSize: '0.66rem', color: 'rgba(255,255,255,0.3)', textTransform: 'uppercase', letterSpacing: '1px' }}>
                        CO₂ Concentration
                    </span>
                    <ArcGauge
                        value={data?.co2}
                        min={0} max={2000}
                        unit="ppm" label="CO₂"
                        size={230}
                        zones={CO2_ZONES}
                    />
                    <LegendRow items={[
                        { label: 'Ambient',  color: '#14b8a6' },
                        { label: 'Optimal',  color: '#10b981' },
                        { label: 'Elevated', color: '#eab308' },
                        { label: 'Alert',    color: '#ef4444' },
                    ]} />
                </div>

                {/* Humidity */}
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.35rem' }}>
                    <span style={{ fontSize: '0.66rem', color: 'rgba(255,255,255,0.3)', textTransform: 'uppercase', letterSpacing: '0.8px' }}>
                        Humidity
                    </span>
                    <ArcGauge
                        value={data?.humidity}
                        min={0} max={100}
                        unit="%" label=""
                        size={135}
                        zones={HUM_ZONES}
                    />
                    <LegendRow items={[
                        { label: 'Dry',  color: '#ef4444' },
                        { label: 'Good', color: '#10b981' },
                        { label: 'Wet',  color: '#0ea5e9' },
                    ]} />
                </div>
            </div>

            {/* ── Footer ── */}
            <div style={{ marginTop: '1rem', textAlign: 'right', fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
                Last update: <span style={{ color: 'var(--text-primary)' }}>{data?.timestamp?.split(' ')[1] || '--:--:--'}</span>
            </div>
        </div>
    );
}
