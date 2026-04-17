import { useState, useEffect, useMemo, useCallback } from 'react';
import { 
    ResponsiveContainer, 
    LineChart, 
    Line, 
    XAxis, 
    YAxis, 
    CartesianGrid, 
    Tooltip, 
    Legend 
} from 'recharts';
import Papa from 'papaparse';
import { fetchTelemetry } from '../api';

/**
 * TelemetryChart - A reusable chart component that fetches and parses CSV data.
 * @param {string} filename - The CSV filename to fetch
 * @param {string} title - Chart title
 * @param {string[]} dataKeys - The columns to display as lines
 * @param {string[]} colors - Colors for each line
 * @param {Object} filter - Optional filter object (e.g. { device_id: 'ADS1115_0x48' })
 * @param {number} historyHours - How many hours of data to show (default 4)
 * @param {number} refreshInterval - Refresh rate in ms (default 10000)
 */
export default function TelemetryChart({ 
    filename, 
    title = "Telemetry", 
    dataKeys = ["v0"], 
    colors = ["var(--accent-teal)"],
    filter = null,
    historyHours = 4,
    refreshInterval = 10000 
}) {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Derived device label for visual verification
    const deviceTag = useMemo(() => {
        if (!filter) return null;
        return Object.values(filter).join(', ');
    }, [filter]);

    const pullData = useCallback(async () => {
        try {
            const csvText = await fetchTelemetry(filename);
            const parsed = Papa.parse(csvText, { 
                header: true, 
                dynamicTyping: true,
                skipEmptyLines: true 
            });

            if (parsed.errors.length > 0 && parsed.data.length === 0) {
                throw new Error("Failed to parse CSV data.");
            }

            // Filter for last N hours and matching device
            const now = new Date();
            const cutoff = now.getTime() - (historyHours * 60 * 60 * 1000);
            
            let rows = parsed.data.filter(row => {
                if (!row.time) return false;
                const d = new Date(row.time);
                if (d.getTime() <= cutoff) return false;

                if (filter) {
                    return Object.entries(filter).every(([key, value]) => {
                        const rowVal = row[key] !== undefined ? row[key] : row['device_id'] !== undefined ? row['device_id'] : row['device_name'];
                        if (typeof rowVal === 'string' && typeof value === 'string') {
                            return rowVal.toLowerCase() === value.toLowerCase();
                        }
                        return rowVal === value;
                    });
                }
                return true;
            });

            const processedData = rows.map(row => ({
                ...row,
                displayTime: row.time ? new Date(row.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''
            }));

            setData(processedData);
            setError(null);
        } catch (err) {
            console.error(`[TelemetryChart] ${filename} error:`, err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [filename, filter, historyHours]);

    useEffect(() => {
        pullData();
        const interval = setInterval(pullData, refreshInterval);
        return () => clearInterval(interval);
    }, [pullData, refreshInterval]);

    const linesToRender = useMemo(() => {
        return dataKeys.map((k, i) => ({ 
            key: k, 
            color: colors[i % colors.length], 
            label: k.toUpperCase() 
        }));
    }, [dataKeys, colors]);

    if (error && data.length === 0) {
        return (
            <div className="glass-card" style={{ padding: '2rem', textAlign: 'center', color: 'var(--accent-red)' }}>
                <p>⚠️ Failed to load {title} history</p>
                {deviceTag && <p style={{ fontSize: '0.65rem' }}>Target: {deviceTag}</p>}
                <p style={{ fontSize: '0.75rem', opacity: 0.7 }}>{error}</p>
            </div>
        );
    }

    return (
        <div className="glass-card" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', minHeight: '340px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <h3 style={{ margin: 0, fontSize: '1.1rem' }}>📈 {title}</h3>
                    {deviceTag && (
                        <span style={{ 
                            fontSize: '0.6rem', 
                            background: 'rgba(255,255,255,0.1)', 
                            padding: '2px 6px', 
                            borderRadius: '4px', 
                            fontFamily: 'monospace',
                            color: 'var(--text-secondary)'
                        }}>
                            {deviceTag}
                        </span>
                    )}
                </div>
                <div style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px' }}>
                    {data.length} PTS • {historyHours}H
                </div>
            </div>

            <div style={{ width: '100%', height: '220px', marginTop: '1rem' }}>
                {loading && data.length === 0 ? (
                    <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
                        Requesting telemetry...
                    </div>
                ) : (
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={data}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                            <XAxis 
                                dataKey="displayTime" 
                                stroke="var(--text-secondary)" 
                                fontSize={10} 
                                tickLine={false} 
                                axisLine={false}
                                minTickGap={30}
                            />
                            <YAxis 
                                stroke="var(--text-secondary)" 
                                fontSize={10} 
                                tickLine={false} 
                                axisLine={false}
                                domain={['auto', 'auto']}
                            />
                            <Tooltip 
                                contentStyle={{ background: 'rgba(20,20,25,0.9)', border: '1px solid var(--glass-border)', borderRadius: '8px', fontSize: '12px' }}
                                itemStyle={{ padding: '2px 0' }}
                            />
                            <Legend wrapperStyle={{ fontSize: '10px', paddingTop: '10px' }} />
                            {linesToRender.map((line) => (
                                <Line
                                    key={line.key}
                                    name={line.label}
                                    type="monotone"
                                    dataKey={line.key}
                                    stroke={line.color}
                                    strokeWidth={2}
                                    dot={false}
                                    activeDot={{ r: 4, stroke: 'white', strokeWidth: 2 }}
                                    animationDuration={500}
                                />
                            ))}
                        </LineChart>
                    </ResponsiveContainer>
                )}
            </div>
        </div>
    );
}
