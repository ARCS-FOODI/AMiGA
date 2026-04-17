import { useState, useEffect } from 'react';
import { getLightConfig, toggleLight, setLightConfig } from '../api';
import { POLL_INTERVALS } from '../polling';

export default function LightControl() {
    const [config, setConfig] = useState(null);
    const [editConfig, setEditConfig] = useState({ mode: 'manual', day_start: '19:00:00', day_end: '07:00:00' });
    const [loading, setLoading] = useState(true);

    const refreshLight = () => {
        getLightConfig()
            .then(data => {
                setConfig(data);
                // Only initialize editConfig if it's the very first load
                if (loading) {
                    setEditConfig({ mode: data.mode, day_start: data.day_start, day_end: data.day_end });
                }
            })
            .finally(() => setLoading(false));
    };

    useEffect(() => {
        refreshLight();
        const interval = setInterval(refreshLight, POLL_INTERVALS.STATUS); // polling for external schedule flips
        return () => clearInterval(interval);
    }, [loading]);

    const handleToggle = async () => {
        await toggleLight();
        refreshLight();
    };

    const handleConfigSave = async () => {
        await setLightConfig({
            mode: editConfig.mode,
            day_start: editConfig.day_start,
            day_end: editConfig.day_end
        });
        alert('Light Configuration Saved!');
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
                    <h4>Configuration</h4>
                    <label style={{ fontSize: '0.85rem' }}>Mode</label>
                    <select
                        value={editConfig.mode}
                        onChange={(e) => setEditConfig({ ...editConfig, mode: e.target.value })}
                        style={{ padding: '0.5rem', background: 'rgba(0,0,0,0.3)', color: 'white', border: '1px solid var(--glass-border)', borderRadius: '4px' }}
                    >
                        <option value="manual">Manual Only</option>
                        <option value="daynight">Day/Night Automation</option>
                    </select>

                    <div style={{ display: 'flex', gap: '1rem', opacity: editConfig.mode === 'manual' ? 0.3 : 1, pointerEvents: editConfig.mode === 'manual' ? 'none' : 'auto' }}>
                        <div style={{ flex: 1 }}>
                            <label style={{ fontSize: '0.85rem' }}>Turn ON</label>
                            <input type="time" value={editConfig.day_start.substring(0, 5)} onChange={(e) => setEditConfig({ ...editConfig, day_start: e.target.value + ':00' })} style={{ width: '100%' }} />
                        </div>
                        <div style={{ flex: 1 }}>
                            <label style={{ fontSize: '0.85rem' }}>Turn OFF</label>
                            <input type="time" value={editConfig.day_end.substring(0, 5)} onChange={(e) => setEditConfig({ ...editConfig, day_end: e.target.value + ':00' })} style={{ width: '100%' }} />
                        </div>
                    </div>

                    <button
                        onClick={handleConfigSave}
                        style={{ marginTop: '0.5rem' }}
                    >
                        Save Configuration
                    </button>

                    {/* Visual indicator of unsaved changes */}
                    {(editConfig.mode !== config.mode || editConfig.day_start !== config.day_start || editConfig.day_end !== config.day_end) && (
                        <span style={{ fontSize: '0.8rem', color: 'var(--accent-yellow)', marginTop: '-0.25rem' }}>
                            Unsaved changes
                        </span>
                    )}
                </div>
            </div>
        </div>
    );
}
