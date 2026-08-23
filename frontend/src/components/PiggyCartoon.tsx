import React from 'react';

export const GoldCoin = ({ className, style }: { className?: string; style?: React.CSSProperties }) => (
    <svg
        width="32"
        height="32"
        viewBox="0 0 40 40"
        className={className}
        style={style}
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
    >
        <circle cx="20" cy="20" r="18" fill="var(--warning)" stroke="var(--text-primary)" strokeWidth="3" />
        <circle cx="20" cy="20" r="15" fill="var(--coin-gold)" />
        <circle cx="20" cy="20" r="10" fill="none" stroke="var(--warning)" strokeWidth="2" strokeDasharray="4 2" />
        <text x="20" y="26" fontFamily="'Outfit', sans-serif" fontWeight="800" fontSize="18" fill="var(--warning)" textAnchor="middle">$</text>
    </svg>
);

export const PiggySvg = () => (
    <svg width="180" height="180" viewBox="0 0 240 240" fill="none" xmlns="http://www.w3.org/2000/svg">
        <ellipse cx="120" cy="205" rx="70" ry="12" fill="rgba(255, 141, 161, 0.2)" />
        <rect x="75" y="165" width="24" height="35" rx="10" fill="#ff738c" />
        <rect x="140" y="165" width="24" height="35" rx="10" fill="#ff738c" />
        <rect x="60" y="160" width="24" height="35" rx="10" fill="#ff8da1" />
        <rect x="155" y="160" width="24" height="35" rx="10" fill="#ff8da1" />
        <path d="M 50 120 C 35 120, 30 100, 40 95 C 50 90, 48 110, 38 105" stroke="#ff738c" strokeWidth="6" strokeLinecap="round" fill="none" />
        <circle cx="120" cy="115" r="75" fill="#ff8da1" />
        <circle cx="120" cy="115" r="70" fill="url(#bodyGrad)" />
        <rect x="100" y="32" width="40" height="10" rx="5" fill="var(--text-primary)" />
        <path d="M 65 55 Q 45 25 70 35 Z" fill="#ff738c" />
        <path d="M 68 53 Q 53 33 70 40 Z" fill="#ffe5ea" />
        <path d="M 175 55 Q 195 25 170 35 Z" fill="#ff738c" />
        <path d="M 172 53 Q 187 33 170 40 Z" fill="#ffe5ea" />
        <ellipse cx="120" cy="132" rx="28" ry="20" fill="#ff738c" />
        <ellipse cx="120" cy="132" rx="24" ry="16" fill="#ffe5ea" />
        <circle cx="110" cy="132" r="4" fill="#ff738c" />
        <circle cx="130" cy="132" r="4" fill="#ff738c" />
        <path d="M 85 105 Q 92 98 100 105" stroke="var(--text-primary)" strokeWidth="4" strokeLinecap="round" fill="none" />
        <path d="M 140 105 Q 148 98 156 105" stroke="var(--text-primary)" strokeWidth="4" strokeLinecap="round" fill="none" />
        <circle cx="78" cy="120" r="10" fill="#ff5e7e" opacity="0.3" />
        <circle cx="162" cy="120" r="10" fill="#ff5e7e" opacity="0.3" />
        <defs>
            <radialGradient id="bodyGrad" cx="30%" cy="30%" r="70%">
                <stop offset="0%" stopColor="#fff0f3" />
                <stop offset="50%" stopColor="#ff8da1" />
                <stop offset="100%" stopColor="#ff738c" />
            </radialGradient>
        </defs>
    </svg>
);

interface PiggyAnimationProps {
    title?: string;
    subtitle?: string;
}

export const PiggyAnimation: React.FC<PiggyAnimationProps> = ({ 
    title = "PiggyNest", 
    subtitle = "Save your gold coins, build up your nests, and grow your wealth in the cutest way!" 
}) => {
    return (
        <div className="split-screen-left">
            {/* Decorative floating items */}
            <div className="absolute animate-sparkle" style={{ top: '15%', left: '15%', fontSize: '20px', animationDelay: '0s' }}>✨</div>
            <div className="absolute animate-sparkle" style={{ top: '25%', right: '20%', fontSize: '18px', animationDelay: '0.8s' }}>⭐</div>
            <div className="absolute animate-sparkle" style={{ bottom: '20%', left: '20%', fontSize: '16px', animationDelay: '1.5s' }}>⭐</div>
            <div className="absolute animate-sparkle" style={{ bottom: '30%', right: '15%', fontSize: '20px', animationDelay: '0.4s' }}>✨</div>

            {/* Soft ambient blur backdrops */}
            <div className="absolute" style={{ top: '-10%', left: '-10%', width: '300px', height: '300px', borderRadius: '50%', background: 'var(--accent-light)', opacity: 0.6, filter: 'blur(60px)', pointerEvents: 'none' }} />
            <div className="absolute" style={{ bottom: '-10%', right: '-10%', width: '300px', height: '300px', borderRadius: '50%', background: '#fff4d6', opacity: 0.5, filter: 'blur(60px)', pointerEvents: 'none' }} />

            {/* Falling Golden Coins Container */}
            <div className="absolute" style={{ top: 'calc(50% - 165px)', left: 'calc(50% - 16px)', zIndex: 10, pointerEvents: 'none' }}>
                <GoldCoin className="absolute animate-coin-1" style={{ left: '-5px' }} />
                <GoldCoin className="absolute animate-coin-2" style={{ left: '15px' }} />
                <GoldCoin className="absolute animate-coin-3" style={{ left: '-25px' }} />
            </div>

            {/* Gently Floating Cute Piggy Bank */}
            <div className="relative animate-float-piggy" style={{ zIndex: 5 }}>
                <PiggySvg />
            </div>

            {/* Brand description text */}
            <div className="text-center mt-6" style={{ zIndex: 10 }}>
                <h1 className="text-3xl font-bold" style={{ color: 'var(--text-primary)', fontSize: '2rem', letterSpacing: '-0.025em', marginBottom: '0.5rem' }}>
                    {title} <span>🐷</span>
                </h1>
                <p className="text-secondary font-medium" style={{ maxWidth: '280px', margin: '0 auto', fontSize: '0.9rem', lineHeight: '1.5', color: 'var(--text-secondary)' }}>
                    {subtitle}
                </p>
            </div>
        </div>
    );
};
