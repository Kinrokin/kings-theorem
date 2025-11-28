/**
 * OntologyHeatmap Component - Token-space heatmap for Ontological Drift visualization
 * 
 * Displays contamination severity as a 10x10 grid with color-coded cells:
 * - Green: Clean/Low drift (Level 0)
 * - Yellow: Medium risk (Level 1) 
 * - Red: High contamination/drift (Level 2+)
 */
import { useMemo } from 'react';
import { clsx } from 'clsx';

export default function OntologyHeatmap({ contaminationBuckets }) {
    if (!contaminationBuckets || contaminationBuckets.length === 0) {
        return (
            <div className="text-gray-400 p-4">
                No contamination data. Run Tribunal verification to populate heatmap.
            </div>
        );
    }

    const CELLS_TO_RENDER = 100;

    const data = useMemo(() => {
        const buckets = contaminationBuckets.slice(0, CELLS_TO_RENDER);
        while (buckets.length < CELLS_TO_RENDER) {
            buckets.push(0); // Fill remaining with lowest severity
        }
        return buckets;
    }, [contaminationBuckets]);

    const getHeatClass = (level) => {
        if (level >= 2) return 'bg-red-700/70 shadow-red-500/50';       // REJECT
        if (level === 1) return 'bg-yellow-500/60 shadow-yellow-500/30'; // REVIEW_REQUIRED
        return 'bg-green-500/40 shadow-green-500/20';                    // APPROVED
    };

    const stats = useMemo(() => {
        const clean = data.filter(l => l === 0).length;
        const medium = data.filter(l => l === 1).length;
        const high = data.filter(l => l >= 2).length;
        return { clean, medium, high };
    }, [data]);

    return (
        <div className="p-2">
            {/* Stats Summary */}
            <div className="mb-4 grid grid-cols-3 gap-2 text-xs">
                <div className="bg-green-500/10 p-2 rounded text-center">
                    <div className="text-green-400 font-bold text-lg">{stats.clean}</div>
                    <div className="opacity-70">Clean</div>
                </div>
                <div className="bg-yellow-500/10 p-2 rounded text-center">
                    <div className="text-yellow-400 font-bold text-lg">{stats.medium}</div>
                    <div className="opacity-70">Medium</div>
                </div>
                <div className="bg-red-500/10 p-2 rounded text-center">
                    <div className="text-red-400 font-bold text-lg">{stats.high}</div>
                    <div className="opacity-70">High</div>
                </div>
            </div>

            {/* 10x10 Grid */}
            <div className="grid grid-cols-10 gap-1">
                {data.map((level, index) => (
                    <div
                        key={index}
                        className={clsx(
                            "w-full pt-[100%] relative rounded-sm cursor-help transition-all duration-300 shadow-lg",
                            getHeatClass(level),
                            "hover:scale-110 hover:z-10"
                        )}
                        title={`Cell ${index + 1}: Severity ${level}`}
                    />
                ))}
            </div>

            {/* Legend */}
            <div className='mt-4 text-xs opacity-60 flex justify-between'>
                <span>🟩 Clean</span>
                <span>🟨 Medium</span>
                <span>🟥 High</span>
            </div>
        </div>
    );
}
