import { useState, useEffect } from 'react';
import { getLightConfig, toggleLight, setLightConfig } from '../api';

export default function LightControl() {
    const [config, setConfig] = useState(null);
    const [loading, setLoading] = useState(true);

    const refreshLight = () => {
        getLightConfig()
            .then(setConfig)
            .finally(() => setLoading(false));
    };

    useEffect(() => {
        refreshLight();
        const interval = setInterval(refreshLight, 5000); // polling for external schedule flips
        return () => clearInterval(interval);
    }, []);

    const handleToggle = async () => {
        await toggleLight();
        refreshLight();
    };

    const handleConfigSave = async () => {
        await setLightConfig({
            mode: config.mode,
            day_start: config.day_start,
            day_end: config.day_end
        });
        alert('Light Schedule Saved!');
        refreshLight();
    };

    if (loading) return <div className="glass-card">Loading Light Config...</div>;
    if (!config) return <div className="glass-card" style={{ color: 'var(--accent-red)' }}>Backend Offline or Unreachable. Retrying...</div>;

    const isOn = config?.state?.on;

    return (
        <div className="glass-card" style={{
            boxShadow: isOn ? '0 0 25px rgba(234, 179, 8, 0.15)' : 'var(--glass-shadow)',
            border: isOn ? '1px solid rgba(234, 179, 8, 0.4)' : '1px solid var(--glass-border)'
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3>💡 Grow Light</h3>
                <span style={{ fontSize: '0.9rem', color: isOn ? 'var(--accent-yellow)' : 'var(--text-secondary)' }}>
                    {isOn ? 'ACTIVE (ON)' : 'STANDBY (OFF)'}
                </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <button
                    onClick={handleToggle}
                    style={{
                        padding: '1rem',
                        background: isOn ? 'linear-gradient(135deg, #ca8a04, #eab308)' : '#2a2a35'
                    }}
                >
                    {isOn ? 'Turn Light OFF' : 'Turn Light ON'}
                </button>

                <hr style={{ border: 'none', borderTop: '1px solid var(--glass-border)', margin: '0.5rem 0' }} />

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    <h4>Schedule Settings</h4>
                    <label style={{ fontSize: '0.85rem' }}>Mode</label>
                    <select
                        value={config.mode}
                        onChange={(e) => setConfig({ ...config, mode: e.target.value })}
                        style={{ padding: '0.5rem', background: 'rgba(0,0,0,0.3)', color: 'white', border: '1px solid var(--glass-border)', borderRadius: '4px' }}
                    >
                        <option value="manual">Manual Only</option>
                        <option value="daynight">Day/Night Automation</option>
                    </select>

                    <div style={{ display: 'flex', gap: '1rem' }}>
                        <div style={{ flex: 1 }}>
                            <label style={{ fontSize: '0.85rem' }}>Turn ON</label>
                            <input type="time" value={config.day_start.substring(0, 5)} onChange={(e) => setConfig({ ...config, day_start: e.target.value + ':00' })} style={{ width: '100%' }} />
                        </div>
                        <div style={{ flex: 1 }}>
                            <label style={{ fontSize: '0.85rem' }}>Turn OFF</label>
                            <input type="time" value={config.day_end.substring(0, 5)} onChange={(e) => setConfig({ ...config, day_end: e.target.value + ':00' })} style={{ width: '100%' }} />
                        </div>
                    </div>

                    <button onClick={handleConfigSave} style={{ marginTop: '0.5rem' }}>Save Schedule</button>
                </div>
            </div>
        </div>
    );
}
