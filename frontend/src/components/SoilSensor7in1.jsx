import { useState, useEffect } from 'react';
import { snapshotNPKSensors } from '../api';

export default function SoilSensor7in1() {
    const [readings, setReadings] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Health thresholds
    const thresholds = {
        ph_min: 5.5,
        ph_max: 8.5,
        moisture_min: 20,
        moisture_max: 80,
        temp_min: 15,
        temp_max: 30,
        ec_max: 2000,
        nitrogen_min: 10,
        phosphorus_min: 5,
        potassium_min: 100,
    };

    const pollSensors = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await snapshotNPKSensors();
            if (data.status === 'error') {
                setError(data.error || 'Failed to read sensor');
                // Keep showing last readings even on error
            } else if (data.readings) {
                setReadings(data.readings);
                setError(null);
            } else {
                setError('No sensor data received');
            }
        } catch (err) {
            setError(err.message || 'Connection error');
            // Keep last readings displayed
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        pollSensors();
        // Auto-poll every 15 seconds
        const interval = setInterval(pollSensors, 15000);
        return () => clearInterval(interval);
    }, []);

    // Get color based on parameter and value
    const getParameterColor = (param, value) => {
        if (value === null || value === undefined) return '#666';

        switch (param) {
            case 'ph':
                if (value < thresholds.ph_min) return 'var(--accent-red)'; // Acidic
                if (value > thresholds.ph_max) return 'var(--accent-blue)'; // Alkaline
                return 'var(--accent-green)'; // Optimal

            case 'moisture':
                if (value < thresholds.moisture_min) return 'var(--accent-red)'; // Dry
                if (value > thresholds.moisture_max) return 'var(--accent-blue)'; // Wet
                return 'var(--accent-green)'; // Optimal

            case 'temperature':
                if (value < thresholds.temp_min) return 'var(--accent-blue)'; // Cold
                if (value > thresholds.temp_max) return 'var(--accent-red)'; // Hot
                return 'var(--accent-green)'; // Optimal

            case 'ec':
                if (value > thresholds.ec_max) return 'var(--accent-red)'; // High
                if (value > thresholds.ec_max * 0.5) return '#f59e0b'; // Yellow (moderate)
                return 'var(--accent-green)'; // Good

            case 'nitrogen':
            case 'phosphorus':
            case 'potassium':
                const min = thresholds[`${param}_min`];
                if (value < min) return 'var(--accent-red)'; // Deficient
                if (value < min * 1.5) return '#f59e0b'; // Yellow (moderate)
                return 'var(--accent-green)'; // Good

            default:
                return 'var(--accent-green)';
        }
    };

    // Format value with appropriate decimal places
    const formatValue = (param, value) => {
        if (value === null || value === undefined) return '--';
        
        if (param === 'ph' || param === 'moisture' || param === 'temperature') {
            return value.toFixed(1);
        }
        return Math.round(value).toString();
    };

    // Get unit for parameter
    const getUnit = (param) => {
        const units = {
            ph: '',
            moisture: '%',
            temperature: '°C',
            ec: 'µs/cm',
            nitrogen: 'mg/kg',
            phosphorus: 'mg/kg',
            potassium: 'mg/kg',
        };
        return units[param] || '';
    };

    // Get display name for parameter
    const getDisplayName = (param) => {
        const names = {
            ph: 'pH',
            moisture: 'Moisture',
            temperature: 'Temp',
            ec: 'EC',
            nitrogen: 'Nitrogen',
            phosphorus: 'Phosphorus',
            potassium: 'Potassium',
        };
        return names[param] || param;
    };

    // Get emoji for parameter
    const getEmoji = (param) => {
        const emojis = {
            ph: '⚗️',
            moisture: '💧',
            temperature: '🌡️',
            ec: '⚡',
            nitrogen: '🟢',
            phosphorus: '🔵',
            potassium: '🟡',
        };
        return emojis[param] || '📊';
    };

    // Parameter order for display
    const parameterOrder = ['ph', 'moisture', 'temperature', 'ec', 'nitrogen', 'phosphorus', 'potassium'];

    if (!readings && loading) {
        return <div className="glass-card">Loading Soil Sensor Data...</div>;
    }

    if (!readings) {
        return (
            <div className="glass-card" style={{ color: 'var(--accent-red)' }}>
                {error ? `⚠️ ${error}` : 'Backend Offline or Unreachable.'}
            </div>
        );
    }

    return (
        <div className="glass-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <h3 style={{ fontSize: '1rem', margin: 0 }}>🌱 7-in-1 Soil Sensor</h3>
                <button 
                    onClick={pollSensors} 
                    disabled={loading} 
                    style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                >
                    {loading ? 'Updating...' : 'Refresh'}
                </button>
            </div>

            {error && (
                <div style={{ color: 'var(--accent-red)', fontSize: '0.75rem', marginBottom: '0.75rem' }}>
                    ⚠️ {error}
                </div>
            )}

            {/* Parameters Grid - 4 columns like SensorMonitor */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: '0.75rem', width: '100%' }}>
                {parameterOrder.map((param) => {
                    const value = readings[param];
                    const color = getParameterColor(param, value);
                    const formattedValue = formatValue(param, value);
                    const unit = getUnit(param);
                    const displayName = getDisplayName(param);
                    const emoji = getEmoji(param);

                    return (
                        <div
                            key={param}
                            style={{
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '0.3rem',
                                padding: '0.6rem',
                                width: '100%',
                                maxWidth: '100%',
                                height: '100px',
                                background: 'rgba(0,0,0,0.2)',
                                border: `2px solid ${color}`,
                                borderRadius: '8px',
                                transition: 'all 0.3s ease',
                                boxSizing: 'border-box',
                            }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.transform = 'translateY(-2px)';
                                e.currentTarget.style.boxShadow = `0 0 15px ${color}50`;
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.transform = 'translateY(0)';
                                e.currentTarget.style.boxShadow = 'none';
                            }}
                        >
                            <div style={{ fontSize: '1.2rem' }}>{emoji}</div>
                            <div style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', textAlign: 'center', fontWeight: '500' }}>
                                {displayName}
                            </div>
                            <div
                                style={{
                                    fontSize: '1rem',
                                    fontWeight: 'bold',
                                    color: color,
                                    textShadow: `0 0 6px ${color}40`,
                                }}
                            >
                                {formattedValue}
                            </div>
                            <div style={{ fontSize: '0.6rem', color: 'var(--text-secondary)' }}>{unit}</div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

