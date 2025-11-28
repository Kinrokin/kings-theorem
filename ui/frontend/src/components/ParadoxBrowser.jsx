import { useState, useEffect } from "react";
import { getTribunalSample } from "../lib/api";
import SampleModal from "./SampleModal";

export default function ParadoxBrowser({ sampleList }) {
    const [filter, setFilter] = useState("");
    const [selectedSample, setSelectedSample] = useState(null);

    const filtered = (sampleList || []).filter((s) => {
        const lowerFilter = filter.toLowerCase();
        return (
            s.short_id?.toLowerCase().includes(lowerFilter) ||
            s.domain?.toLowerCase().includes(lowerFilter) ||
            s.source?.toLowerCase().includes(lowerFilter)
        );
    });

    const handleView = async (id) => {
        const detail = await getTribunalSample(id);
        if (detail) setSelectedSample(detail);
    };

    return (
        <div className="bg-stone-900 border border-amber-700/40 rounded-lg shadow-lg p-4">
            <h2 className="text-xl font-bold text-amber-400 mb-3 flex items-center">
                <span className="text-2xl mr-2">🔍</span>
                Paradox Browser
            </h2>

            {/* Filter */}
            <input
                type="text"
                placeholder="Filter by ID, domain, or source..."
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="w-full mb-3 px-3 py-2 bg-stone-950 border border-amber-700/30 rounded text-stone-300 placeholder-stone-600 focus:outline-none focus:border-amber-500/50"
            />

            {/* Table */}
            <div className="overflow-x-auto">
                <table className="w-full text-sm">
                    <thead className="border-b border-amber-700/30">
                        <tr className="text-left text-stone-400">
                            <th className="py-2 px-2">ID</th>
                            <th className="py-2 px-2">Domain</th>
                            <th className="py-2 px-2">Source</th>
                            <th className="py-2 px-2 text-right">Score</th>
                            <th className="py-2 px-2 text-center">Level</th>
                            <th className="py-2 px-2 text-center">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filtered.length === 0 && (
                            <tr>
                                <td colSpan={6} className="text-center py-4 text-stone-500">
                                    No samples found
                                </td>
                            </tr>
                        )}
                        {filtered.map((s) => (
                            <tr
                                key={s.id}
                                className="border-b border-amber-700/10 hover:bg-stone-950/50 transition-colors"
                            >
                                <td className="py-2 px-2 font-mono text-xs text-amber-300">
                                    {s.short_id || "N/A"}
                                </td>
                                <td className="py-2 px-2 text-stone-300">{s.domain || "N/A"}</td>
                                <td className="py-2 px-2 text-stone-300">{s.source || "N/A"}</td>
                                <td className="py-2 px-2 text-right font-mono text-green-400">
                                    {s.final_score?.toFixed(3) || "N/A"}
                                </td>
                                <td className="py-2 px-2 text-center">
                                    <span
                                        className={`inline-block px-2 py-1 rounded text-xs font-bold ${s.contamination_level === 0
                                                ? "bg-green-900/30 text-green-400"
                                                : s.contamination_level === 1
                                                    ? "bg-yellow-900/30 text-yellow-400"
                                                    : "bg-red-900/30 text-red-400"
                                            }`}
                                    >
                                        {s.contamination_level ?? "?"}
                                    </span>
                                </td>
                                <td className="py-2 px-2 text-center">
                                    <button
                                        onClick={() => handleView(s.id)}
                                        className="px-3 py-1 bg-amber-700/30 hover:bg-amber-700/50 text-amber-300 rounded text-xs font-semibold transition-colors"
                                    >
                                        View
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Modal */}
            {selectedSample && (
                <SampleModal
                    sample={selectedSample}
                    onClose={() => setSelectedSample(null)}
                />
            )}
        </div>
    );
}
