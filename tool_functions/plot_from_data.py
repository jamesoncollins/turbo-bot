import base64
import io
from typing import Dict, List, Optional

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
) -> Dict:
    """
    Generate a plot image from raw data and return it as a base64 PNG.

    Args:
        y: List of Y values for a single series.
        x: Optional list of X values for a single series.
        series: Optional list of series objects with keys: name, x, y, kind.
        title: Plot title.
        xlabel: X-axis label.
        ylabel: Y-axis label.
        kind: One of line, scatter, bar (used for single series).
    """
    categorical_labels = None
    if mode is None:
        if series is not None:
            mode = "multi"
        else:
            mode = "single"

    if mode not in ("single", "multi"):
        raise ValueError("mode must be 'single' or 'multi'")

    if mode == "single":
        if y is None:
            raise ValueError("Provide 'y' for mode='single'")
    else:
        if not series:
            raise ValueError("Provide 'series' for mode='multi'")

    if series is None:
        if labels is not None:
            if len(labels) != len(y):
                raise ValueError("'labels' length must match 'y' length")
            categorical_labels = labels
            x = list(range(1, len(labels) + 1))
        series = [{"name": None, "x": x, "y": y, "kind": kind}]
    else:
        for entry in series:
            x_vals = entry.get("x")
            if x_vals and isinstance(x_vals[0], str):
                categorical_labels = x_vals
                break

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


TOOL_SPEC: Dict = {
    "type": "function",
    "name": "plot_from_data",
    "function": {
        "name": "plot_from_data",
        "description": (
            "Generate a plot image from numeric data and return it as an attachment. "
            "Never call this tool without providing data. "
            "Use mode='single' with y (and optional x), or mode='multi' with series."
        ),
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "required": ["mode"],
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["single", "multi"],
                    "description": "Use 'single' for one series (y required). Use 'multi' for multiple series (series required).",
                },
                "y": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Y values for a single series (required when mode='single'). Example: [0, 1, 4, 9]",
                    "minItems": 1,
                },
                "x": {
                    "type": "array",
                    "items": {"anyOf": [{"type": "number"}, {"type": "string"}]},
                    "description": "Optional X values for a single series (same length as y).",
                    "minItems": 1,
                },
                "labels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional labels for a single series (same length as y).",
                    "minItems": 1,
                },
                "series": {
                    "type": "array",
                    "minItems": 1,
                    "description": "Multiple series to plot (required when mode='multi').",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["y"],
                        "properties": {
                            "name": {"type": "string"},
                            "x": {"type": "array", "items": {"anyOf": [{"type": "number"}, {"type": "string"}]}},
                            "y": {"type": "array", "items": {"type": "number"}, "minItems": 1},
                            "kind": {"type": "string", "enum": ["line", "scatter", "bar"]},
                        },
                    },
                },
                "title": {"type": "string"},
                "xlabel": {"type": "string"},
                "ylabel": {"type": "string"},
                "kind": {"type": "string", "enum": ["line", "scatter", "bar"]},
            },
            "allOf": [
                {
                    "if": {"properties": {"mode": {"const": "single"}}},
                    "then": {"required": ["y"]},
                },
                {
                    "if": {"properties": {"mode": {"const": "multi"}}},
                    "then": {"required": ["series"]},
                },
            ],
        },
    },
}

TOOL_FN = plot_from_data
