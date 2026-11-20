import assert from 'node:assert/strict';
import { convertAmount } from '../src/utils/currency.ts';
import { convertLedger, summarizePeriods } from '../src/utils/ledgerAnalytics.ts';

const rates = [
    { currency: 'SGD', rate_to_ntd: 24, updated_at: '2026-01-01' },
    { currency: 'USD', rate_to_ntd: 30, updated_at: '2026-01-01' },
];
assert.equal(convertAmount(10, 'SGD', 'USD', rates).amount, 8);
assert.equal(convertAmount(10, 'SGD', 'NTD', rates).amount, 240);
assert.equal(convertAmount(10, 'EUR', 'NTD', rates), null);

const bank = { id: 1, currency: 'SGD' };
const entry = (id, amount, type, date) => ({ bank, transaction: {
    id, amount, type, date, category: 'Food', piggy_bank_id: 1,
} });
const ledger = [
    entry(1, 100, 'income', '2026-12-31T12:00:00'),
    entry(2, -20, 'expense', '2027-01-01T12:00:00'),
    entry(3, -5, 'transfer_out', '2027-01-02T12:00:00'),
    entry(4, -30, 'transfer', '2027-01-02T12:00:00'),
    entry(5, 30, 'transfer', '2027-01-02T12:00:00'),
];
const converted = convertLedger(ledger, 'NTD', rates);
assert.deepEqual(converted.missing, []);
const daily = summarizePeriods(converted.converted, 'day', null, null).periods;
assert.deepEqual(daily.map(row => row.period), ['2026-12-31', '2027-01-01', '2027-01-02']);
assert.equal(daily[0].balance, 2400);
assert.equal(daily[1].balance, 1920);
assert.equal(daily[2].balance, 1800);
assert.equal(daily[2].expense, 120);

const monthly = summarizePeriods(converted.converted, 'month', null, null).periods;
assert.deepEqual(monthly.map(row => row.period), ['2026-12', '2027-01']);
assert.equal(monthly[0].income, 2400);
assert.equal(monthly[1].expense, 600);
assert.equal(monthly[1].net, -600);
assert.equal(monthly[1].expenseCount, 2);
assert.equal(monthly[1].netCount, 4);
assert.equal(monthly[1].balance, 1800);

const yearly = summarizePeriods(converted.converted, 'year', null, null).periods;
assert.deepEqual(yearly.map(row => row.period), ['2026', '2027']);
assert.equal(yearly[0].balance, 2400);
assert.equal(yearly[1].expense, 600);
assert.equal(yearly[1].balance, 1800);
console.log('Ledger conversion and transfer checks passed');
