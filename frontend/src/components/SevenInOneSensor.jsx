import { useState, useEffect } from 'react';

// Mock data generator for the 7-in-1 sensor
const generateMockData = () => ({
    moisture: (Math.random() * 30 + 40).toFixed(1), // 40-70%
    temp: (Math.random() * 5 + 20).toFixed(1), // 20-25 C
    ec: Math.floor(Math.random() * 200 + 800), // 800-1000 us/cm
    ph: (Math.random() * 1.5 + 5.5).toFixed(1), // 5.5-7.0
    nitrogen: Math.floor(Math.random() * 50 + 100), // 100-150 mg/kg
    phosphorus: Math.floor(Math.random() * 20 + 40), // 40-60 mg/kg
    potassium: Math.floor(Math.random() * 80 + 150), // 150-230 mg/kg
});

export default function SevenInOneSensor() {
    const [readings, setReadings] = useState(null);
    const [loading, setLoading] = useState(false);

    const pollSensors = async () => {
        setLoading(true);
        // Simulate network delay
        setTimeout(() => {
            setReadings(generateMockData());
            setLoading(false);
        }, 600);
    };

    useEffect(() => {
        pollSensors();
        const interval = setInterval(pollSensors, 10000);
        return () => clearInterval(interval);
    }, []);

    const MetricCard = ({ label, value, unit, icon, color }) => (
        <div style={{
            background: 'rgba(0,0,0,0.2)',
            borderRadius: '12px',
            padding: '1rem',
            border: '1px solid var(--glass-border)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '0.5rem',
            transition: 'transform 0.2s',
            cursor: 'default'
        }}
            onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
            onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
        >
            <div style={{ fontSize: '1.5rem', color: color }}>{icon}</div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', fontWeight: 500 }}>{label}</div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.25rem' }}>
                <span style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--text-primary)' }}>
                    {value || '--'}
                </span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{unit}</span>
            </div>
        </div>
    );

    const NPKBar = ({ label, value, max, color }) => {
        const percentage = Math.min(100, Math.max(0, (value / max) * 100));
        return (
            <div style={{ marginBottom: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem', fontSize: '0.85rem' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>{label}</span>
                    <span style={{ fontWeight: 'bold' }}>{value || '--'} mg/kg</span>
                </div>
                <div style={{
                    width: '100%',
                    height: '8px',
                    background: 'rgba(0,0,0,0.3)',
                    borderRadius: '4px',
                    overflow: 'hidden',
                    border: '1px solid var(--glass-border)'
                }}>
                    <div style={{
                        width: `${percentage}%`,
                        height: '100%',
                        background: color,
                        transition: 'width 1s ease-out',
                        boxShadow: `0 0 10px ${color}80`
                    }} />
                </div>
            </div>
        );
    };

    return (
        <div className="glass-card" style={{ position: 'relative', overflow: 'hidden' }}>
            {loading && (
                <div style={{
                    position: 'absolute', top: 0, left: 0,
                    width: '100%', height: '4px',
                    background: 'var(--accent-green)',
                    animation: 'pulse 1s infinite'
                }} />
            )}

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    🌱 7-in-1 Soil Sensor
                    <span style={{
                        fontSize: '0.7rem',
                        padding: '0.2rem 0.5rem',
                        background: 'rgba(16, 185, 129, 0.2)',
                        color: 'var(--accent-green)',
                        borderRadius: '12px',
                        fontWeight: 'bold'
                    }}>MOCK DATA</span>
                </h3>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <span
                        className={`status-indicator ${readings ? 'status-online' : 'status-neutral'}`}
                        style={{ backgroundColor: readings ? 'var(--accent-green)' : '' }}
                    ></span>
                    <button className="success" onClick={pollSensors} disabled={loading} style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}>
                        {loading ? 'Refreshing...' : 'Refresh'}
                    </button>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
                <MetricCard
                    label="Moisture"
                    value={readings?.moisture}
                    unit="%"
                    icon="💧"
                    color="var(--accent-blue)"
                />
                <MetricCard
                    label="Temperature"
                    value={readings?.temp}
                    unit="°C"
                    icon="🌡️"
                    color="var(--accent-red)"
                />
                <MetricCard
                    label="pH Level"
                    value={readings?.ph}
                    unit="pH"
                    icon="🧪"
                    color="var(--accent-purple)"
                />
                <MetricCard
                    label="Conductivity"
                    value={readings?.ec}
                    unit="µS/cm"
                    icon="⚡"
                    color="var(--accent-yellow)"
                />
            </div>

            <div style={{
                background: 'rgba(0,0,0,0.15)',
                padding: '1.5rem',
                borderRadius: '12px',
                border: '1px solid var(--glass-border)'
            }}>
                <h4 style={{ marginBottom: '1rem', color: 'var(--text-primary)', fontSize: '0.95rem' }}>NPK Nutrients</h4>
                <NPKBar
                    label="Nitrogen (N)"
                    value={readings?.nitrogen}
                    max={250}
                    color="var(--accent-green)"
                />
                <NPKBar
                    label="Phosphorus (P)"
                    value={readings?.phosphorus}
                    max={100}
                    color="var(--accent-blue)"
                />
                <NPKBar
                    label="Potassium (K)"
                    value={readings?.potassium}
                    max={300}
                    color="var(--accent-yellow)"
                />
            </div>
        </div>
    );
}
