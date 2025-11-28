import { useEffect, useState } from "react";

export default function QwenStatusCard() {
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStatus = async () => {
            try {
                const res = await fetch("/api/qwen_status");
                if (res.ok) {
                    const data = await res.json();
                    setStatus(data);
                }
            } catch (err) {
                console.error("Failed to fetch Qwen status:", err);
            } finally {
                setLoading(false);
            }
        };

        fetchStatus();
        const interval = setInterval(fetchStatus, 30000); // Refresh every 30s

        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return (
            <div className="bg-stone-900 border border-amber-700/40 rounded-lg shadow-lg p-4">
                <h2 className="text-xl font-bold text-amber-400 mb-3">
                    🐉 Qwen Backend
                </h2>
                <div className="text-gray-400 animate-pulse">Loading status...</div>
            </div>
        );
    }

    if (!status) {
        return null;
    }

    const isOk = status.ok === true;
    const backend = status.backend || "unknown";

    return (
        <div className="bg-stone-900 border border-amber-700/40 rounded-lg shadow-lg p-4">
            <h2 className="text-xl font-bold text-amber-400 mb-3 flex items-center">
                <span className="text-2xl mr-2">🐉</span>
                Qwen Backend
            </h2>

            {/* Status Badge */}
            <div className="mb-4">
                <span
                    className={`inline-block px-3 py-1 rounded-full text-sm font-bold ${isOk
                            ? "bg-green-900/30 text-green-400"
                            : "bg-red-900/30 text-red-400"
                        }`}
                >
                    {isOk ? "✅ Available" : "❌ Unavailable"}
                </span>
            </div>

            {/* Backend Type */}
            <div className="mb-3">
                <div className="text-sm text-stone-500">Backend Type</div>
                <div className="text-lg font-mono text-amber-300">{backend}</div>
            </div>

            {/* Configuration */}
            {status.config && (
                <div className="mt-3 p-3 bg-stone-950/50 rounded border border-amber-700/20">
                    <div className="text-xs text-stone-400 mb-2">Configuration</div>
                    {backend === "http" && status.config.http_url && (
                        <div className="text-xs font-mono text-stone-300 break-all">
                            URL: {status.config.http_url}
                        </div>
                    )}
                    {backend === "http" && status.config.model_name && (
                        <div className="text-xs font-mono text-stone-300">
                            Model: {status.config.model_name}
                        </div>
                    )}
                    {backend === "local" && status.config.local_path && (
                        <div className="text-xs font-mono text-stone-300 break-all">
                            Path: {status.config.local_path}
                        </div>
                    )}
                    {backend === "openai" && status.config.model && (
                        <div className="text-xs font-mono text-stone-300">
                            Model: {status.config.model}
                        </div>
                    )}
                </div>
            )}

            {/* Error Message */}
            {!isOk && status.error && (
                <div className="mt-3 p-3 bg-red-900/20 rounded border border-red-700/30">
                    <div className="text-xs text-red-400">{status.error}</div>
                </div>
            )}
        </div>
    );
}
