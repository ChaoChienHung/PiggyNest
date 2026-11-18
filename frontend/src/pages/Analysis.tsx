import { Link, useSearchParams } from 'react-router-dom';
import { StatisticsCharts } from '../components/StatisticsCharts';
import { PiggyBankView } from './PiggyBankView';

export const Analysis = () => {
    const [params] = useSearchParams();
    const bankId = Number(params.get('bank'));
    if (Number.isSafeInteger(bankId) && bankId > 0) return <PiggyBankView analyticsOnly bankId={bankId} />;
    return <main className="container page-layout-container animate-fade-in analysis-page">
        <Link to="/" className="back-to-dashboard-link">← Back to Dashboard</Link>
        <h1 className="dashboard-title">Graph Analysis</h1>
        <StatisticsCharts />
    </main>;
};
