import { useState } from 'react';
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';
import { formatMoney } from '../utils/money';
import { categoryPercentTenths, type CategoryAmount } from '../utils/categoryPercentages';

const COLORS = ['#ff8da1', '#ffd166', '#ffb703', '#ff5e7e', '#ffc2d1', '#f59e0b', '#ec4899', '#8b5cf6'];

interface ExpenseCategoryChartProps {
    data: CategoryAmount[];
    currency: string;
}

export const ExpenseCategoryChart = ({ data, currency }: ExpenseCategoryChartProps) => {
    const [listOpen, setListOpen] = useState(false);
    const [hovered, setHovered] = useState<number | null>(null);
    const [selected, setSelected] = useState<number | null>(null);
    const sorted = [...data].filter(item => item.value > 0).sort((a, b) => b.value - a.value);
    const percentages = categoryPercentTenths(sorted);
    const detailIndex = hovered ?? selected;
    const detail = detailIndex !== null ? sorted[detailIndex] : null;
    const summary = (index: number) => `${formatMoney(sorted[index].value, currency)} · ${(percentages[index] / 10).toFixed(1)}%`;

    return (
        <div className="category-chart">
            <div className="category-chart-header">
                <h3 className="font-semibold text-text-secondary">Expense Categories</h3>
            </div>
            <div className="category-chart-plot">
                {sorted.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                            <Pie
                                data={sorted}
                                cx="50%"
                                cy="50%"
                                outerRadius={80}
                                labelLine={false}
                                dataKey="value"
                                onMouseEnter={(_, index) => setHovered(index)}
                                onMouseLeave={() => setHovered(null)}
                                onClick={(_, index) => setSelected(index)}
                            >
                                {sorted.map((item, index) => (
                                    <Cell key={item.name} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip content={({ active, payload }) => {
                                if (!active || !payload?.length) return null;
                                const entry = payload[0].payload as CategoryAmount;
                                const index = sorted.findIndex(item => item.name === entry.name);
                                if (index < 0) return null;
                                return <div className="category-slice-tooltip"><strong>{entry.name}</strong><br />{summary(index)}</div>;
                            }} />
                        </PieChart>
                    </ResponsiveContainer>
                ) : (
                    <div className="flex h-full items-center justify-center text-muted text-sm">No categorized expenses.</div>
                )}
            </div>
            {sorted.length > 0 && (
                <div
                    className="category-list-control"
                    onMouseEnter={() => setListOpen(true)}
                    onMouseLeave={() => setListOpen(false)}
                    onBlur={(event) => {
                        if (!event.currentTarget.contains(event.relatedTarget)) setListOpen(false);
                    }}
                >
                    <button
                        type="button"
                        className="category-list-trigger"
                        aria-expanded={listOpen}
                        aria-controls="category-list-panel"
                        onClick={() => setListOpen(true)}
                        onFocus={() => setListOpen(true)}
                        onKeyDown={(event) => {
                            if (event.key === 'Escape') setListOpen(false);
                        }}
                    >
                        Category Breakdown
                    </button>
                    {listOpen && (
                        <div id="category-list-panel" className="category-list-panel" role="region" aria-label="Expense category breakdown">
                            {sorted.map((item, index) => (
                                <div key={item.name} className="category-list-row">
                                    <span className="category-list-swatch" style={{ backgroundColor: COLORS[index % COLORS.length] }} aria-hidden="true" />
                                    <span className="category-list-name">{item.name}</span>
                                    <span className="category-list-value">{summary(index)}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
            <p className="category-slice-detail" role="status" aria-live="polite">
                {detail && detailIndex !== null ? `${detail.name}: ${summary(detailIndex)}` : '\u00a0'}
            </p>
        </div>
    );
};
