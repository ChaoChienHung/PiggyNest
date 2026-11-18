import type { CurrencyRate } from '../api/rates';

export interface Conversion {
    amount: number;
    explanation: string;
    updatedAt: string | null;
}

export const displayCurrencyOptions = (held: string[], current?: string) =>
    [...new Set(['NTD', 'SGD', 'USD', 'EUR', 'GBP', 'JPY', ...held, ...(current ? [current] : [])])]
        .map(currency => ({ value: currency, label: currency }));

export const rateSummary = (currencies: string[], displayCurrency: string, rates: CurrencyRate[]) =>
    [...new Set(currencies)].filter(currency => currency !== displayCurrency).map(currency => {
        const converted = convertAmount(1, currency, displayCurrency, rates);
        return converted ? `${currency}: ${converted.explanation}; set ${converted.updatedAt}` : '';
    }).filter(Boolean).join('\n');

/** Converts through NTD without changing any stored ledger amount. */
export const convertAmount = (
    amount: number, from: string, to: string, rates: CurrencyRate[],
): Conversion | null => {
    if (from === to) return { amount, explanation: `1 ${from} = 1 ${to}`, updatedAt: null };
    const source = from === 'NTD' ? null : rates.find(rate => rate.currency === from);
    const target = to === 'NTD' ? null : rates.find(rate => rate.currency === to);
    if ((from !== 'NTD' && !source) || (to !== 'NTD' && !target)) return null;
    const sourceRate = source?.rate_to_ntd ?? 1;
    const targetRate = target?.rate_to_ntd ?? 1;
    if (!Number.isFinite(sourceRate) || !Number.isFinite(targetRate) || sourceRate <= 0 || targetRate <= 0) return null;
    const terms = [source, target].filter((rate): rate is CurrencyRate => rate !== null);
    return {
        amount: amount * sourceRate / targetRate,
        explanation: terms.map(rate => `1 ${rate.currency} = ${rate.rate_to_ntd} NTD`).join('; '),
        updatedAt: terms.map(rate => rate.updated_at).join('; ') || null,
    };
};
