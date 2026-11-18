import { useContext } from 'react';
import { RateContext } from './rate-context';

export const useRates = () => {
    const context = useContext(RateContext);
    if (!context) throw new Error('useRates must be used inside RateProvider');
    return context;
};
