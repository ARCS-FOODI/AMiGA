import { useState, useEffect } from 'react';
import { getScaleWeight, tareScale } from '../api';

export default function ScaleMonitor() {
    const [weight, setWeight] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const pollScale = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await getScaleWeight();
            setWeight(data.weight);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleTare = async () => {
        setLoading(true);
        setError(null);
        try {
            await tareScale();
            await pollScale();
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        pollScale();
        // Auto-poll every 5 seconds
        const interval = setInterval(pollScale, 5000);
        return () => clearInterval(interval);
    }, []);

    // Format weight strictly to 3 decimal places as requested
    const formattedWeight = weight !== null
        ? Number(weight).toFixed(3)
        : '--.---';

    return (
        <div className="glass-card" style={{ position: 'relative', overflow: 'hidden' }}>
            {loading && (
                <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '4px', background: 'var(--accent-purple)', animation: 'pulse 1s infinite' }} />
            )}

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3>⚖️ System Scale</h3>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <span className={`status-indicator ${weight !== null && !error ? 'status-online' : 'status-neutral'}`} style={{ backgroundColor: weight !== null && !error ? 'var(--accent-purple)' : '' }}></span>
                    <button onClick={pollScale} disabled={loading} style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}>
                        {loading ? 'Polling...' : 'Poll Now'}
                    </button>
                </div>
            </div>

            {error && <div style={{ color: 'var(--accent-red)', fontSize: '0.85rem', marginBottom: '1rem' }}>{error}</div>}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'center', padding: '1rem 0' }}>
                    <div style={{
                        fontSize: '3.5rem',
                        fontWeight: 'bold',
                        fontFamily: 'monospace',
                        color: weight !== null && weight < 0 ? 'var(--accent-red)' : 'var(--text-primary)',
                        textShadow: '0 0 20px rgba(255,255,255,0.1)'
                    }}>
                        {formattedWeight} <span style={{ fontSize: '1.5rem', color: 'var(--text-secondary)' }}>g</span>
                    </div>
                </div>

                <hr style={{ border: 'none', borderTop: '1px solid var(--glass-border)', margin: '0.25rem 0' }} />

                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-end' }}>
                    <div style={{ flex: 2, fontSize: '0.8rem', color: 'var(--text-secondary)', paddingBottom: '0.5rem' }}>
                        Calibrate Zero Point
                    </div>
                    <button
                        onClick={handleTare}
                        disabled={loading}
                        style={{ flex: 1 }}
                    >
                        Tare Scale
                    </button>
                </div>
            </div>
        </div>
    );
}
