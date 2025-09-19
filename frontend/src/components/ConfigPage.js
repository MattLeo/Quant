import React, { useState, useEffect } from 'react';
import {
    Box,
    Card,
    CardContent,
    Typography,
    TextField,
    FormControl,
    FormControlLabel,
    InputLabel,
    Select,
    MenuItem,
    Switch,
    Button,
    Grid,
    Alert,
    Snackbar,
    Divider,
    InputAdornment,
    Chip
} from '@mui/material';
import {
    Save as SaveIcon,
    Refresh as RefreshIcon,
    Security as SecurityIcon,
    Settings as SettingsIcon,
    TrendingUp as TradingIcon,
    AccountBalance as AccountBalanceIcon
} from '@mui/icons-material'

function ConfigPage() {
    const [config, setConfig] = useState({
        alpaca: {
            api_key: '',
            secret: '',
            paper_trading: true
        },
        settings: {
            results_folder: 'results_folder',
            universe_type: 'filtered',
            risk_profile: 'medium',
            minimum_profit_percent: 5.0,
            auto_execute_trades: true,
            max_positions: 27,
            position_size_percent: 3.7,
            stop_loss_percent: 8.0,
            take_profit_percent: 15.0
        },
        notifications: {
            email_alerts: false,
            trade_confirmations: false,
            analysis_complete: true 
        }
    });

    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
    const [errors, setErrors] = useState({});

    useEffect(() => {
        fetchConfig();
    }, []);

    const fetchConfig = async () => {
        try {
            const response = await fetch('/api/config');
            if (response.ok) {
                const data = await response.json();
                setConfig(data);
            } else {
                throw new Error(`Failed to fetch configuration`);
            }
        } catch (error) {
            setSnackbar({ open: true, message: `Error loading configuration: ${error.message}`, severity: 'error' });
        } finally {
            setLoading(false);
        }
    };

    const validateConfig = () => {
        const newErrors = {};
        if (!config.alpaca.api_key) newErrors.api_key = 'API Key is required';
        if (!config.alpaca.secret) newErrors.secret = 'API Secret is required';
        if (config.settings.minimum_profit_percent < 1 || config.settings.minimum_profit_percent > 100) {
            newErrors.minimum_profit_percent = 'Must be between 1 and 100';
        }
        if (config.settings.position_size_percent < 1  || config.settings.position_size_percent > 100) {
            newErrors.position_size_percent = 'Must be between 1 and 100';
        }
        if (config.settings.stop_loss_percent < 1 || config.settings.stop_loss_percent > 50) {
            newErrors.stop_loss_percent = 'Must be between 1 and 50';
        }
        if (config.settings.take_profit_percent < 1 || config.settings.take_profit_percent > 200) {
            newErrors.take_profit_percent = 'Must be between 1 and 200';
        }
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const saveConfig = async () => {
        if (!validateConfig()) {
            setSnackbar ({
                open: true,
                message: 'Please fix the errors before saving',
                severity: 'error'
            });
            return
        }

        setSaving(true);
        try{
            const response = await fetch('/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(config)
            });

            if (response.ok) {
                setSnackbar({
                    open: true,
                    message: 'Configuration saved successfully',
                    severity: 'success'
                });
            } else {
                throw new Error('Failed to save configuration');
            }
        } catch (error) {
            setSnackbar({
                open: true,
                message: `Error saving configuration: ${error.message}`,
                severity: 'error'
            });
        } finally {
            setSaving(false);
        }
    };

    const handleInputChange = (section, field, value) => {
        setConfig(prev => ({
            ...prev,
            [section]: {
                ...prev[section],
                [field]: value
            }
        }));

        if(errors[field]) {
            setErrors(prev => {
                const newErrors = {...prev};
                delete newErrors[field];
                return newErrors;
            });
        }
    };

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
                <Typography>Loading configuration...</Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ maxWidth: 1200, margin: '0 auto', padding: 3 }}>
            <Typography variant='h4' gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: '2' }}>
                <SettingsIcon /> Trading System Configuration
            </Typography>

            <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant='h6' gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: '1' }}>
                                <SecurityIcon /> API Configuration
                            </Typography>

                            <TextField
                                fullWidth
                                label="Alpaca API Key"
                                type="password"
                                value={config.alpaca.api_key}
                                onChange={(e) => handleInputChange('alpaca', 'api_key', e.target.value)}
                                error={!!errors.api_key}
                                helperText={errors.api_key || 'Your Alpaca Markets API key'}
                                margin='normal'
                            />

                            <TextField
                                fullWidth
                                label="Alpaca Secret Key"
                                type='password'
                                value={config.alpaca.secret}
                                onChange={(e) => handleInputChange('alpaca', 'secret', e.target.value)}
                                error={!!errors.secret}
                                helperText={errors.secret || 'Your Alpaca Markets Secret key'}
                                margin='normal'
                            />

                            <FormControlLabel
                                control={
                                    <Switch
                                        checked={config.alpaca.paper_trading}
                                        onChange={(e) => handleInputChange('alpaca', 'paper_trading', e.target.checked)}
                                    />
                                }
                                label="Paper Trading"
                                ex={{mt:2}}
                            />
                            {config.alpaca.paper_trading ? (
                                <Chip label="SAFE MODE" color="success" size="small" />
                            ) : (
                                <Chip label="LIVE MODE" color="error" size="small" />
                            )}
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant='h6' gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: '1' }}>
                                <TradingIcon /> Trading Settings
                            </Typography>

                            <FormControl fullWidth margin="normal">
                                <InputLabel>Universe Type</InputLabel>
                                <Select
                                    value={config.settings.universe_type}
                                    onChange={(e) => handleInputChange('settings', 'universe_type', e.target.value)}
                                    label="Universe Type"
                                >
                                    <MenuItem value="filtered">Filtered (Recommended)</MenuItem>
                                    <MenuItem value="full">Full Universe</MenuItem>
                                    <MenuItem value="sp500">S&P 500</MenuItem>
                                    <MenuItem value="nasdaq">NASDAQ</MenuItem>
                                </Select>
                            </FormControl>

                            <FormControl fullWidth margin="normal">
                                <InputLabel>Risk Profile</InputLabel>
                                <Select
                                    value={config.settings.risk_profile}
                                    onChange={(e) => handleInputChange('settings', 'risk_profile', e.target.value)}
                                    label="Risk Profile"
                                >
                                    <MenuItem value="low">Low Risk</MenuItem>
                                    <MenuItem value="medium">Medium Risk</MenuItem>
                                    <MenuItem value="high">High Risk</MenuItem>
                                </Select>
                            </FormControl>

                            <TextField
                                fullWidth
                                label="Minimum Profit to Sell (%)"
                                type='number'
                                slotProps={{htmlInput: {min: 0, max:100, step: 0.1}}}
                                value={config.settings.minimum_profit_percent}
                                onChange={(e) => handleInputChange('settings', 'minimum_profit_percent', e.target.value)}
                                error={!!errors.minimum_profit_percent}
                                helperText={errors.minimum_profit_percent || 'Minimum profit to sell (percent)'}
                                margin="normal"
                                inputProps={{endAdornment: <InputAdornment position="end">%</InputAdornment>}}
                            />

                            <TextField
                                fullWidth
                                label="Maximum Positions"
                                type='number'
                                inputProps={{min: 0, max: 50}}
                                value={config.settings.max_positions}
                                onChange={(e) => handleInputChange('settings', 'max_positions', e.target.value)}
                                margin='normal'
                                helperText='Maximum number of positions to hold'
                            />
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant='h6' gutterBottom sx={{display: 'flex', alignItems: 'center', gap: 1 }}>
                                <AccountBalanceIcon /> Risk Management
                            </Typography>

                            <TextField
                                fullWidth
                                label="Position Size (%)"
                                type='number'
                                inputProps={{min: 0, max: 100, step: 0.5, endAdornment: <InputAdornment position="end">%</InputAdornment>}}
                                value={config.settings.position_size_percent}
                                onChange={(e) => handleInputChange('settings', 'position_size_percent', e.target.value)}
                                error={!!errors.position_size_percent}
                                helperText={errors.position_size_percent || 'Position size (percent)'}
                                margin='normal'
                            />

                            <TextField
                                fullWidth
                                label="Stop Loss (%)"
                                type='number'
                                inputProps={{min: 0, max: 50, step: 0.1, endAdornment: <InputAdornment position="end">%</InputAdornment>}}
                                value={config.settings.stop_loss_percent}
                                onChange={(e) => handleInputChange('settings', 'stop_loss_percent', e.target.value)}
                                error={!!errors.stop_loss_percent}
                                helperText={errors.stop_loss_percent || 'Automatic stop loss (percent)'}
                                margin='normal'
                            />
                            <TextField
                                fullWidth
                                label="Stop Loss (%)"
                                type="number"
                                inputProps={{ min: 0, max: 50, step: 0.1 }}
                                value={config.settings.stop_loss_percent}
                                onChange={(e) => handleInputChange('settings', 'stop_loss_percent', parseFloat(e.target.value) || 0)}
                                error={!!errors.stop_loss_percent}
                                helperText={errors.stop_loss_percent || 'Automatic stop loss percentage'}
                                margin="normal"
                                InputProps={{
                                    endAdornment: <InputAdornment position="end">%</InputAdornment>
                                }}
                            />

                            <TextField
                                fullWidth
                                label="Take Profit (%)"
                                type="number"
                                inputProps={{ min: 1, max: 200, step: 0.5 }}
                                value={config.settings.take_profit_percent}
                                onChange={(e) => handleInputChange('settings', 'take_profit_percent', parseFloat(e.target.value) || 1)}
                                error={!!errors.take_profit_percent}
                                helperText={errors.take_profit_percent || 'Automatic take profit percentage'}
                                margin="normal"
                                InputProps={{
                                    endAdornment: <InputAdornment position="end">%</InputAdornment>
                                }}
                            />

                            <FormControlLabel
                                control={
                                    <Switch
                                        checked={config.settings.auto_execute_trades}
                                        onChange={(e) => handleInputChange('settings', 'auto_execute_trades', e.target.checked)}
                                    />
                                }
                                label="Auto Execute Trades"
                                sx={{ mt: 2 }}
                            />
                        </CardContent>
                    </Card>
                </Grid>


                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                System & Notifications
                            </Typography>

                            <TextField
                                fullWidth
                                label="Results Folder"
                                value={config.settings.results_folder}
                                onChange={(e) => handleInputChange('settings', 'results_folder', e.target.value)}
                                margin="normal"
                                helperText="Folder path for storing analysis results"
                            />

                            <Divider sx={{ my: 2 }} />

                            <Typography variant="subtitle2" gutterBottom>
                                Notifications
                            </Typography>

                            <FormControlLabel
                                control={
                                    <Switch
                                        checked={config.notifications.email_alerts}
                                        onChange={(e) => handleInputChange('notifications', 'email_alerts', e.target.checked)}
                                    />
                                }
                                label="Email Alerts"
                            />

                            <FormControlLabel
                                control={
                                    <Switch
                                        checked={config.notifications.trade_confirmations}
                                        onChange={(e) => handleInputChange('notifications', 'trade_confirmations', e.target.checked)}
                                    />
                                }
                                label="Trade Confirmations"
                            />

                            <FormControlLabel
                                control={
                                    <Switch
                                        checked={config.notifications.analysis_complete}
                                        onChange={(e) => handleInputChange('notifications', 'analysis_complete', e.target.checked)}
                                    />
                                }
                                label="Analysis Complete Notifications"
                            />
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* Action Buttons */}
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end', mt: 4 }}>
                <Button
                    variant="outlined"
                    startIcon={<RefreshIcon />}
                    onClick={fetchConfig}
                    disabled={loading}
                >
                    Reload
                </Button>

                <Button
                    variant="contained"
                    startIcon={<SaveIcon />}
                    onClick={saveConfig}
                    disabled={saving}
                >
                    {saving ? 'Saving...' : 'Save Configuration'}
                </Button>
            </Box>

            {/* Snackbar for notifications */}
            <Snackbar
                open={snackbar.open}
                autoHideDuration={6000}
                onClose={() => setSnackbar({ ...snackbar, open: false })}
            >
                <Alert
                    onClose={() => setSnackbar({ ...snackbar, open: false })}
                    severity={snackbar.severity}
                    variant="filled"
                >
                    {snackbar.message}
                </Alert>
            </Snackbar>
        </Box>
    );
}

export default ConfigPage;