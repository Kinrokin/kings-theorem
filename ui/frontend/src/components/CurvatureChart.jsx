/**
 * CurvatureChart Component - Pie chart showing Euclidean vs Curved distribution
 */
import { PieChart, Pie, Cell, Legend, Tooltip } from "recharts";

export default function CurvatureChart({ data }) {
    if (!data) return <div className="text-gray-400">No Data</div>;

    const chartData = [
        { name: "Euclidean", value: data.euclidean_count },
        { name: "Curved", value: data.curved_count },
    ];

    const COLORS = ["#7df9ff", "#7442ff"];

    return (
        <div className="flex flex-col items-center">
            <PieChart width={280} height={280}>
                <Pie
                    data={chartData}
                    cx={140}
                    cy={120}
                    outerRadius={90}
                    fill="#8884d8"
                    dataKey="value"
                    label
                >
                    {chartData.map((entry, idx) => (
                        <Cell key={`cell-${idx}`} fill={COLORS[idx]} />
                    ))}
                </Pie>
                <Tooltip
                    contentStyle={{
                        backgroundColor: "#0d1020",
                        border: "1px solid #7442ff",
                        borderRadius: "8px",
                        color: "#7df9ff",
                    }}
                />
                <Legend
                    wrapperStyle={{ color: "#7df9ff" }}
                    iconType="circle"
                />
            </PieChart>

            {/* Curvature Breakdown */}
            {data.curved_breakdown && Object.keys(data.curved_breakdown).length > 0 && (
                <div className="mt-4 w-full text-xs space-y-1 opacity-80">
                    <div className="font-semibold text-highlight mb-2">Curved Breakdown:</div>
                    {Object.entries(data.curved_breakdown).map(([type, count]) => (
                        <div key={type} className="flex justify-between px-2 py-1 bg-black/20 rounded">
                            <span>{type}</span>
                            <span className="text-neon">{count}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
