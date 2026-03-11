import { useState, useEffect } from 'react';
import { getScaleWeight } from '../api';

export default function ScaleMonitor() {
    const [weightData, setWeightData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const pollScale = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await getScaleWeight();
            setWeightData(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        pollScale();
        // Since backend contiguous thread fetches non-blocking, we can poll frequently
        const interval = setInterval(pollScale, 1000);
        return () => clearInterval(interval);
    }, []);

    const hasData = weightData && weightData.weight !== null;

    return (
        <div className="glass-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3>⚖️ U.S. Solid Scale</h3>
                <button onClick={pollScale} disabled={loading} style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}>
                    {loading ? 'Polling...' : 'Poll Now'}
                </button>
            </div>

            {error && <div style={{ color: 'var(--accent-red)', fontSize: '0.85rem', marginBottom: '1rem' }}>{error}</div>}

            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '120px', padding: '1rem' }}>
                {hasData ? (
                    <>
                        <div style={{ fontSize: '3rem', fontWeight: 'bold', color: 'var(--accent-blue)', textShadow: '0 0 10px rgba(59, 130, 246, 0.5)' }}>
                            {weightData.weight.toFixed(2)}
                            <span style={{ fontSize: '1.5rem', color: 'var(--text-secondary)', marginLeft: '0.5rem' }}>
                                {weightData.unit || 'g'}
                            </span>
                        </div>
                        {weightData.simulated && (
                            <div style={{ fontSize: '0.75rem', color: 'var(--accent-red)', marginTop: '0.5rem', background: 'rgba(255, 0, 0, 0.1)', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>
                                SIMULATION MODE
                            </div>
                        )}
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                            Port: {weightData.port}
                        </div>
                    </>
                ) : (
                    <div style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
                        {loading && !weightData ? 'Initializing Connection...' : 'No Data Available'}
                    </div>
                )}
            </div>
        </div>
    );
}
