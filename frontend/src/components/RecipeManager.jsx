import { useState, useEffect } from 'react';
import { getRecipe, getRecipeStatus, saveRecipe, getRecipeTemplate } from '../api';
import { POLL_INTERVALS } from '../polling';

export default function RecipeManager() {
    const [recipe, setRecipe] = useState(null);
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);
    const [isExpanded, setIsExpanded] = useState(false);

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchStatus, POLL_INTERVALS.STATUS);
        return () => clearInterval(interval);
    }, []);

    const fetchData = async () => {
        try {
            const [rData, sData] = await Promise.all([getRecipe(), getRecipeStatus()]);
            setRecipe(rData);
            setStatus(sData);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const fetchStatus = async () => {
        try {
            const sData = await getRecipeStatus();
            setStatus(sData);
        } catch (err) {
            // silent
        }
    };

    const handleSave = async () => {
        setSaving(true);
        setError(null);
        try {
            await saveRecipe(recipe);
            await fetchData();
        } catch (err) {
            setError(err.message);
        } finally {
            setSaving(false);
        }
    };

    const handleAddPhase = () => {
        const lastPhase = recipe.phases?.[recipe.phases.length - 1];
        const newStart = lastPhase ? lastPhase.day_end + 1 : 0;
        const newPhase = {
            name: `Phase ${recipe.phases?.length + 1 || 1}`,
            day_start: newStart,
            day_end: newStart + 7,
            lighting: { mode: 'daynight', on_time: '06:00', off_time: '20:00' },
            fluid_control: { 
                trigger: 'moisture', 
                sensor_override: false,
                pump: 'water', 
                dry_threshold_v: 4.0, 
                priming_v: 2.5,
                super_dry_v: 5.3,
                vote_k: 2,
                dose_ml: 50, 
                hz: 10000, 
                cooldown_minutes: 60,
                irrigate_at: [],
                interval_hours: 24
            }
        };
        setRecipe({
            ...recipe,
            phases: [...(recipe.phases || []), newPhase]
        });
    };

    const handleRemovePhase = (idx) => {
        const newPhases = recipe.phases.filter((_, i) => i !== idx);
        setRecipe({ ...recipe, phases: newPhases });
    };

    const handleResetToTemplate = async () => {
        if (!window.confirm("Overwrite current recipe with system default template?")) return;
        try {
            setSaving(true);
            const template = await getRecipeTemplate();
            setRecipe(template);
            setError(null);
        } catch (err) {
            setError("Failed to load template: " + err.message);
        } finally {
            setSaving(false);
        }
    };

    if (loading) return <div className="glass-card">Loading Recipe Manager...</div>;
    if (!recipe) return <div className="glass-card">No recipe found. Initialize backend first.</div>;

    const daemonActive = status?.active;

    return (
        <div className="glass-card" style={{ 
            borderColor: daemonActive ? 'var(--accent-purple)' : 'var(--glass-border)', 
            boxShadow: daemonActive ? '0 0 15px rgba(168, 85, 247, 0.15)' : 'var(--glass-shadow)',
            transition: 'all 0.3s ease'
        }}>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
                    <h3 style={{ margin: 0, color: 'var(--accent-purple)' }}>⚙️ Recipe Settings</h3>
                    <div style={{ 
                        fontSize: '0.7rem', 
                        padding: '0.2rem 0.5rem', 
                        background: daemonActive ? 'rgba(168, 85, 247, 0.2)' : 'rgba(255,255,255,0.05)',
                        borderRadius: '10px',
                        color: daemonActive ? 'var(--accent-purple)' : 'var(--text-secondary)'
                    }}>
                        {daemonActive ? 'ACTIVE' : 'IDLE'}
                    </div>
                </div>
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    <button 
                        className="secondary" 
                        onClick={() => setIsExpanded(!isExpanded)} 
                        style={{ 
                            padding: '0.4rem 0.8rem', 
                            fontSize: '0.85rem',
                            background: isExpanded ? 'rgba(255,255,255,0.1)' : 'transparent',
                            borderColor: isExpanded ? 'var(--accent-purple)' : 'var(--glass-border)'
                        }}
                    >
                        {isExpanded ? 'Close Config' : 'Configure Recipe'}
                    </button>
                    {isExpanded && (
                        <button className="primary" onClick={handleSave} disabled={saving} style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem', background: 'var(--accent-purple)', color: 'black' }}>
                            {saving ? 'Saving...' : 'Save Changes'}
                        </button>
                    )}
                </div>
            </div>

            {error && <div style={{ color: 'var(--accent-red)', marginBottom: '1rem', padding: '0.5rem', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '4px' }}>⚠️ {error}</div>}

            {/* Quick Stats (Always Visible) */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem', marginBottom: isExpanded ? '2rem' : '0' }}>
                <div style={{ background: 'rgba(255,255,255,0.02)', padding: '0.8rem', borderRadius: '8px' }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>CURRENT RECIPE</div>
                    <div style={{ fontWeight: 'bold' }}>{recipe.name || 'Unnamed'}</div>
                </div>
                <div style={{ background: 'rgba(255,255,255,0.02)', padding: '0.8rem', borderRadius: '8px' }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>GROWTH DAY</div>
                    <div style={{ fontWeight: 'bold' }}>Day {status?.current_day || 0}</div>
                </div>
                <div style={{ background: 'rgba(255,255,255,0.02)', padding: '0.8rem', borderRadius: '8px' }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>ACTIVE PHASE</div>
                    <div style={{ fontWeight: 'bold', color: 'var(--accent-teal)' }}>{status?.phase?.name || 'None'}</div>
                </div>
            </div>

            {isExpanded && (
                <div style={{ marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid var(--glass-border)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                        <div style={{ flex: 1 }}>
                            <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Recipe Name</label>
                            <input 
                                type="text" 
                                value={recipe.name || ''} 
                                onChange={e => setRecipe({...recipe, name: e.target.value})}
                                style={{ width: '100%', maxWidth: '400px', fontSize: '1.1rem', fontWeight: 'bold', background: 'transparent', border: 'none', borderBottom: '2px solid var(--accent-purple)' }}
                            />
                        </div>
                        <div style={{ display: 'flex', gap: '0.8rem' }}>
                            <button className="secondary" onClick={() => fetchData()} style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem' }}>Reload</button>
                            <button className="secondary" onClick={handleResetToTemplate} style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem', color: 'var(--accent-purple)' }}>Reset to Default</button>
                        </div>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        <h4 style={{ margin: 0, borderBottom: '1px solid var(--glass-border)', paddingBottom: '0.5rem' }}>Growth Phases</h4>
                        {recipe.phases?.map((phase, idx) => (
                            <div key={idx} style={{ background: 'rgba(255,255,255,0.02)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
                                    <div style={{ background: 'var(--accent-purple)', color: 'black', padding: '0.2rem 0.6rem', borderRadius: '4px', fontWeight: 'bold', fontSize: '0.8rem' }}>
                                        Day {phase.day_start} - {phase.day_end}
                                    </div>
                                    <input 
                                        type="text" 
                                        value={phase.name || ''}
                                        onChange={e => {
                                            const newPhases = [...recipe.phases];
                                            newPhases[idx].name = e.target.value;
                                            setRecipe({...recipe, phases: newPhases});
                                        }}
                                        style={{ flex: 1, minWidth: '200px', background: 'transparent', border: 'none', borderBottom: '1px solid var(--glass-border)', fontSize: '1rem', color: 'var(--accent-teal)' }}
                                    />
                                    <button 
                                        onClick={() => handleRemovePhase(idx)}
                                        style={{ background: 'rgba(239, 68, 68, 0.1)', color: 'var(--accent-red)', border: '1px solid rgba(239, 68, 68, 0.2)', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.7rem' }}
                                    >
                                        Remove
                                    </button>
                                </div>

                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem' }}>
                                    <div>
                                        <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Lighting Mode</label>
                                        <select 
                                            value={phase.lighting?.mode || 'off'}
                                            onChange={e => {
                                                const newPhases = [...recipe.phases];
                                                newPhases[idx].lighting.mode = e.target.value;
                                                setRecipe({...recipe, phases: newPhases});
                                            }}
                                            style={{ width: '100%', marginBottom: '0.5rem' }}
                                        >
                                            <option value="off">Always OFF (Blackout)</option>
                                            <option value="on">Always ON</option>
                                            <option value="daynight">Day/Night Cycle</option>
                                        </select>
                                        {phase.lighting?.mode === 'daynight' && (
                                            <div style={{ display: 'flex', gap: '0.5rem' }}>
                                                <input type="time" value={phase.lighting.on_time || '06:00'} onChange={e => { const np=[...recipe.phases]; np[idx].lighting.on_time=e.target.value; setRecipe({...recipe, phases: np}); }} style={{ flex: 1 }} />
                                                <input type="time" value={phase.lighting.off_time || '20:00'} onChange={e => { const np=[...recipe.phases]; np[idx].lighting.off_time=e.target.value; setRecipe({...recipe, phases: np}); }} style={{ flex: 1 }} />
                                            </div>
                                        )}
                                    </div>

                                    <div style={{ flex: 1.5 }}>
                                        <div style={{ marginBottom: '1rem' }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                                                <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Irrigation Mode</label>
                                                {phase.fluid_control?.trigger === 'moisture' && status?.current_voltages && status.current_voltages.length > 0 && (
                                                    <div style={{ fontSize: '0.7rem', color: 'var(--accent-teal)' }}>
                                                        Live Avg: {(status.current_voltages.reduce((a,b)=>a+b,0)/status.current_voltages.length).toFixed(2)}V
                                                    </div>
                                                )}
                                            </div>
                                            <div style={{ display: 'flex', background: 'rgba(0,0,0,0.2)', padding: '0.2rem', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.05)' }}>
                                                <button
                                                    onClick={() => {
                                                        const newPhases = [...recipe.phases];
                                                        newPhases[idx].fluid_control.trigger = 'moisture';
                                                        setRecipe({...recipe, phases: newPhases});
                                                    }}
                                                    style={{
                                                        flex: 1,
                                                        padding: '0.4rem',
                                                        fontSize: '0.75rem',
                                                        border: 'none',
                                                        borderRadius: '4px',
                                                        background: (phase.fluid_control?.trigger || 'moisture') === 'moisture' ? 'var(--accent-purple)' : 'transparent',
                                                        color: (phase.fluid_control?.trigger || 'moisture') === 'moisture' ? 'black' : 'var(--text-secondary)',
                                                        fontWeight: (phase.fluid_control?.trigger || 'moisture') === 'moisture' ? 'bold' : 'normal',
                                                        cursor: 'pointer',
                                                        transition: 'all 0.2s',
                                                    }}
                                                >
                                                    💧 Moisture Sensors
                                                </button>
                                                <button
                                                    onClick={() => {
                                                        const newPhases = [...recipe.phases];
                                                        newPhases[idx].fluid_control.trigger = 'scheduled';
                                                        setRecipe({...recipe, phases: newPhases});
                                                    }}
                                                    style={{
                                                        flex: 1,
                                                        padding: '0.4rem',
                                                        fontSize: '0.75rem',
                                                        border: 'none',
                                                        borderRadius: '4px',
                                                        background: phase.fluid_control?.trigger === 'scheduled' ? 'var(--accent-purple)' : 'transparent',
                                                        color: phase.fluid_control?.trigger === 'scheduled' ? 'black' : 'var(--text-secondary)',
                                                        fontWeight: phase.fluid_control?.trigger === 'scheduled' ? 'bold' : 'normal',
                                                        cursor: 'pointer',
                                                        transition: 'all 0.2s',
                                                    }}
                                                >
                                                    ⏱ Time Scheduled
                                                </button>
                                            </div>
                                        </div>

                                        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.8rem' }}>
                                            <select 
                                                value={phase.fluid_control?.pump || 'water'}
                                                onChange={e => { const np=[...recipe.phases]; np[idx].fluid_control.pump=e.target.value; setRecipe({...recipe, phases: np}); }}
                                                style={{ flex: 1 }}
                                            >
                                                <option value="water">Water Pump</option>
                                                <option value="food">Food Pump</option>
                                            </select>

                                            {phase.fluid_control?.trigger === 'moisture' && (
                                                <button 
                                                    onClick={() => {
                                                        const np = [...recipe.phases];
                                                        np[idx].fluid_control.sensor_override = !np[idx].fluid_control.sensor_override;
                                                        setRecipe({...recipe, phases: np});
                                                    }}
                                                    style={{ 
                                                        fontSize: '0.7rem', 
                                                        padding: '0.4rem 0.8rem', 
                                                        borderRadius: '4px',
                                                        background: phase.fluid_control?.sensor_override ? 'rgba(245, 158, 11, 0.2)' : 'rgba(255,255,255,0.05)',
                                                        borderColor: phase.fluid_control?.sensor_override ? 'rgba(245, 158, 11, 0.5)' : 'var(--glass-border)',
                                                        color: phase.fluid_control?.sensor_override ? '#f59e0b' : 'var(--text-secondary)',
                                                        transition: 'all 0.2s',
                                                        whiteSpace: 'nowrap'
                                                    }}
                                                >
                                                    {phase.fluid_control?.sensor_override ? '⚠️ Sensor Override ON' : 'Sensor Override OFF'}
                                                </button>
                                            )}
                                        </div>

                                        {phase.fluid_control?.trigger === 'moisture' ? (
                                            <>
                                                <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.8rem' }}>
                                                    <div style={{ display: 'flex', alignItems: 'center', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--glass-border)', borderRadius: '4px', padding: '0 0.5rem', flex: 1 }}>
                                                        <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginRight: '0.5rem' }}>&gt;</span>
                                                        <input 
                                                            type="number" 
                                                            step="0.1" 
                                                            value={phase.fluid_control?.dry_threshold_v || 4.0} 
                                                            onChange={e => { const np=[...recipe.phases]; np[idx].fluid_control.dry_threshold_v=parseFloat(e.target.value); setRecipe({...recipe, phases: np}); }}
                                                            style={{ width: '100%', background: 'transparent', border: 'none', padding: '0.4rem 0' }}
                                                        />
                                                        <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>V</span>
                                                    </div>
                                                    <div style={{ display: 'flex', alignItems: 'center', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--glass-border)', borderRadius: '4px', padding: '0 0.5rem', flex: 0.6 }}>
                                                        <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginRight: '0.3rem' }}>K:</span>
                                                        <input 
                                                            type="number" 
                                                            value={phase.fluid_control?.vote_k || 2} 
                                                            onChange={e => { const np=[...recipe.phases]; np[idx].fluid_control.vote_k=parseInt(e.target.value); setRecipe({...recipe, phases: np}); }}
                                                            style={{ width: '100%', background: 'transparent', border: 'none', padding: '0.4rem 0' }}
                                                        />
                                                    </div>
                                                </div>

                                                {/* Calibration Row */}
                                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: '0.5rem', marginBottom: '1.2rem' }}>
                                                    <div style={{ display: 'flex', alignItems: 'center', background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '4px', padding: '0 0.5rem' }}>
                                                        <span style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', width: '45px' }}>Primed:</span>
                                                        <input 
                                                            type="number" 
                                                            step="0.1"
                                                            value={phase.fluid_control?.priming_v || 2.5} 
                                                            onChange={e => { const np=[...recipe.phases]; np[idx].fluid_control.priming_v=parseFloat(e.target.value); setRecipe({...recipe, phases: np}); }}
                                                            style={{ width: '100%', background: 'transparent', border: 'none', fontSize: '0.75rem', padding: '0.3rem 0' }}
                                                        />
                                                        <span style={{ fontSize: '0.65rem', color: 'var(--text-secondary)' }}>V</span>
                                                    </div>
                                                    <div style={{ display: 'flex', alignItems: 'center', background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '4px', padding: '0 0.5rem' }}>
                                                        <span style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', width: '45px' }}>Dry:</span>
                                                        <input 
                                                            type="number" 
                                                            step="0.1"
                                                            value={phase.fluid_control?.super_dry_v || 5.3} 
                                                            onChange={e => { const np=[...recipe.phases]; np[idx].fluid_control.super_dry_v=parseFloat(e.target.value); setRecipe({...recipe, phases: np}); }}
                                                            style={{ width: '100%', background: 'transparent', border: 'none', fontSize: '0.75rem', padding: '0.3rem 0' }}
                                                        />
                                                        <span style={{ fontSize: '0.65rem', color: 'var(--text-secondary)' }}>V</span>
                                                    </div>
                                                    <button 
                                                        className="secondary" 
                                                        onClick={() => {
                                                            const p = phase.fluid_control?.priming_v || 2.5;
                                                            const d = phase.fluid_control?.super_dry_v || 5.3;
                                                            const midway = (p + d) / 2;
                                                            const np = [...recipe.phases];
                                                            np[idx].fluid_control.dry_threshold_v = parseFloat(midway.toFixed(2));
                                                            setRecipe({...recipe, phases: np});
                                                        }}
                                                        style={{ fontSize: '0.65rem', padding: '0.2rem 0.5rem' }}
                                                    >
                                                        Set 50%
                                                    </button>
                                                </div>
                                            </>
                                        ) : (
                                            <div style={{ marginBottom: '1.2rem' }}>
                                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                                                    <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Irrigate At (Clock Time)</label>
                                                    <button 
                                                        className="secondary" 
                                                        onClick={() => {
                                                            const np = [...recipe.phases];
                                                            const times = np[idx].fluid_control.irrigate_at || [];
                                                            np[idx].fluid_control.irrigate_at = [...times, "08:00"];
                                                            setRecipe({...recipe, phases: np});
                                                        }}
                                                        style={{ fontSize: '0.65rem', padding: '0.1rem 0.4rem' }}
                                                    >
                                                        + Add Time
                                                    </button>
                                                </div>
                                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginBottom: '0.8rem' }}>
                                                    {(phase.fluid_control?.irrigate_at || []).map((timeStr, tIdx) => (
                                                        <div key={tIdx} style={{ display: 'flex', alignItems: 'center', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--glass-border)', borderRadius: '4px', padding: '0 0.3rem' }}>
                                                            <input 
                                                                type="time" 
                                                                value={timeStr} 
                                                                onChange={e => {
                                                                    const np = [...recipe.phases];
                                                                    np[idx].fluid_control.irrigate_at[tIdx] = e.target.value;
                                                                    setRecipe({...recipe, phases: np});
                                                                }}
                                                                style={{ background: 'transparent', border: 'none', color: 'white', fontSize: '0.8rem', padding: '0.2rem' }}
                                                            />
                                                            <button 
                                                                onClick={() => {
                                                                    const np = [...recipe.phases];
                                                                    np[idx].fluid_control.irrigate_at.splice(tIdx, 1);
                                                                    setRecipe({...recipe, phases: np});
                                                                }}
                                                                style={{ background: 'transparent', border: 'none', color: 'var(--accent-red)', padding: '0 0.2rem', cursor: 'pointer' }}
                                                            >
                                                                ✕
                                                            </button>
                                                        </div>
                                                    ))}
                                                    {(!phase.fluid_control?.irrigate_at || phase.fluid_control.irrigate_at.length === 0) && (
                                                        <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', fontStyle: 'italic', padding: '0.4rem' }}>No times set. Using interval instead.</div>
                                                    )}
                                                </div>

                                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', opacity: phase.fluid_control?.irrigate_at?.length > 0 ? 0.5 : 1 }}>
                                                    <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>Fallback Interval:</label>
                                                    <div style={{ display: 'flex', alignItems: 'center', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--glass-border)', borderRadius: '4px', padding: '0 0.5rem', flex: 1 }}>
                                                        <input 
                                                            type="number" 
                                                            step="0.5"
                                                            value={phase.fluid_control?.interval_hours || 24} 
                                                            onChange={e => { const np=[...recipe.phases]; np[idx].fluid_control.interval_hours=parseFloat(e.target.value); setRecipe({...recipe, phases: np}); }}
                                                            style={{ width: '100%', background: 'transparent', border: 'none', padding: '0.4rem 0' }}
                                                            disabled={phase.fluid_control?.irrigate_at?.length > 0}
                                                        />
                                                        <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>hrs</span>
                                                    </div>
                                                </div>
                                            </div>
                                        )}

                                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--glass-border)', borderRadius: '4px', padding: '0 0.5rem', flex: 1 }}>
                                                <input 
                                                    type="number" 
                                                    value={phase.fluid_control?.dose_ml || 50} 
                                                    onChange={e => { const np=[...recipe.phases]; np[idx].fluid_control.dose_ml=parseFloat(e.target.value); setRecipe({...recipe, phases: np}); }}
                                                    style={{ width: '100%', background: 'transparent', border: 'none', padding: '0.4rem 0' }}
                                                />
                                                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>mL</span>
                                            </div>
                                            <div style={{ display: 'flex', alignItems: 'center', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--glass-border)', borderRadius: '4px', padding: '0 0.5rem', flex: 1 }}>
                                                <input 
                                                    type="number" 
                                                    value={phase.fluid_control?.hz || 10000} 
                                                    onChange={e => { const np=[...recipe.phases]; np[idx].fluid_control.hz=parseFloat(e.target.value); setRecipe({...recipe, phases: np}); }}
                                                    style={{ width: '100%', background: 'transparent', border: 'none', padding: '0.4rem 0' }}
                                                />
                                                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Hz</span>
                                            </div>
                                            <div style={{ display: 'flex', alignItems: 'center', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--glass-border)', borderRadius: '4px', padding: '0 0.5rem', flex: 1 }}>
                                                <input 
                                                    type="number" 
                                                    value={phase.fluid_control?.cooldown_minutes || 60} 
                                                    onChange={e => { const np=[...recipe.phases]; np[idx].fluid_control.cooldown_minutes=parseInt(e.target.value); setRecipe({...recipe, phases: np}); }}
                                                    style={{ width: '100%', background: 'transparent', border: 'none', padding: '0.4rem 0' }}
                                                />
                                                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>Gap Min</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                        <button 
                            className="secondary" 
                            onClick={handleAddPhase}
                            style={{ width: '100%', padding: '0.8rem', borderStyle: 'dashed' }}
                        >
                            + Add New Growth Phase
                        </button>
                    </div>
                </div>
            )}
            
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textAlign: 'center', marginTop: '1rem' }}>
                Note: Growth logic strictly enforces these thresholds in the background. Changes require saving.
            </div>
        </div>
    );
}
