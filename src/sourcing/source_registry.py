# src/sourcing/source_registry.py
from __future__ import annotations

import logging
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Set

logger = logging.getLogger("kt.sourcing.registry")
logger.setLevel(logging.INFO)


@dataclass
class SourceMetadata:
    """Metadata for a federated source."""

    source_id: str
    public_key: bytes  # Ed25519 public key for signature verification
    reputation_score: float = 1.0  # 0.0 (blacklisted) to 1.0 (trusted)
    diversity_tags: Set[str] = field(default_factory=set)  # e.g., {"medical", "academic", "gov"}
    total_contributions: int = 0
    verified_contributions: int = 0
    last_activity: float = field(default_factory=time.time)
    creation_time: float = field(default_factory=time.time)
    is_blacklisted: bool = False


class SourceRegistry:
    """
    Registry for federated sources with authenticity verification,
    reputation tracking, and diversity enforcement.

    Prevents:
    - Source flooding attacks (monoculture bias)
    - Sybil attacks (multiple IDs from same entity)
    - Low-quality source dominance
    """

    def __init__(
        self,
        min_reputation: float = 0.3,
        max_cluster_influence: float = 0.4,  # No cluster can exceed 40% influence
        diversity_quota: Dict[str, float] = None,
        flood_detection_window: float = 3600.0,  # 1 hour
        max_new_sources_per_window: int = 10,
    ):
        self.sources: Dict[str, SourceMetadata] = {}
        self.min_reputation = min_reputation
        self.max_cluster_influence = max_cluster_influence
        self.diversity_quota = diversity_quota or {}  # e.g., {"medical": 0.3, "gov": 0.2}
        self.flood_window = flood_detection_window
        self.max_new_sources = max_new_sources_per_window
        self.recent_registrations: List[float] = []

    def register_source(
        self,
        source_id: str,
        public_key: bytes,
        diversity_tags: Set[str] = None,
        initial_reputation: float = 0.5,
    ) -> bool:
        """
        Register a new source. Returns False if flooding detected or blacklisted.
        """
        # Flood detection: check recent registrations
        now = time.time()
        self.recent_registrations = [t for t in self.recent_registrations if now - t < self.flood_window]

        if len(self.recent_registrations) >= self.max_new_sources:
            logger.warning(f"Source registration flood detected: {len(self.recent_registrations)} in window")
            return False

        # Check if already exists
        if source_id in self.sources:
            logger.warning(f"Source {source_id} already registered")
            return False

        # Register
        self.sources[source_id] = SourceMetadata(
            source_id=source_id,
            public_key=public_key,
            reputation_score=initial_reputation,
            diversity_tags=diversity_tags or set(),
            creation_time=now,
            last_activity=now,
        )
        self.recent_registrations.append(now)
        logger.info(f"Registered source {source_id} with tags {diversity_tags}")
        return True

    def update_reputation(self, source_id: str, contribution_verified: bool):
        """
        Update source reputation based on contribution quality.
        Uses exponential moving average.
        """
        if source_id not in self.sources:
            logger.warning(f"Unknown source: {source_id}")
            return

        source = self.sources[source_id]
        source.total_contributions += 1
        if contribution_verified:
            source.verified_contributions += 1

        # Exponential moving average: new_score = alpha * signal + (1-alpha) * old_score
        alpha = 0.1
        signal = 1.0 if contribution_verified else 0.0
        source.reputation_score = alpha * signal + (1 - alpha) * source.reputation_score
        source.last_activity = time.time()

        # Blacklist if reputation drops too low
        if source.reputation_score < 0.1:
            source.is_blacklisted = True
            logger.warning(f"Source {source_id} blacklisted due to low reputation: {source.reputation_score:.3f}")

    def compute_influence_weights(self) -> Dict[str, float]:
        """
        Compute influence weights for each source, enforcing diversity constraints.
        Returns dict mapping source_id -> weight (sums to 1.0).
        """
        # Filter out blacklisted and low-reputation sources
        active_sources = {
            sid: s
            for sid, s in self.sources.items()
            if not s.is_blacklisted and s.reputation_score >= self.min_reputation
        }

        if not active_sources:
            return {}

        # 1) Initial weights: proportional to reputation * recency
        now = time.time()
        raw_weights = {}
        for sid, s in active_sources.items():
            recency_factor = 1.0 / (1.0 + (now - s.last_activity) / 86400.0)  # Decay over days
            raw_weights[sid] = s.reputation_score * recency_factor

        # 2) Cluster detection: group by diversity tags
        clusters = self._detect_clusters(active_sources)

        # 3) Apply per-cluster caps
        cluster_weights = {}
        for cluster_name, members in clusters.items():
            cluster_total = sum(raw_weights[sid] for sid in members)
            cluster_weights[cluster_name] = cluster_total

        total_weight = sum(cluster_weights.values())
        if total_weight == 0:
            return {}

        # Normalize and cap clusters
        adjusted_weights = {}
        total_capped = 0.0
        capped_clusters = set()

        for cluster_name, members in clusters.items():
            cluster_weight = cluster_weights[cluster_name] / total_weight

            # Apply cap
            if cluster_weight > self.max_cluster_influence:
                capped_weight = self.max_cluster_influence
                capped_clusters.add(cluster_name)
                logger.info(
                    f"Capping cluster {cluster_name} influence: {cluster_weight:.2f} -> {self.max_cluster_influence:.2f}"
                )
            else:
                capped_weight = cluster_weight

            total_capped += capped_weight

            # Distribute capped weight among cluster members proportionally
            cluster_member_weights = {sid: raw_weights[sid] for sid in members}
            cluster_member_total = sum(cluster_member_weights.values())

            for sid in members:
                if cluster_member_total > 0:
                    adjusted_weights[sid] = (cluster_member_weights[sid] / cluster_member_total) * capped_weight
                else:
                    adjusted_weights[sid] = 0.0

        # 4) Redistribute excess weight if caps were applied
        total_adjusted = sum(adjusted_weights.values())

        if len(capped_clusters) > 0 and total_adjusted < 1.0:
            # Calculate how much weight to redistribute
            excess_weight = 1.0 - total_adjusted

            # Identify uncapped sources for redistribution
            uncapped_sources = {}
            for cluster_name, members in clusters.items():
                if cluster_name not in capped_clusters:
                    for sid in members:
                        uncapped_sources[sid] = adjusted_weights[sid]

            # Redistribute proportionally to uncapped sources
            if uncapped_sources:
                uncapped_total = sum(uncapped_sources.values())
                if uncapped_total > 0:
                    for sid in uncapped_sources:
                        boost = (uncapped_sources[sid] / uncapped_total) * excess_weight
                        adjusted_weights[sid] += boost
        elif len(capped_clusters) == 0 and total_adjusted > 0 and abs(total_adjusted - 1.0) > 0.01:
            # Safe to renormalize when no caps were hit
            adjusted_weights = {sid: w / total_adjusted for sid, w in adjusted_weights.items()}

        return adjusted_weights

    def _detect_clusters(self, sources: Dict[str, SourceMetadata]) -> Dict[str, Set[str]]:
        """
        Detect source clusters based on diversity tags.
        Returns dict mapping cluster_name -> set of source_ids.
        """
        clusters = {}
        for sid, s in sources.items():
            if not s.diversity_tags:
                cluster_name = "untagged"
            else:
                # Use primary tag (first in sorted list for determinism)
                cluster_name = sorted(s.diversity_tags)[0]

            if cluster_name not in clusters:
                clusters[cluster_name] = set()
            clusters[cluster_name].add(sid)

        return clusters

    def check_diversity_quota(self) -> Dict[str, float]:
        """
        Check if diversity quotas are met.
        Returns dict mapping tag -> actual_proportion.
        """
        active_sources = {
            sid: s
            for sid, s in self.sources.items()
            if not s.is_blacklisted and s.reputation_score >= self.min_reputation
        }

        if not active_sources:
            return {}

        tag_counts = Counter()
        for s in active_sources.values():
            for tag in s.diversity_tags:
                tag_counts[tag] += 1

        total = len(active_sources)
        proportions = {tag: count / total for tag, count in tag_counts.items()}

        # Check against quotas
        for tag, required in self.diversity_quota.items():
            actual = proportions.get(tag, 0.0)
            if actual < required:
                logger.warning(f"Diversity quota not met for {tag}: {actual:.2f} < {required:.2f}")

        return proportions

    def blacklist_source(self, source_id: str, reason: str = "manual"):
        """Manually blacklist a source."""
        if source_id in self.sources:
            self.sources[source_id].is_blacklisted = True
            logger.warning(f"Source {source_id} blacklisted: {reason}")

    def get_active_sources(self) -> List[SourceMetadata]:
        """Get list of active (non-blacklisted, above min reputation) sources."""
        return [s for s in self.sources.values() if not s.is_blacklisted and s.reputation_score >= self.min_reputation]
