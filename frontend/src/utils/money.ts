export const getCurrencySymbol = (currency: string) => {
    switch (currency) {
        case 'USD': return '$';
        case 'EUR': return '€';
        case 'GBP': return '£';
        case 'JPY': return '¥';
        case 'NTD': return 'NT$';
        case 'SGD': return 'S$';
        default: return currency + ' ';
    }
};

/**
 * Formats an amount with its sign before the currency symbol, e.g. -S$6.42.
 * `showPlus` adds a leading + to positive amounts, as transaction rows do.
 */
export const formatMoney = (amount: number, currency: string, showPlus = false) => {
    const sign = amount < 0 ? '-' : showPlus && amount > 0 ? '+' : '';
    return `${sign}${getCurrencySymbol(currency)}${Math.abs(amount).toFixed(2)}`;
};
