import { useState, useEffect } from 'react';
import { snapshotTSL2561 } from '../api';

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

    const Metric = ({ label, value, unit, color }) => (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            background: 'rgba(255,255,255,0.05)',
            padding: '0.8rem',
            borderRadius: '8px',
            border: '1px solid var(--glass-border)'
        }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>{label}</span>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.2rem' }}>
                <span style={{ fontSize: '1.2rem', fontWeight: 'bold', color: color || 'var(--text-primary)' }}>{value}</span>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>{unit}</span>
            </div>
        </div>
    );

    return (
        <div className="glass-card" style={{ gridColumn: 'span 2' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
                    <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: data?.simulated ? 'var(--accent-yellow)' : '#eab308', boxShadow: '0 0 8px #eab308' }}></div>
                    <h3 style={{ margin: 0 }}>☀️ {title}</h3>
                </div>
                <button
                    onClick={pollSensor}
                    disabled={loading}
                    className="btn-secondary"
                    style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}
                >
                    {loading ? 'Reading...' : 'Refresh'}
                </button>
            </div>

            {error && <div style={{ color: 'var(--accent-red)', fontSize: '0.85rem', marginBottom: '1rem', padding: '0.5rem', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '4px' }}>⚠️ {error}</div>}

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
                <Metric label="Lux" value={data?.lux ?? '--'} unit="lx" color="#eab308" />
                <Metric label="Broadband" value={data?.broadband ?? '--'} unit="val" color="var(--accent-green)" />
                <Metric label="Infrared" value={data?.infrared ?? '--'} unit="val" color="var(--accent-red)" />

                <div style={{
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                    padding: '0.8rem',
                    fontSize: '0.7rem',
                    color: 'var(--text-secondary)'
                }}>
                    <span>Last Update:</span>
                    <span style={{ color: 'var(--text-primary)' }}>{data?.timestamp?.split(' ')[1] || '--:--:--'}</span>
                    {data?.simulated && <span style={{ color: 'var(--accent-yellow)', marginTop: '0.2rem' }}>SIMULATED MODE</span>}
                </div>
            </div>
        </div>
    );
}
