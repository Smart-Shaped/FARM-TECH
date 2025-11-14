import React from 'react';

export const AnalysisProgressBar = ({ progress }) => {
    return (
        <div
            style={{
                position: 'fixed',
                bottom: 0,
                left: 0,
                right: 0,
                height: '4px',
                zIndex: 9999,
                backgroundColor: 'rgba(0, 0, 0, 0.1)'
            }}
        >
            <div
                style={{
                    height: '100%',
                    width: `${progress}%`,
                    backgroundColor: 'var(--gn-primary, #397aab)',
                    transition: 'width 0.3s ease-in-out',
                    boxShadow: '0 0 10px rgba(57, 122, 171, 0.5)'
                }}
            />
        </div>
    );
};
