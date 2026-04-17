import { useState, useEffect } from 'react';
import { getRecipe, getRecipeStatus, saveRecipe } from '../api';

export default function RecipeManager() {
    const [recipe, setRecipe] = useState(null);
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchStatus, 5000);
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
            // silent fail on poll
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

    const handleResetSession = async () => {
        setSaving(true);
        setError(null);
        try {
            const newRecipe = { ...recipe, created_at: new Date().toISOString() };
            await saveRecipe(newRecipe);
            await fetchData();
        } catch (err) {
            setError(err.message);
        } finally {
            setSaving(false);
        }
    };

    if (loading) return <div className="glass-card">Loading Recipe Manager...</div>;
    if (!recipe) return <div className="glass-card">No recipe found. Initialize backend first.</div>;

    const currentDay = status?.current_day || 0;
    const activePhase = status?.phase?.name || "None";
    const daemonActive = status?.active;

    return (
        <div className="glass-card" style={{ borderColor: daemonActive ? 'var(--accent-purple)' : 'var(--glass-border)', boxShadow: daemonActive ? '0 0 15px rgba(168, 85, 247, 0.15)' : 'var(--glass-shadow)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
                    <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: daemonActive ? 'var(--accent-green)' : 'var(--accent-red)', boxShadow: daemonActive ? '0 0 8px var(--accent-green)' : 'none' }}></div>
                    <h3 style={{ margin: 0, color: 'var(--accent-purple)' }}>⚙️ Recipe Manager</h3>
                </div>
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                        Day: <strong style={{ color: 'white' }}>{currentDay}</strong> | Phase: <strong style={{ color: 'var(--accent-teal)' }}>{activePhase}</strong>
                    </span>
                    <button className="btn-secondary" onClick={handleResetSession} style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}>
                        Reset Session (Day 0)
                    </button>
                    <button className="primary" onClick={handleSave} disabled={saving} style={{ padding: '0.5rem 1rem' }}>
                        {saving ? 'Saving...' : 'Save Recipe'}
                    </button>
                </div>
            </div>

            {error && <div style={{ color: 'var(--accent-red)', marginBottom: '1rem', padding: '0.5rem', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '4px' }}>⚠️ {error}</div>}

            <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Recipe Name</label>
                <input 
                    type="text" 
                    value={recipe.name || ''} 
                    onChange={e => setRecipe({...recipe, name: e.target.value})}
                    style={{ width: '100%', maxWidth: '400px', fontSize: '1.1rem', fontWeight: 'bold' }}
                />
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
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem' }}>
                            {/* Lighting */}
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

                            {/* Fluid Control */}
                            <div>
                                <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Fluid Target & Pump</label>
                                <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                                    <select 
                                        value={phase.fluid_control?.pump || 'water'}
                                        onChange={e => { const np=[...recipe.phases]; np[idx].fluid_control.pump=e.target.value; setRecipe({...recipe, phases: np}); }}
                                        style={{ flex: 1 }}
                                    >
                                        <option value="water">Water Pump</option>
                                        <option value="food">Food Pump</option>
                                    </select>
                                    <div style={{ display: 'flex', alignItems: 'center', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--glass-border)', borderRadius: '4px', padding: '0 0.5rem', flex: 1 }}>
                                        <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginRight: '0.5rem' }}>&lt;</span>
                                        <input 
                                            type="number" 
                                            step="0.1" 
                                            value={phase.fluid_control?.dry_threshold_v || 2.0} 
                                            onChange={e => { const np=[...recipe.phases]; np[idx].fluid_control.dry_threshold_v=parseFloat(e.target.value); setRecipe({...recipe, phases: np}); }}
                                            style={{ width: '100%', background: 'transparent', border: 'none', padding: '0.4rem 0' }}
                                        />
                                        <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>V</span>
                                    </div>
                                </div>
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
                                            value={phase.fluid_control?.cooldown_minutes || 60} 
                                            onChange={e => { const np=[...recipe.phases]; np[idx].fluid_control.cooldown_minutes=parseInt(e.target.value); setRecipe({...recipe, phases: np}); }}
                                            style={{ width: '100%', background: 'transparent', border: 'none', padding: '0.4rem 0' }}
                                        />
                                        <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Min Wait</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
            
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textAlign: 'center', marginTop: '1rem' }}>
                Note: Updating the recipe requires saving. Active phase logic strictly enforces these thresholds in the background daemon.
            </div>
        </div>
    );
}
