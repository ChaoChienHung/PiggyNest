import assert from 'node:assert/strict';
import { fillReportPeriods, metricSummary } from '../src/utils/reportMath.ts';

const row = (period, income, expense, net, incomeCount, expenseCount, netCount) => ({
    period, income, expense, net, incomeCount, expenseCount, netCount,
    balance: net, transactionCount: incomeCount + expenseCount, categoryExpenses: {},
});

const days = fillReportPeriods([
    row('2026-12-31', 10, 0, 10, 1, 0, 1),
    row('2027-01-02', 0, 4, -4, 0, 1, 1),
], 'day', '2026-12-31', '2027-01-02');
assert.deepEqual(days.map(item => item.period), ['2026-12-31', '2027-01-01', '2027-01-02']);
assert.equal(metricSummary(days, 'income').average, 10 / 3);
assert.equal(metricSummary(days, 'income').minPeriod, '2027-01-01');
assert.equal(metricSummary(days, 'expense').maxPeriod, '2027-01-02');
assert.equal(metricSummary(days, 'net').count, 2);

const months = fillReportPeriods([
    row('2026-12', 10, 0, 10, 1, 0, 1),
    row('2027-02', 0, 4, -4, 0, 1, 1),
], 'month', '2026-12-01', '2027-02-28');
assert.deepEqual(months.map(item => item.period), ['2026-12', '2027-01', '2027-02']);
assert.equal(metricSummary(months, 'expense').average, 4 / 3);

const years = fillReportPeriods([
    row('2026', 10, 0, 10, 1, 0, 1),
    row('2028', 0, 4, -4, 0, 1, 1),
], 'year', '2026-01-01', '2028-12-31');
assert.deepEqual(years.map(item => item.period), ['2026', '2027', '2028']);
console.log('Report period and summary checks passed');
