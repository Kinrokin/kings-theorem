/**
 * Dashboard Page - Main Ouroboros visualization interface
 * 
 * Features:
 * - WebSocket live streaming (fallback to 8-second polling)
 * - Tribunal contamination metrics with Paradox Browser
 * - Optimization reward trajectory
 * - Curvature distribution pie chart
 * - Ontological drift heatmap (10x10 grid)
 * - Real-time sample inspection with modal viewer
 * - Responsive grid layout with neon-accent sovereign aesthetic
 */
import { useEffect, useState, useRef } from "react";

import Card from "../components/Card";
import MetricCard from "../components/MetricCard";
import CurvatureChart from "../components/CurvatureChart";
import RewardChart from "../components/RewardChart";
import OntologyHeatmap from "../components/OntologyHeatmap";
import ParadoxBrowser from "../components/ParadoxBrowser";
import QwenStatusCard from "../components/QwenStatusCard";

import {
    getTribunal,
    getOptimization,
    getCurvature,
} from "../lib/api";

export default function Dashboard() {
    const [tribunal, setTribunal] = useState(null);
    const [opt, setOpt] = useState(null);
    const [curvature, setCurvature] = useState(null);
    const [rewardHistory, setRewardHistory] = useState([]);
    const [lastUpdate, setLastUpdate] = useState(null);
    const [wsConnected, setWsConnected] = useState(false);
    const wsRef = useRef(null);

    const pollAll = async () => {
        const t = await getTribunal();
        const o = await getOptimization();
        const c = await getCurvature();

        if (t) setTribunal(t);
        if (o) {
            setOpt(o);
            setRewardHistory((prev) => {
                // Keep last 20 iterations for trend visualization
                const updated = [...prev, o];
                return updated.slice(-20);
            });
        }
        if (c) setCurvature(c);

        setLastUpdate(new Date());
    };

    useEffect(() => {
        // Try WebSocket first
        const wsUrl = "ws://localhost:8000/ws/metrics";
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log("WebSocket connected");
            setWsConnected(true);
        };

        ws.onmessage = (event) => {
            try {
                const payload = JSON.parse(event.data);

                if (payload.tribunal) setTribunal(payload.tribunal);
                if (payload.optimization) {
                    setOpt(payload.optimization);
                    setRewardHistory((prev) => {
                        const updated = [...prev, payload.optimization];
                        return updated.slice(-20);
                    });
                }
                if (payload.curvature) setCurvature(payload.curvature);

                setLastUpdate(new Date());
            } catch (err) {
                console.error("WebSocket parse error:", err);
            }
        };

        ws.onerror = (err) => {
            console.error("WebSocket error:", err);
            setWsConnected(false);
        };

        ws.onclose = () => {
            console.log("WebSocket closed");
            setWsConnected(false);
        };

        wsRef.current = ws;

        // Fallback polling if WebSocket fails
        const pollInterval = setInterval(() => {
            if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
                console.log("Polling (WebSocket not available)");
                pollAll();
            }
        }, 8000);

        // Initial poll
        pollAll();

        return () => {
            clearInterval(pollInterval);
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, []);

    return (
        <div className="min-h-screen p-6 md:p-10 space-y-8">
            {/* Header */}
            <div className="text-center space-y-2">
                <h1 className="text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-neon to-highlight tracking-tight">
                    🐍 Ouroboros Protocol Dashboard
                </h1>
                <p className="text-lg opacity-70">
                    Real-time visualization of Tribunal metrics, optimization signals, and curvature distribution
                </p>
                <div className="flex items-center justify-center gap-4 text-sm">
                    {lastUpdate && (
                        <span className="opacity-50">
                            Last updated: {lastUpdate.toLocaleTimeString()}
                        </span>
                    )}
                    <span className={`px-2 py-1 rounded text-xs font-bold ${wsConnected
                        ? "bg-green-900/30 text-green-400"
                        : "bg-yellow-900/30 text-yellow-400"
                        }`}>
                        {wsConnected ? "🟢 Live" : "🟡 Polling"}
                    </span>
                </div>
            </div>

            {/* Top Row - Core Metrics + Qwen Status */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <Card title="⚖️ Tribunal Summary">
                    {tribunal ? (
                        <>
                            <MetricCard
                                label="Total Samples"
                                value={tribunal.num_samples}
                            />
                            <MetricCard
                                label="Contamination Rate"
                                value={tribunal.contamination_rate.toFixed(3)}
                            />
                            <MetricCard
                                label="Average Final Score"
                                value={tribunal.avg_final_score.toFixed(3)}
                            />
                            <MetricCard
                                label="Compression Ratio"
                                value={tribunal.compression_ratio_avg.toFixed(3)}
                            />
                            <div className="mt-3 p-2 bg-black/20 rounded text-xs opacity-70 break-all">
                                {tribunal.harvest_path.split('/').pop() || tribunal.harvest_path.split('\\').pop()}
                            </div>
                        </>
                    ) : (
                        <div className="text-gray-400 animate-pulse">Loading tribunal data...</div>
                    )}
                </Card>

                <Card title="🎯 Optimization Signal">
                    {opt ? (
                        <>
                            <MetricCard label="Iteration" value={opt.iteration} />
                            <MetricCard label="Composite Reward" value={opt.reward.toFixed(4)} />
                            <MetricCard label="Temperature" value={opt.temperature.toFixed(3)} />
                            <MetricCard label="Curvature Ratio" value={opt.curvature_ratio.toFixed(3)} />
                            <MetricCard label="Fractal Score Gain" value={opt.fractal_score_gain.toFixed(3)} />
                            <MetricCard label="Compression Density" value={opt.compression_density.toFixed(3)} />
                        </>
                    ) : (
                        <div className="text-gray-400 animate-pulse">Loading optimization data...</div>
                    )}
                </Card>

                <Card title="🌀 Curvature Distribution">
                    <CurvatureChart data={curvature} />
                    {curvature && (
                        <div className="mt-3 text-xs opacity-70 text-center">
                            Preservation Rate: {(curvature.curvature_preservation_rate * 100).toFixed(1)}%
                        </div>
                    )}
                </Card>

                {/* Qwen Status */}
                <QwenStatusCard />
            </div>

            {/* Middle Row - Reward Trend + Ontology Heatmap */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="md:col-span-2">
                    <Card title="📈 Reward Trajectory">
                        <RewardChart history={rewardHistory} />
                        {rewardHistory.length > 1 && (
                            <div className="mt-4 grid grid-cols-3 gap-4 text-xs text-center">
                                <div>
                                    <div className="opacity-70">First</div>
                                    <div className="text-highlight font-bold">
                                        {rewardHistory[0].reward.toFixed(4)}
                                    </div>
                                </div>
                                <div>
                                    <div className="opacity-70">Latest</div>
                                    <div className="text-neon font-bold">
                                        {rewardHistory[rewardHistory.length - 1].reward.toFixed(4)}
                                    </div>
                                </div>
                                <div>
                                    <div className="opacity-70">Delta</div>
                                    <div className={`font-bold ${rewardHistory[rewardHistory.length - 1].reward >= rewardHistory[0].reward
                                        ? "text-green-400"
                                        : "text-red-400"
                                        }`}>
                                        {(rewardHistory[rewardHistory.length - 1].reward - rewardHistory[0].reward >= 0 ? "+" : "")}
                                        {(rewardHistory[rewardHistory.length - 1].reward - rewardHistory[0].reward).toFixed(4)}
                                    </div>
                                </div>
                            </div>
                        )}
                    </Card>
                </div>

                <Card title="🔬 Ontological Drift Heatmap">
                    {tribunal ? (
                        <OntologyHeatmap contaminationBuckets={tribunal.contamination_buckets} />
                    ) : (
                        <div className="text-gray-400 animate-pulse">Loading heatmap data...</div>
                    )}
                </Card>
            </div>

            {/* Paradox Browser - Full Width */}
            {tribunal && tribunal.sample_list && (
                <ParadoxBrowser sampleList={tribunal.sample_list} />
            )}

            {/* Footer Info */}
            <div className="text-center text-xs opacity-40 space-y-1">
                <div>Ouroboros Protocol v2.0 - Autonomous Meta-Optimization System</div>
                <div>
                    {wsConnected
                        ? "Live WebSocket stream: ws://localhost:8000/ws/metrics"
                        : "Polling mode: 8 seconds | Backend: http://localhost:8000"
                    }
                </div>
            </div>
        </div>
    );
}
