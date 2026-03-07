import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { statisticsApi, type StatRecord } from '../api/statistics';

export const StatisticsCharts = () => {
    const [stats, setStats] = useState<StatRecord[]>([]);
    const [timeframe, setTimeframe] = useState<'monthly' | 'yearly'>('monthly');
    const [currency, setCurrency] = useState<string>('USD');
    const [availableCurrencies, setAvailableCurrencies] = useState<string[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [showAnalytics, setShowAnalytics] = useState(false);

    useEffect(() => {
        const loadStats = async () => {
            setIsLoading(true);
            try {
                const data = await statisticsApi.get(timeframe);
                setStats(data);

                // Extract unique currencies from the response
                const currencies = Array.from(new Set(data.map(d => d.currency)));
                setAvailableCurrencies(currencies);
                if (currencies.length > 0 && !currencies.includes(currency)) {
                    setCurrency(currencies[0]);
                }
            } catch (error) {
                console.error("Failed to load statistics", error);
            } finally {
                setIsLoading(false);
            }
        };

        loadStats();
    }, [timeframe]); // Intentionally omitting currency from dep array to not reload network

    const filteredStats = stats.filter(s => s.currency === currency);

    if (isLoading) {
        return <div className="p-8 text-center text-muted animate-pulse">Loading charts...</div>;
    }

    if (!showAnalytics) {
        return (
            <div className="flex justify-end mb-6">
                <button
                    onClick={() => setShowAnalytics(true)}
                    className="text-accent-primary hover:text-accent-light text-sm font-medium transition-colors"
                >
                    + Show Financial Analytics
                </button>
            </div>
        );
    }

    if (stats.length === 0) {
        return (
            <div className="glass-panel p-6 mb-8 animate-fade-in text-center">
                <p className="text-muted mb-4">No transaction data available yet.</p>
                <button
                    onClick={() => setShowAnalytics(false)}
                    className="btn btn-secondary text-sm"
                >
                    Hide Analytics
                </button>
            </div>
        );
    }

    return (
        <div className="glass-panel p-6 mb-8 animate-fade-in">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold">Financial Analytics</h2>
                <div className="flex gap-4 items-center">
                    <select
                        className="input-field py-1 px-3 text-sm h-auto"
                        value={timeframe}
                        onChange={(e) => setTimeframe(e.target.value as 'monthly' | 'yearly')}
                    >
                        <option value="monthly">Monthly</option>
                        <option value="yearly">Yearly</option>
                    </select>

                    {availableCurrencies.length > 1 && (
                        <select
                            className="input-field py-1 px-3 text-sm h-auto"
                            value={currency}
                            onChange={(e) => setCurrency(e.target.value)}
                        >
                            {availableCurrencies.map(c => (
                                <option key={c} value={c}>{c}</option>
                            ))}
                        </select>
                    )}

                    <button
                        onClick={() => setShowAnalytics(false)}
                        className="text-muted hover:text-text-primary text-sm ml-2 transition-colors"
                    >
                        Hide
                    </button>
                </div>
            </div>

            <div style={{ height: '300px', width: '100%' }} className="mb-8">
                {filteredStats.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                            data={filteredStats}
                            margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                        >
                            <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                            <XAxis dataKey="period" stroke="#888" />
                            <YAxis stroke="#888" />
                            <Tooltip
                                cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                                contentStyle={{ backgroundColor: 'rgb(30,30,30)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                            />
                            <Legend />
                            <Bar dataKey="income" name="Income/Deposits" fill="#10B981" radius={[4, 4, 0, 0]} maxBarSize={50} />
                            <Bar dataKey="expense" name="Expenses/Withdrawals" fill="#EF4444" radius={[4, 4, 0, 0]} maxBarSize={50} />
                        </BarChart>
                    </ResponsiveContainer>
                ) : (
                    <div className="flex items-center justify-center h-full text-muted">
                        No transaction data for this currency yet.
                    </div>
                )}
            </div>

            {filteredStats.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 border-t border-glass-border pt-8 mt-4">
                    {/* Pie Chart 1: Money Flow Summary (Income vs Expense) */}
                    <div>
                        <h3 className="text-center font-semibold mb-4 text-text-secondary">Overall Money Flow</h3>
                        <div style={{ height: '250px', width: '100%' }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={[
                                            { name: 'Total Income', value: filteredStats.reduce((sum, s) => sum + s.income, 0) },
                                            { name: 'Total Expense', value: filteredStats.reduce((sum, s) => sum + s.expense, 0) }
                                        ].filter(d => d.value > 0)}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={60}
                                        outerRadius={80}
                                        paddingAngle={5}
                                        dataKey="value"
                                    >
                                        <Cell fill="#10B981" />
                                        <Cell fill="#EF4444" />
                                    </Pie>
                                    <Tooltip
                                        contentStyle={{ backgroundColor: 'rgb(30,30,30)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                                        itemStyle={{ color: '#fff' }}
                                    />
                                    <Legend />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* Pie Chart 2: Expense Breakdown by Category */}
                    <div>
                        <h3 className="text-center font-semibold mb-4 text-text-secondary">Expense Categories</h3>
                        <div style={{ height: '250px', width: '100%' }}>
                            {(() => {
                                // Aggregate categories across all filtered periods
                                const catTotals: Record<string, number> = {};
                                filteredStats.forEach(stat => {
                                    if (stat.category_expenses) {
                                        Object.entries(stat.category_expenses).forEach(([cat, amt]) => {
                                            catTotals[cat] = (catTotals[cat] || 0) + amt;
                                        });
                                    }
                                });

                                const pieData = Object.entries(catTotals)
                                    .map(([name, value]) => ({ name, value }))
                                    .filter(d => d.value > 0)
                                    .sort((a, b) => b.value - a.value); // Sort biggest first

                                // Vibrant color palette for categories
                                const COLORS = ['#6366f1', '#ec4899', '#f59e0b', '#06b6d4', '#8b5cf6', '#14b8a6', '#f43f5e', '#a855f7'];

                                if (pieData.length === 0) {
                                    return <div className="flex h-full items-center justify-center text-muted text-sm pb-8">No categorized expenses.</div>;
                                }

                                return (
                                    <ResponsiveContainer width="100%" height="100%">
                                        <PieChart>
                                            <Pie
                                                data={pieData}
                                                cx="50%"
                                                cy="50%"
                                                labelLine={false}
                                                outerRadius={80}
                                                fill="#8884d8"
                                                dataKey="value"
                                            >
                                                {pieData.map((_, index) => (
                                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                                ))}
                                            </Pie>
                                            <Tooltip
                                                contentStyle={{ backgroundColor: 'rgb(30,30,30)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                                                itemStyle={{ color: '#fff' }}
                                            />
                                            <Legend />
                                        </PieChart>
                                    </ResponsiveContainer>
                                );
                            })()}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
