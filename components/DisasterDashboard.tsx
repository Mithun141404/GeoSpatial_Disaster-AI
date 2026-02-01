import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    AlertTriangle,
    Activity,
    Bell,
    MapPin,
    Clock,
    TrendingUp,
    Zap,
    Shield,
    Radio,
    RefreshCw,
    ChevronRight,
    X
} from 'lucide-react';

// API base URL
const API_BASE = 'http://127.0.0.1:8000/api';

interface DisasterEvent {
    event_id: string;
    disaster_type: string;
    location: string;
    coordinates: [number, number];
    timestamp: string;
    alert_level: string;
    status: string;
    magnitude?: number;
    description: string;
}

interface AlertMessage {
    alert_id: string;
    event_id: string;
    disaster_type: string;
    location: string;
    alert_level: string;
    priority: number;
    message: string;
    timestamp: string;
    acknowledged: boolean;
}

interface DisasterStats {
    total_active_events: number;
    total_historical_events: number;
    disaster_type_distribution: Record<string, number>;
    current_alert_levels: Record<string, number>;
    recent_activity: number;
    last_updated: string;
}

const alertLevelColors: Record<string, { bg: string; text: string; border: string; glow: string }> = {
    black: { bg: 'bg-gray-900', text: 'text-white', border: 'border-gray-700', glow: 'shadow-gray-500/50' },
    red: { bg: 'bg-red-600', text: 'text-white', border: 'border-red-500', glow: 'shadow-red-500/50' },
    orange: { bg: 'bg-orange-500', text: 'text-white', border: 'border-orange-400', glow: 'shadow-orange-500/50' },
    yellow: { bg: 'bg-yellow-400', text: 'text-gray-900', border: 'border-yellow-300', glow: 'shadow-yellow-500/50' },
    green: { bg: 'bg-green-500', text: 'text-white', border: 'border-green-400', glow: 'shadow-green-500/50' },
};

const disasterTypeIcons: Record<string, string> = {
    earthquake: '🌍',
    flood: '🌊',
    wildfire: '🔥',
    hurricane: '🌀',
    tornado: '🌪️',
    tsunami: '🌊',
    volcanic: '🌋',
    drought: '☀️',
    storm: '⛈️',
    landslide: '🏔️',
    cyclone: '🌀',
    typhoon: '🌀',
    blizzard: '❄️',
    heat_wave: '🌡️',
    cold_wave: '🥶',
    air_quality: '💨',
    other: '⚠️',
};

export const DisasterDashboard: React.FC = () => {
    const [activeDisasters, setActiveDisasters] = useState<DisasterEvent[]>([]);
    const [activeAlerts, setActiveAlerts] = useState<AlertMessage[]>([]);
    const [stats, setStats] = useState<DisasterStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedEvent, setSelectedEvent] = useState<DisasterEvent | null>(null);
    const [wsConnected, setWsConnected] = useState(false);

    const fetchData = useCallback(async () => {
        try {
            const [disastersRes, alertsRes, statsRes] = await Promise.all([
                fetch(`${API_BASE}/disasters/live`),
                fetch(`${API_BASE}/alerts/active`),
                fetch(`${API_BASE}/disasters/stats`),
            ]);

            if (disastersRes.ok) {
                const disasters = await disastersRes.json();
                setActiveDisasters(disasters);
            }

            if (alertsRes.ok) {
                const alerts = await alertsRes.json();
                setActiveAlerts(alerts);
            }

            if (statsRes.ok) {
                const statsData = await statsRes.json();
                setStats(statsData);
            }

            setError(null);
        } catch (err) {
            setError('Failed to connect to disaster monitoring service');
            console.error('Error fetching disaster data:', err);
        } finally {
            setLoading(false);
        }
    }, []);

    // WebSocket connection for real-time updates
    useEffect(() => {
        let ws: WebSocket | null = null;

        const connectWebSocket = () => {
            try {
                ws = new WebSocket(`ws://127.0.0.1:8000/api/ws?client_id=dashboard_${Date.now()}&categories=disasters,alerts,system`);

                ws.onopen = () => {
                    setWsConnected(true);
                    console.log('WebSocket connected');
                };

                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);

                    if (data.type === 'disaster_event') {
                        if (data.action === 'new') {
                            setActiveDisasters(prev => [data.data, ...prev]);
                        } else if (data.action === 'update') {
                            setActiveDisasters(prev =>
                                prev.map(d => d.event_id === data.data.event_id ? data.data : d)
                            );
                        }
                    } else if (data.type === 'alert') {
                        if (data.action === 'new') {
                            setActiveAlerts(prev => [data.data, ...prev]);
                        }
                    } else if (data.type === 'system_stats') {
                        setStats(data.data);
                    }
                };

                ws.onclose = () => {
                    setWsConnected(false);
                    // Reconnect after 5 seconds
                    setTimeout(connectWebSocket, 5000);
                };

                ws.onerror = () => {
                    setWsConnected(false);
                };
            } catch (err) {
                console.error('WebSocket error:', err);
            }
        };

        fetchData();
        connectWebSocket();

        // Fallback polling every 30 seconds
        const pollInterval = setInterval(fetchData, 30000);

        return () => {
            if (ws) ws.close();
            clearInterval(pollInterval);
        };
    }, [fetchData]);

    const formatTime = (timestamp: string) => {
        const date = new Date(timestamp);
        return date.toLocaleString();
    };

    const getTimeAgo = (timestamp: string) => {
        const now = new Date();
        const then = new Date(timestamp);
        const diffMs = now.getTime() - then.getTime();
        const diffMins = Math.floor(diffMs / 60000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
        return `${Math.floor(diffMins / 1440)}d ago`;
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full"
                />
            </div>
        );
    }

    return (
        <div className="h-full overflow-y-auto p-6 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-black text-slate-900 dark:text-white flex items-center gap-3">
                        <div className="p-2 bg-gradient-to-br from-red-500 to-orange-500 rounded-xl">
                            <Activity className="w-6 h-6 text-white" />
                        </div>
                        Real-Time Disaster Monitor
                    </h1>
                    <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                        Multi-hazard detection & alerting system
                    </p>
                </div>

                <div className="flex items-center gap-4">
                    {/* WebSocket Status */}
                    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold ${wsConnected
                        ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                        : 'bg-red-500/20 text-red-400 border border-red-500/30'
                        }`}>
                        <Radio className={`w-3 h-3 ${wsConnected ? 'animate-pulse' : ''}`} />
                        {wsConnected ? 'LIVE' : 'OFFLINE'}
                    </div>

                    <button
                        onClick={fetchData}
                        className="p-2 bg-slate-100 dark:bg-slate-800 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                    >
                        <RefreshCw className="w-4 h-4 text-slate-600 dark:text-slate-400" />
                    </button>
                </div>
            </div>

            {/* Error Banner */}
            {error && (
                <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-center gap-3"
                >
                    <AlertTriangle className="w-5 h-5 text-red-500" />
                    <span className="text-red-500 text-sm font-medium">{error}</span>
                </motion.div>
            )}

            {/* Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-gradient-to-br from-red-500 to-red-600 rounded-2xl p-5 text-white"
                >
                    <div className="flex items-center justify-between mb-3">
                        <Zap className="w-6 h-6 opacity-80" />
                        <span className="text-xs font-bold bg-white/20 px-2 py-0.5 rounded-full">ACTIVE</span>
                    </div>
                    <div className="text-3xl font-black">{stats?.total_active_events || 0}</div>
                    <div className="text-xs opacity-80 font-medium mt-1">Active Events</div>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="bg-gradient-to-br from-orange-500 to-amber-500 rounded-2xl p-5 text-white"
                >
                    <div className="flex items-center justify-between mb-3">
                        <Bell className="w-6 h-6 opacity-80" />
                        <span className="text-xs font-bold bg-white/20 px-2 py-0.5 rounded-full">PENDING</span>
                    </div>
                    <div className="text-3xl font-black">{activeAlerts.length}</div>
                    <div className="text-xs opacity-80 font-medium mt-1">Active Alerts</div>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="bg-gradient-to-br from-blue-500 to-indigo-500 rounded-2xl p-5 text-white"
                >
                    <div className="flex items-center justify-between mb-3">
                        <TrendingUp className="w-6 h-6 opacity-80" />
                        <span className="text-xs font-bold bg-white/20 px-2 py-0.5 rounded-full">24H</span>
                    </div>
                    <div className="text-3xl font-black">{stats?.recent_activity || 0}</div>
                    <div className="text-xs opacity-80 font-medium mt-1">Recent Activity</div>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    className="bg-gradient-to-br from-emerald-500 to-green-500 rounded-2xl p-5 text-white"
                >
                    <div className="flex items-center justify-between mb-3">
                        <Shield className="w-6 h-6 opacity-80" />
                        <span className="text-xs font-bold bg-white/20 px-2 py-0.5 rounded-full">TOTAL</span>
                    </div>
                    <div className="text-3xl font-black">{stats?.total_historical_events || 0}</div>
                    <div className="text-xs opacity-80 font-medium mt-1">Historical Events</div>
                </motion.div>
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Active Disasters */}
                <div className="lg:col-span-2 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
                    <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
                        <h2 className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
                            <AlertTriangle className="w-5 h-5 text-red-500" />
                            Active Disaster Events
                        </h2>
                        <span className="text-xs text-slate-500 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded-full">
                            {activeDisasters.length} events
                        </span>
                    </div>

                    <div className="divide-y divide-slate-100 dark:divide-slate-800 max-h-[400px] overflow-y-auto">
                        {activeDisasters.length === 0 ? (
                            <div className="p-8 text-center text-slate-500">
                                <Shield className="w-12 h-12 mx-auto mb-3 opacity-30" />
                                <p className="font-medium">No active disasters</p>
                                <p className="text-sm opacity-70">All systems operational</p>
                            </div>
                        ) : (
                            activeDisasters.map((event, idx) => (
                                <motion.div
                                    key={event.event_id}
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: idx * 0.05 }}
                                    onClick={() => setSelectedEvent(event)}
                                    className="p-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer transition-colors"
                                >
                                    <div className="flex items-start gap-4">
                                        <div className="text-3xl">{disasterTypeIcons[event.disaster_type] || '⚠️'}</div>

                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 mb-1">
                                                <span className="font-bold text-slate-900 dark:text-white capitalize">
                                                    {event.disaster_type.replace('_', ' ')}
                                                </span>
                                                <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${alertLevelColors[event.alert_level]?.bg || 'bg-gray-500'
                                                    } ${alertLevelColors[event.alert_level]?.text || 'text-white'}`}>
                                                    {event.alert_level.toUpperCase()}
                                                </span>
                                            </div>

                                            <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
                                                <MapPin className="w-3.5 h-3.5" />
                                                <span className="truncate">{event.location}</span>
                                            </div>

                                            <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
                                                <span className="flex items-center gap-1">
                                                    <Clock className="w-3 h-3" />
                                                    {getTimeAgo(event.timestamp)}
                                                </span>
                                                {event.magnitude && (
                                                    <span className="font-bold text-orange-500">
                                                        Mag {event.magnitude}
                                                    </span>
                                                )}
                                            </div>
                                        </div>

                                        <ChevronRight className="w-5 h-5 text-slate-400" />
                                    </div>
                                </motion.div>
                            ))
                        )}
                    </div>
                </div>

                {/* Alert Feed */}
                <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
                    <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
                        <h2 className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
                            <Bell className="w-5 h-5 text-orange-500" />
                            Alert Feed
                        </h2>
                        <span className="text-xs text-slate-500 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded-full">
                            {activeAlerts.length} pending
                        </span>
                    </div>

                    <div className="divide-y divide-slate-100 dark:divide-slate-800 max-h-[400px] overflow-y-auto">
                        {activeAlerts.length === 0 ? (
                            <div className="p-8 text-center text-slate-500">
                                <Bell className="w-12 h-12 mx-auto mb-3 opacity-30" />
                                <p className="font-medium">No pending alerts</p>
                            </div>
                        ) : (
                            activeAlerts.map((alert, idx) => (
                                <motion.div
                                    key={alert.alert_id}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: idx * 0.05 }}
                                    className={`p-4 border-l-4 ${alertLevelColors[alert.alert_level]?.border || 'border-gray-500'
                                        }`}
                                >
                                    <div className="flex items-start justify-between gap-2 mb-2">
                                        <span className="font-bold text-sm text-slate-900 dark:text-white capitalize">
                                            {alert.disaster_type.replace('_', ' ')} Alert
                                        </span>
                                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${alertLevelColors[alert.alert_level]?.bg || 'bg-gray-500'
                                            } ${alertLevelColors[alert.alert_level]?.text || 'text-white'}`}>
                                            {alert.alert_level.toUpperCase()}
                                        </span>
                                    </div>

                                    <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-2 mb-2">
                                        {alert.message}
                                    </p>

                                    <div className="flex items-center justify-between text-[10px] text-slate-500">
                                        <span className="flex items-center gap-1">
                                            <MapPin className="w-3 h-3" />
                                            {alert.location}
                                        </span>
                                        <span>{getTimeAgo(alert.timestamp)}</span>
                                    </div>
                                </motion.div>
                            ))
                        )}
                    </div>
                </div>
            </div>

            {/* Disaster Type Distribution */}
            {stats?.disaster_type_distribution && Object.keys(stats.disaster_type_distribution).length > 0 && (
                <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6">
                    <h2 className="font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                        <TrendingUp className="w-5 h-5 text-blue-500" />
                        Disaster Type Distribution
                    </h2>

                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
                        {Object.entries(stats.disaster_type_distribution).map(([type, count]) => (
                            <div
                                key={type}
                                className="bg-slate-50 dark:bg-slate-800 rounded-xl p-3 text-center"
                            >
                                <div className="text-2xl mb-1">{disasterTypeIcons[type] || '⚠️'}</div>
                                <div className="text-lg font-black text-slate-900 dark:text-white">{count}</div>
                                <div className="text-[10px] text-slate-500 font-medium capitalize">
                                    {type.replace('_', ' ')}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Event Detail Modal */}
            <AnimatePresence>
                {selectedEvent && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                        onClick={() => setSelectedEvent(null)}
                    >
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                            onClick={(e) => e.stopPropagation()}
                            className="bg-white dark:bg-slate-900 rounded-2xl max-w-lg w-full overflow-hidden shadow-2xl"
                        >
                            <div className={`p-6 ${alertLevelColors[selectedEvent.alert_level]?.bg || 'bg-slate-700'}`}>
                                <div className="flex items-start justify-between">
                                    <div className="flex items-center gap-4">
                                        <span className="text-4xl">{disasterTypeIcons[selectedEvent.disaster_type] || '⚠️'}</span>
                                        <div>
                                            <h3 className="text-xl font-black text-white capitalize">
                                                {selectedEvent.disaster_type.replace('_', ' ')}
                                            </h3>
                                            <p className="text-white/80 text-sm">{selectedEvent.location}</p>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => setSelectedEvent(null)}
                                        className="p-1 hover:bg-white/20 rounded-lg transition-colors"
                                    >
                                        <X className="w-5 h-5 text-white" />
                                    </button>
                                </div>
                            </div>

                            <div className="p-6 space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <div className="text-xs text-slate-500 font-medium mb-1">Alert Level</div>
                                        <div className={`inline-block px-3 py-1 rounded-full text-sm font-bold ${alertLevelColors[selectedEvent.alert_level]?.bg || 'bg-gray-500'
                                            } ${alertLevelColors[selectedEvent.alert_level]?.text || 'text-white'}`}>
                                            {selectedEvent.alert_level.toUpperCase()}
                                        </div>
                                    </div>

                                    <div>
                                        <div className="text-xs text-slate-500 font-medium mb-1">Status</div>
                                        <div className="text-sm font-bold text-slate-900 dark:text-white capitalize">
                                            {selectedEvent.status}
                                        </div>
                                    </div>

                                    {selectedEvent.magnitude && (
                                        <div>
                                            <div className="text-xs text-slate-500 font-medium mb-1">Magnitude</div>
                                            <div className="text-sm font-bold text-orange-500">
                                                {selectedEvent.magnitude}
                                            </div>
                                        </div>
                                    )}

                                    <div>
                                        <div className="text-xs text-slate-500 font-medium mb-1">Coordinates</div>
                                        <div className="text-sm font-mono text-slate-900 dark:text-white">
                                            {selectedEvent.coordinates[0].toFixed(4)}, {selectedEvent.coordinates[1].toFixed(4)}
                                        </div>
                                    </div>
                                </div>

                                <div>
                                    <div className="text-xs text-slate-500 font-medium mb-1">Description</div>
                                    <p className="text-sm text-slate-700 dark:text-slate-300">
                                        {selectedEvent.description || 'No additional details available.'}
                                    </p>
                                </div>

                                <div>
                                    <div className="text-xs text-slate-500 font-medium mb-1">Timestamp</div>
                                    <div className="text-sm text-slate-900 dark:text-white">
                                        {formatTime(selectedEvent.timestamp)}
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default DisasterDashboard;
