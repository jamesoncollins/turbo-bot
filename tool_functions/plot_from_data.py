# tool_functions/plot_from_data.py
import base64
import io
from typing import Dict, List, Optional, Any, Sequence

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _as_float_list(vals: Any, field_name: str) -> List[float]:
    if vals is None:
        raise ValueError(f"Missing '{field_name}'")
    if not isinstance(vals, (list, tuple)):
        raise ValueError(f"'{field_name}' must be a list")
    out: List[float] = []
    for i, v in enumerate(vals):
        try:
            out.append(float(v))
        except Exception:
            raise ValueError(f"'{field_name}[{i}]' is not numeric: {v!r}")
    if len(out) == 0:
        raise ValueError(f"'{field_name}' must be non-empty")
    return out


def _plot_series(ax, series: dict, default_kind: str, categorical_labels: Optional[List[str]] = None):
    name = series.get("name")
    x_vals = series.get("x")
    y_vals_raw = series.get("y")
    kind = series.get("kind", default_kind)

    y_vals = _as_float_list(y_vals_raw, "y")

    if x_vals is None:
        x_vals = list(range(1, len(y_vals) + 1))
    else:
        # If categorical labels are in use, use 1..N for x positions
        if categorical_labels is not None:
            x_vals = list(range(1, len(categorical_labels) + 1))
        else:
            # numeric x
            x_vals = _as_float_list(x_vals, "x")
            if len(x_vals) != len(y_vals):
                raise ValueError("'x' length must match 'y' length")

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
        return "multi" if series else "single"
    m = str(mode).strip().lower()
    if m not in ("single", "multi"):
        raise ValueError("mode must be 'single' or 'multi'")
    return m


def _apply_sane_y_limits(ax, y_all: Sequence[float]) -> None:
    y_min = min(y_all)
    y_max = max(y_all)
    if y_min == y_max:
        pad = 1.0 if y_min == 0 else abs(y_min) * 0.05
        ax.set_ylim(y_min - pad, y_max + pad)
        return
    pad = (y_max - y_min) * 0.10
    ax.set_ylim(y_min - pad, y_max + pad)


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
    categorical_labels = None

    # Treat empty series as "not provided" (models sometimes include series: [])
    if isinstance(series, list) and len(series) == 0:
        series = None

    mode = _coerce_mode(mode, series)
    kind = _coerce_kind(kind, "line")

    plotted_y_values: List[float] = []

    if mode == "single":
        y_vals = _as_float_list(y, "y")

        if labels is not None:
            if not isinstance(labels, list) or len(labels) != len(y_vals):
                raise ValueError("'labels' length must match 'y' length")
            categorical_labels = labels
            x_vals = list(range(1, len(labels) + 1))
        else:
            x_vals = None if x is None else _as_float_list(x, "x")
            if x_vals is not None and len(x_vals) != len(y_vals):
                raise ValueError("'x' length must match 'y' length")

        series_to_plot = [{"name": None, "x": x_vals, "y": y_vals, "kind": kind}]
        plotted_y_values.extend(y_vals)

    else:
        if not series:
            raise ValueError("Provide non-empty 'series' for mode='multi'")

        series_to_plot = []
        for entry in series:
            if not isinstance(entry, dict):
                raise ValueError("Each entry in 'series' must be an object")

            entry_y = _as_float_list(entry.get("y"), "series.y")
            entry_kind = _coerce_kind(entry.get("kind"), kind)

            entry_x = entry.get("x")
            # Keep x numeric-only in tool calls; categorical should use top-level labels in single mode
            if entry_x is not None:
                entry_x = _as_float_list(entry_x, "series.x")
                if len(entry_x) != len(entry_y):
                    raise ValueError("series.x length must match series.y length")

            series_to_plot.append(
                {"name": entry.get("name"), "x": entry_x, "y": entry_y, "kind": entry_kind}
            )
            plotted_y_values.extend(entry_y)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    for entry in series_to_plot:
        _plot_series(ax, entry, kind, categorical_labels=categorical_labels)

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    if categorical_labels is not None:
        ax.set_xticks(list(range(1, len(categorical_labels) + 1)))
        ax.set_xticklabels(categorical_labels)

    if any(s.get("name") for s in series_to_plot):
        ax.legend()

    ax.grid(True, alpha=0.3)

    if plotted_y_values:
        _apply_sane_y_limits(ax, plotted_y_values)

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)

    image_b64 = base64.b64encode(buf.read()).decode("utf-8")
    return {"text": "Plot generated.", "attachments": [image_b64]}


TOOL_SPEC: Dict[str, Any] = {
    "type": "function",
    "name": "plot_from_data",
    "description": (
        "Generate a plot image from numeric data and return it as an attachment. "
        "Only call when you have the data. "
        "For categorical x in single-series plots, prefer 'labels' + 'y'."
    ),
    "parameters": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "mode": {"type": "string", "description": "single or multi"},
            "y": {"type": "array", "items": {"type": "number"}, "description": "Y values for single"},
            "x": {"type": "array", "items": {"type": "number"}, "description": "Optional X values for single"},
            "labels": {"type": "array", "items": {"type": "string"}, "description": "Optional categorical labels"},
            "series": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "name": {"type": "string"},
                        "x": {"type": "array", "items": {"type": "number"}},
                        "y": {"type": "array", "items": {"type": "number"}},
                        "kind": {"type": "string"},
                    },
                },
            },
            "title": {"type": "string"},
            "xlabel": {"type": "string"},
            "ylabel": {"type": "string"},
            "kind": {"type": "string"},
        },
    },
}

TOOL_FN = plot_from_data
