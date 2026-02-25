import { useState, useEffect } from 'react';
import { snapshotSensors } from '../api';

export default function SensorMonitor() {
    const [readings, setReadings] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const pollSensors = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await snapshotSensors(1, 5);
            setReadings(data.readings[0]);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        pollSensors();
        // Auto-poll every 10 seconds
        const interval = setInterval(pollSensors, 10000);
        return () => clearInterval(interval);
    }, []);

    const getVoltageColor = (volts) => {
        if (volts == null) return '#333';
        if (volts > 2.5) return 'var(--accent-red)'; // Dry
        if (volts < 1.0) return 'var(--accent-blue)'; // Wet
        return 'var(--accent-green)'; // Good
    };

    return (
        <div className="glass-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3>🌡️ Soil Sensors</h3>
                <button onClick={pollSensors} disabled={loading} style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}>
                    {loading ? 'Polling...' : 'Poll Now'}
                </button>
            </div>

            {error && <div style={{ color: 'var(--accent-red)', fontSize: '0.85rem', marginBottom: '1rem' }}>{error}</div>}

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
                {readings?.voltages ? (
                    readings.voltages.map((v, i) => (
                        <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Sensor {i}</div>
                            <div
                                style={{
                                    width: '100%',
                                    height: '100px',
                                    background: 'rgba(0,0,0,0.3)',
                                    borderRadius: '8px',
                                    position: 'relative',
                                    overflow: 'hidden',
                                    border: '1px solid var(--glass-border)'
                                }}
                            >
                                {/* Visual fill based on inverted voltage (lower V = wetter = fuller) */}
                                <div
                                    style={{
                                        position: 'absolute',
                                        bottom: 0,
                                        left: 0,
                                        width: '100%',
                                        height: `${Math.max(0, Math.min(100, (3.3 - v) / 3.3 * 100))}%`,
                                        background: getVoltageColor(v),
                                        transition: 'height 0.5s ease-in-out, background 0.5s ease'
                                    }}
                                />
                            </div>
                            <div style={{ fontWeight: 'bold' }}>{v == null ? '--' : v.toFixed(2)}V</div>
                        </div>
                    ))
                ) : (
                    <div style={{ gridColumn: 'span 4', textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                        No Data Available
                    </div>
                )}
            </div>

            {readings?.do_state && (
                <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', display: 'flex', justifyContent: 'space-between' }}>
                    <span>Digital Float Switch:</span>
                    <span style={{ fontWeight: 'bold', color: readings.do_state === 'WET' ? 'var(--accent-blue)' : 'var(--accent-red)' }}>
                        {readings.do_state}
                    </span>
                </div>
            )}
        </div>
    );
}
