import { useState, useEffect, useCallback } from 'react';
import { ThemeProvider, CssBaseline, Box, Alert, Snackbar, CircularProgress } from '@mui/material';
import { getTheme } from './theme';
import { AppProvider } from './context/AppContext';
import { ChatProvider } from './context/ChatContext';
import { WorkspaceProvider } from './context/WorkspaceContext';
import { AgentProvider } from './context/AgentContext';
import { MemoryProvider } from './context/MemoryContext';
import { ToolProvider } from './context/ToolContext';
import { GitProvider } from './context/GitContext';
import { SettingsProvider } from './context/SettingsContext';
import { ModelProvider as ModelProviderCtx } from './context/ModelContext';
import { PlanProvider } from './context/PlanContext';
import { Sidebar } from './components/Sidebar';
import { MainContent } from './components/MainContent';
import { StatusBar } from './components/StatusBar';
import { TitleBar } from './components/TitleBar';
import { initBackend, updateBackendUrl } from './api';

function App() {
    const [backendReady, setBackendReady] = useState(false);
    const [backendError, setBackendError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    // Initialize backend in Electron mode
    useEffect(() => {
        const init = async () => {
            try {
                const isElectron = typeof window !== 'undefined' && window.clawai !== undefined;
                
                if (isElectron) {
                    console.log('[App] Electron detected, initializing backend...');
                    const started = await initBackend();
                    if (started) {
                        await updateBackendUrl();
                        setBackendReady(true);
                    } else {
                        setBackendError('Failed to start backend server');
                        // Still allow loading for development
                        setBackendReady(true);
                    }
                } else {
                    // Browser mode - backend must be running separately
                    console.log('[App] Browser mode detected');
                    setBackendReady(true);
                }
            } catch (err) {
                console.error('[App] Init error:', err);
                setBackendError('Failed to initialize application');
                setBackendReady(true); // Allow loading anyway
            } finally {
                setLoading(false);
            }
        };

        init();
    }, []);

    // Periodically update backend URL in Electron
    useEffect(() => {
        if (typeof window !== 'undefined' && window.clawai) {
            const interval = setInterval(async () => {
                await updateBackendUrl();
            }, 10000);
            return () => clearInterval(interval);
        }
    }, []);

    const theme = getTheme();

    if (loading) {
        return (
            <ThemeProvider theme={theme}>
                <CssBaseline />
                <Box
                    sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        height: '100vh',
                        backgroundColor: '#1a1a2e',
                    }}
                >
                    <CircularProgress sx={{ color: theme.palette.primary.main }} />
                    <Box sx={{ ml: 2, color: theme.palette.text.secondary }}>
                        Initializing ClawAI...
                    </Box>
                </Box>
            </ThemeProvider>
        );
    }

    return (
        <ThemeProvider theme={theme}>
            <CssBaseline />
            <AppProvider>
                <ChatProvider>
                    <WorkspaceProvider>
                        <AgentProvider>
                            <MemoryProvider>
                                <ToolProvider>
                                    <GitProvider>
                                        <SettingsProvider>
                                            <ModelProviderCtx>
                                                <PlanProvider>
                                                    <Box
                                                        sx={{
                                                            display: 'flex',
                                                            flexDirection: 'column',
                                                            height: '100vh',
                                                            width: '100vw',
                                                            overflow: 'hidden',
                                                            backgroundColor: theme.palette.background.default,
                                                        }}
                                                    >
                                                        {/* Title Bar */}
                                                        <TitleBar />

                                                        {/* Main Content */}
                                                        <Box
                                                            sx={{
                                                                display: 'flex',
                                                                flex: 1,
                                                                overflow: 'hidden',
                                                            }}
                                                        >
                                                            <Sidebar />
                                                            <MainContent />
                                                        </Box>

                                                        {/* Status Bar */}
                                                        <StatusBar />
                                                    </Box>
                                                </PlanProvider>
                                            </ModelProviderCtx>
                                        </SettingsProvider>
                                    </GitProvider>
                                </ToolProvider>
                            </MemoryProvider>
                        </AgentProvider>
                    </WorkspaceProvider>
                </ChatProvider>
            </AppProvider>

            {/* Error Snackbar */}
            <Snackbar
                open={!!backendError}
                autoHideDuration={6000}
                onClose={() => setBackendError(null)}
            >
                <Alert severity="error" onClose={() => setBackendError(null)}>
                    {backendError}
                </Alert>
            </Snackbar>
        </ThemeProvider>
    );
}

export default App;
