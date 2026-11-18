import { createContext } from 'react';
import type { CurrencyRate } from '../api/rates';

export interface RateContextValue {
    rates: CurrencyRate[];
    isLoading: boolean;
    saveRate: (currency: string, value: number) => Promise<void>;
}

export const RateContext = createContext<RateContextValue | null>(null);
