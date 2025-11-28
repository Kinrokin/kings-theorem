/**
 * API Communication Layer - Ouroboros Dashboard
 * Handles all fetch requests to FastAPI backend endpoints
 */

export async function fetchJSON(endpoint) {
    try {
        const res = await fetch(endpoint);
        if (!res.ok) return null;
        return await res.json();
    } catch (e) {
        console.error("API error:", endpoint, e);
        return null;
    }
}

export const getTribunal = () => fetchJSON("/api/tribunal_report");
export const getOptimization = () => fetchJSON("/api/optimization_signal");
export const getCurvature = () => fetchJSON("/api/curvature_metrics");
export const getTribunalSample = (id) =>
    fetchJSON(`/api/tribunal_sample?id=${encodeURIComponent(id)}`);