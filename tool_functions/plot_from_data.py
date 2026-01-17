import base64
import io
from typing import Dict, List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _plot_series(ax, series: dict, default_kind: str):
    name = series.get("name")
    x_vals = series.get("x")
    y_vals = series.get("y")
    kind = series.get("kind", default_kind)

    if y_vals is None:
        raise ValueError("Series is missing 'y' values")
    if x_vals is None:
        x_vals = list(range(1, len(y_vals) + 1))

    if kind == "bar":
        ax.bar(x_vals, y_vals, label=name)
    elif kind == "scatter":
        ax.scatter(x_vals, y_vals, label=name)
    else:
        ax.plot(x_vals, y_vals, label=name)


def plot_from_data(
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
    if series is None:
        if y is None:
            raise ValueError("Provide 'y' or 'series'")
        if labels is not None:
            if len(labels) != len(y):
                raise ValueError("'labels' length must match 'y' length")
            x = labels
        series = [{"name": None, "x": x, "y": y, "kind": kind}]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    for entry in series:
        _plot_series(ax, entry, kind)

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
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
        "description": "Generate a plot image from raw numeric data and return it as an attachment.",
        "parameters": {
            "type": "object",
            "properties": {
                "y": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Y values for a single series.",
                },
                "x": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Optional X values for a single series.",
                },
                "labels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional labels for a single series (same length as y).",
                },
                "series": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "x": {"type": "array", "items": {"type": "number"}},
                            "y": {"type": "array", "items": {"type": "number"}},
                            "kind": {"type": "string"},
                        },
                    },
                    "description": "Multiple series to plot.",
                },
                "title": {"type": "string"},
                "xlabel": {"type": "string"},
                "ylabel": {"type": "string"},
                "kind": {"type": "string", "description": "line, scatter, or bar"},
            },
            "anyOf": [
                {"required": ["y"]},
                {"required": ["series"]}
            ],
        },
    },
}

TOOL_FN = plot_from_data
