import { memo, useCallback, useEffect, useState } from 'react';
import { Box } from '@mui/material';
import {
    Minimize,
    Maximize,
    Square,
    AppRegistration as Logo,
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { useWindowState } from '../hooks/useWindowState';

interface TitleBarProps {
    title?: string;
    showLogo?: boolean;
}

const TitleBar = memo(({ title = 'ClawAI', showLogo = true }: TitleBarProps) => {
    const theme = useTheme();
    const windowState = useWindowState();
    const [isMaximized, setIsMaximized] = useState(false);

    useEffect(() => {
        const handler = (e: Event) => {
            const state = (e as CustomEvent).detail as string;
            setIsMaximized(state === 'maximized');
        };
        window.addEventListener('window-state', handler);
        return () => window.removeEventListener('window-state', handler);
    }, []);

    const handleMinimize = useCallback(() => {
        window.clawai?.window.minimize();
    }, []);

    const handleMaximize = useCallback(() => {
        window.clawai?.window.maximize();
    }, []);

    const handleClose = useCallback(() => {
        window.clawai?.window.close();
    }, []);

    return (
        <Box
            sx={{
                height: 32,
                width: '100%',
                backgroundColor: theme.palette.background.default,
                borderBottom: `1px solid ${theme.palette.divider}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                userSelect: 'none',
                WebkitAppRegion: 'drag',
                position: 'relative',
                zIndex: 1000,
                flexShrink: 0,
            }}
        >
            {/* Left: Logo + Title */}
            <Box
                sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    px: 1.5,
                    opacity: 0.9,
                }}
            >
                {showLogo && (
                    <Logo
                        sx={{
                            fontSize: 18,
                            color: theme.palette.primary.main,
                        }}
                    />
                )}
                <span
                    style={{
                        fontSize: 12,
                        fontWeight: 500,
                        color: theme.palette.text.secondary,
                        letterSpacing: '0.3px',
                    }}
                >
                    {title}
                </span>
            </Box>

            {/* Right: Window Controls */}
            <Box
                sx={{
                    display: 'flex',
                    alignItems: 'center',
                    height: '100%',
                    WebkitAppRegion: 'no-drag',
                }}
            >
                <WindowControlButton
                    icon={<Minimize sx={{ fontSize: 16 }} />}
                    onClick={handleMinimize}
                    tooltip="Minimize"
                />
                <WindowControlButton
                    icon={isMaximized ? <Square sx={{ fontSize: 14 }} /> : <Maximize sx={{ fontSize: 16 }} />}
                    onClick={handleMaximize}
                    tooltip={isMaximized ? 'Restore' : 'Maximize'}
                />
                <WindowControlButton
                    icon={<Square sx={{ fontSize: 14 }} />}
                    onClick={handleClose}
                    tooltip="Close"
                    isClose
                />
            </Box>
        </Box>
    );
});

// ==================== Individual Window Control Button ====================

interface WindowControlButtonProps {
    icon: React.ReactNode;
    onClick: () => void;
    tooltip: string;
    isClose?: boolean;
}

const WindowControlButton = memo(({ icon, onClick, tooltip, isClose = false }: WindowControlButtonProps) => {
    const theme = useTheme();
    const [hovered, setHovered] = useState(false);

    return (
        <Box
            onMouseEnter={() => setHovered(true)}
            onMouseLeave={() => setHovered(false)}
            onClick={onClick}
            sx={{
                width: 46,
                height: 32,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                WebkitAppRegion: 'no-drag',
                position: 'relative',
                transition: 'background-color 0.15s ease',
                backgroundColor: hovered
                    ? isClose
                        ? '#e81123'
                        : theme.palette.action.hover
                    : 'transparent',
                '&:hover': {
                    backgroundColor: hovered
                        ? isClose
                            ? '#e81123'
                            : theme.palette.action.hover
                        : 'transparent',
                },
            }}
            title={tooltip}
        >
            <Box
                sx={{
                    color: isClose && hovered ? '#fff' : theme.palette.text.secondary,
                    transition: 'color 0.15s ease',
                }}
            >
                {icon}
            </Box>
        </Box>
    );
});

export default TitleBar;
