/**
 * RewardChart Component - Line chart showing reward trajectory over iterations
 */
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from "recharts";

export default function RewardChart({ history }) {
    if (!history || history.length === 0) {
        return <div className="text-gray-400 p-4">No reward data yet. Start Ouroboros runner to see trajectory.</div>;
    }

    return (
        <ResponsiveContainer width="100%" height={300}>
            <LineChart data={history}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1a1f3a" />
                <XAxis
                    dataKey="iteration"
                    stroke="#7df9ff"
                    label={{ value: "Iteration", position: "insideBottom", offset: -5, fill: "#7df9ff" }}
                />
                <YAxis
                    domain={[0, 1]}
                    stroke="#7df9ff"
                    label={{ value: "Reward", angle: -90, position: "insideLeft", fill: "#7df9ff" }}
                />
                <Tooltip
                    contentStyle={{
                        backgroundColor: "#0d1020",
                        border: "1px solid #7442ff",
                        borderRadius: "8px",
                        color: "#7df9ff",
                    }}
                    formatter={(value) => value.toFixed(4)}
                />
                <Line
                    type="monotone"
                    dataKey="reward"
                    stroke="#7442ff"
                    strokeWidth={3}
                    dot={{ fill: "#7df9ff", r: 4 }}
                    activeDot={{ r: 6 }}
                />
            </LineChart>
        </ResponsiveContainer>
    );
}
