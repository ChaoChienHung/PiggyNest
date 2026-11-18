import { useCallback, useEffect, useState, type ReactNode } from 'react';
import { ratesApi, type CurrencyRate } from '../api/rates';
import { useAuth } from './useAuth';
import { RateContext } from './rate-context';

export const RateProvider = ({ children }: { children: ReactNode }) => {
    const { user } = useAuth();
    const userId = user?.id;
    const [loaded, setLoaded] = useState<{ userId: number; rates: CurrencyRate[] } | null>(null);
    const rates = loaded && loaded.userId === userId ? loaded.rates : [];
    const isLoading = !!userId && loaded?.userId !== userId;

    useEffect(() => {
        let active = true;
        if (!userId) return;
        ratesApi.list().then(data => {
            if (active) setLoaded({ userId, rates: data });
        }).catch(error => {
            console.error('Could not load currency rates', error);
            if (active) setLoaded({ userId, rates: [] });
        });
        return () => { active = false; };
    }, [userId]);

    const saveRate = useCallback(async (currency: string, value: number) => {
        const saved = await ratesApi.save(currency, value);
        if (userId) setLoaded(current => ({
            userId,
            rates: [...(current?.userId === userId ? current.rates : []).filter(rate => rate.currency !== currency), saved],
        }));
    }, [userId]);

    return <RateContext.Provider value={{ rates, isLoading, saveRate }}>{children}</RateContext.Provider>;
};
