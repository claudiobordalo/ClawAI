import { useState, useEffect } from 'react';

export function useWindowState() {
    const [maximized, setMaximized] = useState(false);

    useEffect(() => {
        const handler = (e: Event) => {
            const state = (e as CustomEvent).detail as string;
            setMaximized(state === 'maximized');
        };

        // Check initial state
        if (typeof window !== 'undefined' && window.clawai?.window) {
            window.clawai.window.isMaximized().then(setMaximized);
            window.addEventListener('window-state', handler);
        }

        return () => window.removeEventListener('window-state', handler);
    }, []);

    return { maximized };
}
