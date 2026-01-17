# tool_functions/plot_from_data.py
import base64
import io
from typing import Dict, List, Optional, Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _plot_series(ax, series: dict, default_kind: str, categorical_labels: Optional[List[str]] = None):
    name = series.get("name")
    x_vals = series.get("x")
    y_vals = series.get("y")
    kind = series.get("kind", default_kind)

    if y_vals is None:
        raise ValueError("Series is missing 'y' values")

    if x_vals is None:
        x_vals = list(range(1, len(y_vals) + 1))
    elif categorical_labels is not None:
        x_vals = list(range(1, len(categorical_labels) + 1))

    if kind == "bar":
        ax.bar(x_vals, y_vals, label=name)
    elif kind == "scatter":
        ax.scatter(x_vals, y_vals, label=name)
    else:
        ax.plot(x_vals, y_vals, label=name)


def _coerce_kind(kind: Optional[str], default_kind: str) -> str:
    if not kind:
        return default_kind
    k = str(kind).strip().lower()
    if k not in ("line", "scatter", "bar"):
        raise ValueError("kind must be one of: line, scatter, bar")
    return k


def _coerce_mode(mode: Optional[str], series: Optional[List[dict]]) -> str:
    if mode is None:
        return "multi" if series is not None else "single"
    m = str(mode).strip().lower()
    if m not in ("single", "multi"):
        raise ValueError("mode must be 'single' or 'multi'")
    return m


def plot_from_data(
    mode: Optional[str] = None,
    y: Optional[List[float]] = None,
    x: Optional[List[float]] = None,
    labels: Optional[List[str]] = None,
    series: Optional[List[dict]] = None,
    title: str = "Plot",
    xlabel: str = "X",
    ylabel: str = "Y",
    kind: str = "line",
) -> Dict[str, Any]:
    """
    Generate a plot image from raw data and return it as a base64 PNG.

    Enforcement of required fields is done here (because the Responses API tool schema
    subset rejects oneOf/anyOf/allOf/enum conditionals at the top level).
    """
    categorical_labels = None

    mode = _coerce_mode(mode, series)
    kind = _coerce_kind(kind, "line")

    if mode == "single":
        if y is None or len(y) == 0:
            raise ValueError("Provide non-empty 'y' for mode='single'")
        if x is not None and len(x) != len(y):
            raise ValueError("'x' length must match 'y' length")
        if labels is not None and len(labels) != len(y):
            raise ValueError("'labels' length must match 'y' length")
    else:
        if not series:
            raise ValueError("Provide non-empty 'series' for mode='multi'")

    if series is None:
        if labels is not None:
            categorical_labels = labels
            x = list(range(1, len(labels) + 1))
        series = [{"name": None, "x": x, "y": y, "kind": kind}]
    else:
        # Validate series entries and detect categorical labels if present
        cleaned = []
        for entry in series:
            if not isinstance(entry, dict):
                raise ValueError("Each entry in 'series' must be an object")
            y_vals = entry.get("y")
            if y_vals is None or len(y_vals) == 0:
                raise ValueError("Each series entry must include non-empty 'y'")
            entry_kind = _coerce_kind(entry.get("kind"), kind)
            x_vals = entry.get("x")

            # If the caller provides labels for categorical x, prefer using 'labels' at the top-level.
            # (We keep the schema numeric-only for x to satisfy tool schema restrictions.)
            cleaned.append(
                {
                    "name": entry.get("name"),
                    "x": x_vals,
                    "y": y_vals,
                    "kind": entry_kind,
                }
            )
        series = cleaned

    fig, ax = plt.subplots(figsize=(8, 4.5))
    for entry in series:
        _plot_series(ax, entry, kind, categorical_labels=categorical_labels)

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    if categorical_labels is not None:
        ax.set_xticks(list(range(1, len(categorical_labels) + 1)))
        ax.set_xticklabels(categorical_labels)

    if any(s.get("name") for s in series):
        ax.legend()

    ax.grid(True, alpha=0.3)

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)

    image_b64 = base64.b64encode(buf.read()).decode("utf-8")
    return {"text": "Plot generated.", "attachments": [image_b64]}


# Responses API tool spec: MUST be a top-level object schema and must NOT include
# oneOf/anyOf/allOf/enum/not at the top level (or conditionals).
TOOL_SPEC: Dict[str, Any] = {
    "type": "function",
    "name": "plot_from_data",
    "description": (
        "Generate a plot image from numeric data and return it as an attachment. "
        "Call only when you have the data. "
        "Arguments: mode ('single' or 'multi'), y/x/labels for single, or series for multi. "
        "kind should be one of: line, scatter, bar."
    ),
    "parameters": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "mode": {
                "type": "string",
                "description": "Either 'single' or 'multi'. If omitted, defaults based on whether 'series' is provided.",
            },
            "y": {
                "type": "array",
                "items": {"type": "number"},
                "description": "Y values for a single series (required when mode='single').",
            },
            "x": {
                "type": "array",
                "items": {"type": "number"},
                "description": "Optional numeric X values for a single series (same length as y).",
            },
            "labels": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional categorical labels for a single series (same length as y).",
            },
            "series": {
                "type": "array",
                "description": "Multiple series objects (required when mode='multi').",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "name": {"type": "string", "description": "Legend label for the series."},
                        "x": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "Optional numeric X values for this series (same length as y).",
                        },
                        "y": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "Y values for this series (required).",
                        },
                        "kind": {
                            "type": "string",
                            "description": "One of: line, scatter, bar. If omitted, falls back to top-level kind.",
                        },
                    },
                },
            },
            "title": {"type": "string", "description": "Plot title."},
            "xlabel": {"type": "string", "description": "X-axis label."},
            "ylabel": {"type": "string", "description": "Y-axis label."},
            "kind": {"type": "string", "description": "One of: line, scatter, bar (used for single series and as default for multi)."},
        },
    },
}

TOOL_FN = plot_from_data
