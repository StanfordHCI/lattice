from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Callable
from models import Separator


class LatticeLayer(ABC):
    """Base class for all lattice layers, analogous to torch.nn.Module."""

    @abstractmethod
    def split(self, nodes: list) -> list[list]:
        """Split a flat list of nodes into groups for LLM synthesis."""
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


class SessionLayer(LatticeLayer):
    """Group nodes by N consecutive sessions.

    Example:
        SessionLayer(n=1)   # each session becomes one group
        SessionLayer(n=10)  # every 10 sessions become one group
    """

    def __init__(self, n: int = 1):
        if n < 1:
            raise ValueError(f"n must be >= 1; got {n}")
        self.n = n

    def split(self, nodes: list) -> list[list]:
        missing = [i for i, nd in enumerate(nodes) if "input_session" not in nd.get("metadata", {})]
        if missing:
            raise ValueError(f"Nodes at indices {missing} are missing 'input_session' in metadata.")

        sorted_nodes = sorted(nodes, key=lambda nd: nd["metadata"]["input_session"])

        session_buckets: dict[int, list] = {}
        for nd in sorted_nodes:
            sid = nd["metadata"]["input_session"]
            session_buckets.setdefault(sid, []).append(nd)

        ordered = list(session_buckets.values())
        groups = []
        for i in range(0, len(ordered), self.n):
            chunk = ordered[i : i + self.n]
            groups.append([nd for session in chunk for nd in session])
        return groups

    def __repr__(self) -> str:
        return f"SessionLayer(n={self.n})"


class TimeLayer(LatticeLayer):
    """Group nodes by calendar period.

    Args:
        by: One of "day", "week", "month", "year".

    Example:
        TimeLayer(by="week")
    """

    _VALID = ("day", "week", "month", "year")

    def __init__(self, by: str = "day"):
        if by not in self._VALID:
            raise ValueError(f"by must be one of {self._VALID}; got {by!r}")
        self.by = by

    def split(self, nodes: list) -> list[list]:
        missing = [i for i, nd in enumerate(nodes) if "time" not in nd.get("metadata", {})]
        if missing:
            raise ValueError(f"Nodes at indices {missing} are missing 'time' in metadata.")

        def bucket_key(nd):
            dt = datetime.fromisoformat(nd["metadata"]["time"])
            if self.by == "day":
                return (dt.year, dt.month, dt.day)
            elif self.by == "week":
                iso = dt.isocalendar()
                return (iso.year, iso.week)
            elif self.by == "month":
                return (dt.year, dt.month)
            else:  # year
                return (dt.year,)

        sorted_nodes = sorted(nodes, key=bucket_key)
        groups: list[list] = []
        current_key = None
        for nd in sorted_nodes:
            key = bucket_key(nd)
            if key != current_key:
                groups.append([])
                current_key = key
            groups[-1].append(nd)
        return groups

    def __repr__(self) -> str:
        return f"TimeLayer(by={self.by!r})"


class NumberLayer(LatticeLayer):
    """Group nodes into fixed-size chunks of N, regardless of session or time.

    Example:
        NumberLayer(n=20)  # every 20 nodes become one group
    """

    def __init__(self, n: int):
        if n < 1:
            raise ValueError(f"n must be >= 1; got {n}")
        self.n = n

    def split(self, nodes: list) -> list[list]:
        return [nodes[i : i + self.n] for i in range(0, len(nodes), self.n)]

    def __repr__(self) -> str:
        return f"NumberLayer(n={self.n})"


class AllLayer(LatticeLayer):
    """Collapse all nodes into a single group.

    Useful as the final layer to produce one top-level insight.
    """

    def split(self, nodes: list) -> list[list]:
        return [nodes]

    def __repr__(self) -> str:
        return "AllLayer()"


class CustomLayer(LatticeLayer):
    """Group nodes using an arbitrary splitting function.

    Args:
        fn: Callable that takes a flat list of nodes and returns a list of
            groups (list[list]).  Each group is processed as one unit by the
            LLM synthesis step.

    Example:
        def split_by_topic(nodes):
            return [group_a, group_b]

        CustomLayer(fn=split_by_topic)
    """

    def __init__(self, fn: Callable[[list], list[list]]):
        self.fn = fn

    def split(self, nodes: list) -> list[list]:
        return self.fn(nodes)

    def __repr__(self) -> str:
        return f"CustomLayer(fn={self.fn.__name__})"


def layer_from_dict(type: str, value: str) -> LatticeLayer:
    """Construct a LatticeLayer from a legacy config entry."""
    if type == "session":
        return SessionLayer(n=int(value))
    elif type == "time":
        return TimeLayer(by=value)
    elif type == "number":
        return NumberLayer(n=int(value))
    elif type == "all":
        return AllLayer()
    else:
        raise ValueError(f"Unknown layer type: {type!r}")


class Sequential:
    """Ordered container of LatticeLayer objects, analogous to torch.nn.Sequential.

    Example:
        layers = Sequential(
            SessionLayer(n=1),
            SessionLayer(n=10),
        )
        await lattice.build(layers)
    """

    def __init__(self, *layers: LatticeLayer):
        self.layers = list(layers)

    def __getitem__(self, idx: int) -> LatticeLayer:
        return self.layers[idx]

    def __len__(self) -> int:
        return len(self.layers)

    def __iter__(self):
        return iter(self.layers)

    def __repr__(self) -> str:
        inner = "\n  ".join(repr(l) for l in self.layers)
        return f"Sequential(\n  {inner}\n)"
