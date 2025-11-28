/**
 * MetricCard Component - Key-value pair display
 */
export default function MetricCard({ label, value }) {
    return (
        <div className="flex justify-between py-1.5 border-b border-white/5 last:border-0">
            <span className="opacity-70">{label}</span>
            <span className="font-semibold text-neon">{value}</span>
        </div>
    );
}
