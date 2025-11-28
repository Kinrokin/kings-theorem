# src/reasoning/dependency_graph.py
from __future__ import annotations

from typing import Dict, List, Set


class DependencyGraph:
    """
    Simple dependency graph for kernels. Nodes are kernel_ids; edges indicate shared dependency.
    """

    def __init__(self):
        self.adj: Dict[str, Set[str]] = {}  # kernel_id -> set(kernel_id)

    def add_node(self, kernel_id: str):
        self.adj.setdefault(kernel_id, set())

    def add_edge(self, a: str, b: str):
        self.add_node(a)
        self.add_node(b)
        self.adj[a].add(b)
        self.adj[b].add(a)

    def neighbors(self, kernel_id: str) -> Set[str]:
        return self.adj.get(kernel_id, set())

    def connected_components(self) -> List[Set[str]]:
        visited = set()
        comps = []
        for n in self.adj:
            if n in visited:
                continue
            stack = [n]
            comp = set()
            while stack:
                u = stack.pop()
                if u in visited:
                    continue
                visited.add(u)
                comp.add(u)
                for v in self.adj.get(u, ()):
                    if v not in visited:
                        stack.append(v)
            comps.append(comp)
        return comps
