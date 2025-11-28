/**
 * Card Component - Reusable panel with neon accent border
 */
export default function Card({ title, children }) {
    return (
        <div className="bg-panel rounded-xl p-5 shadow-xl border border-highlight/20 transition-all hover:border-highlight/40">
            <h2 className="text-xl mb-3 font-semibold text-neon">{title}</h2>
            {children}
        </div>
    );
}
