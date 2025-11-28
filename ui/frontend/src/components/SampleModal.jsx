export default function SampleModal({ sample, onClose }) {
    if (!sample) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="bg-stone-900 border border-amber-700/40 rounded-lg shadow-2xl w-[90vw] h-[85vh] flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between border-b border-amber-700/30 p-4">
                    <div>
                        <h2 className="text-xl font-bold text-amber-400">
                            Sample Inspector
                        </h2>
                        <p className="text-sm text-stone-400 mt-1">
                            ID: {sample.id || "N/A"} | Domain: {sample.domain || "N/A"} |
                            Source: {sample.source || "N/A"}
                        </p>
                    </div>
                    <button
                        onClick={onClose}
                        className="text-stone-400 hover:text-amber-400 text-2xl font-bold transition-colors"
                    >
                        ×
                    </button>
                </div>

                {/* Instruction */}
                <div className="border-b border-amber-700/20 p-4 bg-stone-950/50">
                    <h3 className="text-sm font-semibold text-amber-500 mb-2">
                        INSTRUCTION
                    </h3>
                    <p className="text-stone-300 text-sm leading-relaxed">
                        {sample.instruction || "N/A"}
                    </p>
                </div>

                {/* Side-by-side responses */}
                <div className="flex-1 grid grid-cols-2 divide-x divide-amber-700/20 overflow-hidden">
                    {/* Verbose */}
                    <div className="flex flex-col p-4 overflow-hidden">
                        <h3 className="text-sm font-semibold text-green-400 mb-2 flex-shrink-0">
                            VERBOSE RESPONSE
                        </h3>
                        <div className="flex-1 overflow-y-auto text-stone-300 text-sm leading-relaxed whitespace-pre-wrap font-mono bg-stone-950/30 p-3 rounded border border-green-900/20">
                            {sample.response_verbose || "N/A"}
                        </div>
                    </div>

                    {/* Compressed */}
                    <div className="flex flex-col p-4 overflow-hidden">
                        <h3 className="text-sm font-semibold text-purple-400 mb-2 flex-shrink-0">
                            COMPRESSED RESPONSE
                        </h3>
                        <div className="flex-1 overflow-y-auto text-stone-300 text-sm leading-relaxed whitespace-pre-wrap font-mono bg-stone-950/30 p-3 rounded border border-purple-900/20">
                            {sample.response_compressed || "N/A"}
                        </div>
                    </div>
                </div>

                {/* Footer Metrics */}
                <div className="border-t border-amber-700/30 p-4 bg-stone-950/50">
                    <div className="grid grid-cols-4 gap-4 text-sm">
                        <div>
                            <span className="text-stone-500">Compression:</span>{" "}
                            <span className="text-amber-300 font-mono">
                                {sample.compression_ratio?.toFixed(3) || "N/A"}
                            </span>
                        </div>
                        <div>
                            <span className="text-stone-500">New Tokens:</span>{" "}
                            <span className="text-amber-300 font-mono">
                                {sample.new_token_count ?? "N/A"}
                            </span>
                        </div>
                        <div>
                            <span className="text-stone-500">Drift Score:</span>{" "}
                            <span className="text-amber-300 font-mono">
                                {sample.drift_score?.toFixed(3) || "N/A"}
                            </span>
                        </div>
                        <div>
                            <span className="text-stone-500">Contamination:</span>{" "}
                            <span
                                className={`font-mono font-bold ${sample.contamination_level === 0
                                        ? "text-green-400"
                                        : sample.contamination_level === 1
                                            ? "text-yellow-400"
                                            : "text-red-400"
                                    }`}
                            >
                                Level {sample.contamination_level ?? "?"}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
