import { useState, useEffect, useRef } from 'react';
import { getScaleWeight, tareScale, getScaleBundles } from '../api';

// Polling interval in ms — configurable between 500ms and 1000ms
const POLL_INTERVAL_MS = 1000;
const HISTORY_LENGTH = 20;

// Compute trend arrow from recent history (slope over last 5 points)
function getTrend(history) {
    if (!history || history.length < 3) return null;
    const recent = history.slice(-5);
    const slope  = (recent[recent.length - 1] - recent[0]) / recent.length;
    if (slope >  0.05) return { symbol: '↑', color: '#10b981', label: 'Increasing' };
    if (slope < -0.05) return { symbol: '↓', color: '#eab308', label: 'Decreasing' };
    return { symbol: '→', color: 'rgba(255,255,255,0.35)', label: 'Stable' };
}

export default function ScaleMonitor() {
    const [weight, setWeight] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [history, setHistory] = useState([]);
    const [bundleHistory, setBundleHistory] = useState([]);
    const historyRef = useRef([]);

    const pollLiveScale = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await getScaleWeight();
            const w = data.weight;
            setWeight(w);

            // Update history for live sparkline
            const updated = [...historyRef.current, w].slice(-HISTORY_LENGTH);
            historyRef.current = updated;
            setHistory(updated);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const pollBundleHistory = async () => {
        try {
            const bundleData = await getScaleBundles();
            if (bundleData && bundleData.history) {
                const averages = bundleData.history.map(b => b.average);
                setBundleHistory(averages);
            }
        } catch (err) {
            console.error("Failed to fetch bundle history:", err);
        }
    };

    const handleTare = async () => {
        setLoading(true);
        setError(null);
        try {
            await tareScale();
            // Reset history after tare since the baseline changed
            historyRef.current = [];
            setHistory([]);
            await pollLiveScale();
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleManualPoll = () => {
        pollLiveScale();
        pollBundleHistory();
    };

    useEffect(() => {
        pollLiveScale();
        pollBundleHistory();

        const liveInterval = setInterval(pollLiveScale, POLL_INTERVAL_MS);
        const bundleInterval = setInterval(pollBundleHistory, 20000);

        return () => {
            clearInterval(liveInterval);
            clearInterval(bundleInterval);
        };
    }, []);

    // Format weight strictly to 3 decimal places
    const formattedWeight = weight !== null
        ? Number(weight).toFixed(3)
        : '--.---';

    const trend = getTrend(history);

    return (
        <div className="glass-card" style={{ position: 'relative', overflow: 'hidden' }}>
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
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3>⚖️ US Solid Scale</h3>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <span
                        className={`status-indicator ${weight !== null && !error ? 'status-online' : 'status-neutral'}`}
                        style={{ backgroundColor: weight !== null && !error ? 'var(--accent-purple)' : '' }}
                    ></span>
                    <button onClick={handleManualPoll} disabled={loading} style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}>
                        {loading ? 'Polling...' : 'Poll Now'}
                    </button>
                </div>
            </div>

            {/* Error display */}
            {error && <div style={{ color: 'var(--accent-red)', fontSize: '0.85rem', marginBottom: '1rem' }}>{error}</div>}

            {/* Dual Column Layout */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '2rem' }}>

                {/* Left Column: Live Scale */}
                <div style={{ flex: '1 1 300px', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {/* Weight readout + trend arrow */}
                    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'baseline', gap: '0.8rem', padding: '1rem 0' }}>
                        <div style={{
                            fontSize: '3.5rem',
                            fontWeight: 'bold',
                            fontFamily: 'monospace',
                            color: weight !== null && weight < 0 ? 'var(--accent-red)' : 'var(--text-primary)',
                            textShadow: '0 0 20px rgba(255,255,255,0.1)'
                        }}>
                            {formattedWeight} <span style={{ fontSize: '1.5rem', color: 'var(--text-secondary)' }}>g</span>
                        </div>
                        {/* Trend arrow */}
                        {trend && (
                            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2px' }}>
                                <span style={{
                                    fontSize: '1.6rem', fontWeight: 'bold',
                                    color: trend.color,
                                    textShadow: `0 0 10px ${trend.color}88`,
                                    transition: 'color 0.4s ease',
                                    lineHeight: 1,
                                }}>{trend.symbol}</span>
                                <span style={{ fontSize: '0.55rem', color: trend.color, opacity: 0.7, letterSpacing: '0.3px' }}>
                                    {trend.label}
                                </span>
                            </div>
                        )}
                    </div>

                    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '-0.5rem' }}>Live Graph</div>
                    <Sparkline data={history} />

                    <hr style={{ border: 'none', borderTop: '1px solid var(--glass-border)', margin: '0.25rem 0' }} />

                    {/* Tare section */}
                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-end' }}>
                        <div style={{ flex: 2, fontSize: '0.8rem', color: 'var(--text-secondary)', paddingBottom: '0.5rem' }}>
                            Calibrate Zero Point
                        </div>
                        <button
                            className="purple"
                            onClick={handleTare}
                            disabled={loading}
                            style={{ flex: 1 }}
                        >
                            Tare Scale
                        </button>
                    </div>
                </div>

                {/* Right Column: Bundle Averages */}
                <div style={{ flex: '1 1 300px', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    <div style={{
                        background: 'rgba(0,0,0,0.15)',
                        padding: '1rem',
                        borderRadius: '8px',
                        border: '1px solid var(--glass-border)',
                        height: '100%',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'center',
                        gap: '1rem'
                    }}>
                        <div style={{ textAlign: 'center' }}>
                            <h4 style={{ margin: '0 0 0.5rem 0', color: 'var(--text-primary)' }}>Telemetry Bundle Averages</h4>
                            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Historical averages of recent 20-point bundles</div>
                        </div>

                        <div style={{ flexGrow: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                            <Sparkline data={bundleHistory} />
                        </div>

                        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textAlign: 'right' }}>
                            {bundleHistory.length > 0 ? `Showing last ${bundleHistory.length} bundles` : 'Awaiting data...'}
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
}


/**
 * Sparkline — Inline SVG mini-chart showing the last N weight readings.
 * Renders a smooth polyline with a gradient fill beneath it.
 */
function Sparkline({ data }) {
    if (!data || data.length < 2) {
        return (
            <div style={{
                height: '60px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.8rem',
                color: 'var(--text-secondary)',
                background: 'rgba(0,0,0,0.2)',
                borderRadius: '8px',
                border: '1px solid var(--glass-border)'
            }}>
                Collecting data...
            </div>
        );
    }

    const width = 280;
    const height = 60;
    const padding = 4;

    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1; // avoid division by zero

    const points = data.map((val, i) => {
        const x = padding + (i / (data.length - 1)) * (width - 2 * padding);
        const y = height - padding - ((val - min) / range) * (height - 2 * padding);
        return `${x},${y}`;
    });

    const polyline = points.join(' ');
    // Fill area: close path along the bottom
    const fillPath = `${points.join(' ')} ${width - padding},${height - padding} ${padding},${height - padding}`;

    return (
        <div style={{
            background: 'rgba(0,0,0,0.2)',
            borderRadius: '8px',
            border: '1px solid var(--glass-border)',
            padding: '0.25rem',
            overflow: 'hidden'
        }}>
            <svg
                viewBox={`0 0 ${width} ${height}`}
                width="100%"
                height="60"
                preserveAspectRatio="none"
                style={{ display: 'block' }}
            >
                <defs>
                    <linearGradient id="sparkFill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="var(--accent-purple)" stopOpacity="0.4" />
                        <stop offset="100%" stopColor="var(--accent-purple)" stopOpacity="0.05" />
                    </linearGradient>
                </defs>
                {/* Filled area */}
                <polygon
                    points={fillPath}
                    fill="url(#sparkFill)"
                />
                {/* Line */}
                <polyline
                    points={polyline}
                    fill="none"
                    stroke="var(--accent-purple)"
                    strokeWidth="2"
                    strokeLinejoin="round"
                    strokeLinecap="round"
                />
                {/* Current value dot */}
                {(() => {
                    const lastPoint = points[points.length - 1].split(',');
                    return (
                        <circle
                            cx={lastPoint[0]}
                            cy={lastPoint[1]}
                            r="3"
                            fill="var(--accent-purple)"
                            style={{ filter: 'drop-shadow(0 0 4px rgba(139, 92, 246, 0.6))' }}
                        />
                    );
                })()}
            </svg>
        </div>
    );
}
