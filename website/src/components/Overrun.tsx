import React, { useEffect, useState } from 'react';

export const OverrunComponent = ({ overrunBack, overrunLay, overrunLast }) => {
    const [isHighlighted, setIsHighlighted] = useState(false);

    useEffect(() => {
        let timer;

        if (overrunLay > 1 || overrunBack < 1) {
            setIsHighlighted(true);
            timer = setTimeout(() => {
                setIsHighlighted(false);
            }, 1000);
        }

        return () => {
            if (timer) {
                clearTimeout(timer);
            }
        };
    }, [overrunLay]);

    return (
        <p style={{ background: isHighlighted ? 'red' : 'transparent' }}>
            Overruns (bk/ly/lt) {overrunBack.toFixed(2)}
            /{overrunLay.toFixed(2)}
            / {overrunLast.toFixed(2)}
        </p>
    );
}