import { useState, useEffect, useMemo } from 'react';
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
 * @param {string} filename - The CSV filename to fetch (e.g., 'sensors.csv')
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

    const pullData = async () => {
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

            // Apply filter if provided
            let rows = parsed.data;
            if (filter) {
                rows = rows.filter(row => {
                    return Object.entries(filter).every(([key, value]) => {
                        const rowVal = row[key];
                        if (typeof rowVal === 'string' && typeof value === 'string') {
                            return rowVal.toLowerCase() === value.toLowerCase();
                        }
                        return rowVal === value;
                    });
                });
            }

            // Filter for last 4 hours
            const now = new Date();
            const cutoff = now.getTime() - (historyHours * 60 * 60 * 1000);
            
            const filteredData = parsed.data.filter(row => {
                if (!row.time) return false;
                const d = new Date(row.time);
                return d.getTime() > cutoff;
            }).map(row => ({
                ...row,
                // Short time for XAxis labels
                displayTime: row.time ? new Date(row.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''
            }));

            setData(filteredData);
            setError(null);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        pullData();
        const interval = setInterval(pullData, refreshInterval);
        return () => clearInterval(interval);
    }, [filename]);

    if (error && data.length === 0) {
        return (
            <div className="glass-card" style={{ padding: '2rem', textAlign: 'center', color: 'var(--accent-red)' }}>
                <p>⚠️ Failed to load {title} history</p>
                <p style={{ fontSize: '0.75rem', opacity: 0.7 }}>{error}</p>
                <div style={{ fontSize: '0.65rem', marginTop: '1rem', color: 'var(--text-secondary)' }}>
                    Ensure a Growth Cycle is ACTIVE and recording telemetry.
                </div>
            </div>
        );
    }

    return (
        <div className="glass-card" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', minHeight: '340px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <h3 style={{ margin: 0, fontSize: '1.1rem' }}>📈 {title}</h3>
                <div style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px' }}>
                    LAST {historyHours} HOURS • {data.length} PTS
                </div>
            </div>

            <div style={{ width: '100%', height: '260px', marginTop: '1rem' }}>
                {loading && data.length === 0 ? (
                    <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
                        Analyzing Data Stream...
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
                            {dataKeys.map((key, i) => (
                                <Line
                                    key={key}
                                    type="monotone"
                                    dataKey={key}
                                    stroke={colors[i % colors.length]}
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
