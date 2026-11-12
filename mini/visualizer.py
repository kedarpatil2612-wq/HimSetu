"""HimSetu Mini — Visualization Utilities.

Produces Plotly figures for the Streamlit dashboard:
  - Feature distributions (box + violin)
  - Ice probability spatial scatter (lat/lon heatmap)
  - Feature importance bar chart
  - Confusion matrix heatmap
  - Ice probability histogram
  - Correlation heatmap of features
"""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


_COLD_HOT_SCALE = [
    [0.0, "#1a1a5e"],
    [0.2, "#1c4e8f"],
    [0.4, "#2e9ad0"],
    [0.6, "#78d2a4"],
    [0.8, "#f5c518"],
    [1.0, "#e8432d"],
]


def plot_feature_distributions(df: pd.DataFrame, feature_cols: List[str]) -> go.Figure:
    """Violin + box plot for each feature, coloured by ice_potential if available."""
    has_label = "ice_potential" in df.columns

    fig = make_subplots(
        rows=1, cols=len(feature_cols),
        subplot_titles=feature_cols,
    )

    colors = {0: "#2e9ad0", 1: "#e8432d"}
    label_names = {0: "No Ice Potential", 1: "Ice Potential"}

    for i, col in enumerate(feature_cols, start=1):
        if col not in df.columns:
            continue
        if has_label:
            for lval in [0, 1]:
                sub = df[df["ice_potential"] == lval][col].dropna()
                fig.add_trace(
                    go.Violin(
                        y=sub,
                        name=label_names[lval],
                        line_color=colors[lval],
                        fillcolor=colors[lval],
                        opacity=0.5,
                        box_visible=True,
                        meanline_visible=True,
                        showlegend=(i == 1),
                    ),
                    row=1, col=i,
                )
        else:
            fig.add_trace(
                go.Violin(
                    y=df[col].dropna(),
                    name=col,
                    fillcolor="#2e9ad0",
                    opacity=0.7,
                    box_visible=True,
                    showlegend=False,
                ),
                row=1, col=i,
            )

    fig.update_layout(
        title_text="Feature Distributions",
        plot_bgcolor="#0d1117",
        paper_bgcolor="#0d1117",
        font=dict(color="#c9d1d9"),
        height=420,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )
    return fig


def plot_ice_probability_map(
    df: pd.DataFrame,
    ice_probability: Optional[np.ndarray] = None,
) -> go.Figure:
    """Scatter plot on lat/lon coloured by ice_probability (or ice_potential label)."""
    plot_df = df.copy()

    if ice_probability is not None:
        plot_df["ice_probability"] = np.round(ice_probability, 4)
        color_col = "ice_probability"
        color_label = "Ice Probability"
        color_scale = _COLD_HOT_SCALE
        range_color = [0.0, 1.0]
    elif "ice_potential" in df.columns:
        plot_df["ice_probability"] = df["ice_potential"].astype(float)
        color_col = "ice_probability"
        color_label = "Ice Potential Label (0/1)"
        color_scale = _COLD_HOT_SCALE
        range_color = [0.0, 1.0]
    else:
        plot_df["ice_probability"] = 0.5
        color_col = "ice_probability"
        color_label = "Uniform (no label)"
        color_scale = _COLD_HOT_SCALE
        range_color = [0.0, 1.0]

    fig = px.scatter(
        plot_df,
        x="longitude",
        y="latitude",
        color=color_col,
        color_continuous_scale=color_scale,
        range_color=range_color,
        labels={"longitude": "Longitude (°)", "latitude": "Latitude (°)", color_col: color_label},
        title="🌕 Lunar South Polar Ice Probability Map (Synthetic)",
        hover_data={
            "latitude": ":.2f",
            "longitude": ":.2f",
            color_col: ":.3f",
        },
    )

    fig.update_traces(marker=dict(size=7, opacity=0.85))
    fig.update_layout(
        plot_bgcolor="#0d1117",
        paper_bgcolor="#0d1117",
        font=dict(color="#c9d1d9"),
        height=500,
        xaxis=dict(gridcolor="#21262d", zeroline=False),
        yaxis=dict(gridcolor="#21262d", zeroline=False),
        coloraxis_colorbar=dict(title=color_label),
    )
    return fig


def plot_feature_importance(feature_importance: Dict[str, float]) -> go.Figure:
    """Horizontal bar chart of Random Forest feature importances."""
    names = list(feature_importance.keys())
    values = list(feature_importance.values())

    # Sort ascending for horizontal bar (Plotly shows last at top)
    sorted_pairs = sorted(zip(names, values), key=lambda x: x[1])
    s_names, s_vals = zip(*sorted_pairs)

    fig = go.Figure(
        go.Bar(
            x=s_vals,
            y=s_names,
            orientation="h",
            marker=dict(
                color=s_vals,
                colorscale="Blues",
                showscale=False,
            ),
        )
    )

    fig.update_layout(
        title_text="Feature Importance (Random Forest — Gini)",
        xaxis_title="Mean Decrease in Impurity",
        plot_bgcolor="#0d1117",
        paper_bgcolor="#0d1117",
        font=dict(color="#c9d1d9"),
        height=380,
        xaxis=dict(gridcolor="#21262d"),
        yaxis=dict(gridcolor="#21262d"),
    )
    return fig


def plot_confusion_matrix(cm: List[List[int]]) -> go.Figure:
    """Annotated confusion matrix heatmap."""
    labels = ["No Ice Potential", "Ice Potential"]
    cm_arr = np.array(cm)

    fig = go.Figure(
        go.Heatmap(
            z=cm_arr,
            x=labels,
            y=labels,
            colorscale="Blues",
            text=cm_arr,
            texttemplate="%{text}",
            showscale=True,
        )
    )

    fig.update_layout(
        title_text="Confusion Matrix",
        xaxis_title="Predicted",
        yaxis_title="Actual",
        plot_bgcolor="#0d1117",
        paper_bgcolor="#0d1117",
        font=dict(color="#c9d1d9"),
        height=350,
    )
    return fig


def plot_probability_histogram(ice_probability: np.ndarray) -> go.Figure:
    """Histogram of predicted ice probability distribution."""
    fig = go.Figure(
        go.Histogram(
            x=ice_probability,
            nbinsx=40,
            marker=dict(
                color=ice_probability,
                colorscale=_COLD_HOT_SCALE,
                cmin=0.0,
                cmax=1.0,
            ),
        )
    )
    fig.add_vline(x=0.5, line_dash="dash", line_color="#f5c518",
                  annotation_text="Decision Threshold (0.5)", annotation_position="top right")

    fig.update_layout(
        title_text="Ice Probability Score Distribution",
        xaxis_title="Ice Probability",
        yaxis_title="Count",
        plot_bgcolor="#0d1117",
        paper_bgcolor="#0d1117",
        font=dict(color="#c9d1d9"),
        height=350,
        xaxis=dict(range=[0, 1], gridcolor="#21262d"),
        yaxis=dict(gridcolor="#21262d"),
    )
    return fig


def plot_correlation_heatmap(df: pd.DataFrame, feature_cols: List[str]) -> go.Figure:
    """Correlation heatmap of selected numeric feature columns."""
    available = [c for c in feature_cols if c in df.columns]
    corr = df[available].corr().round(3)

    fig = go.Figure(
        go.Heatmap(
            z=corr.values,
            x=corr.columns.tolist(),
            y=corr.index.tolist(),
            colorscale="RdBu",
            zmid=0,
            text=corr.values.round(2),
            texttemplate="%{text}",
            colorbar=dict(title="r"),
        )
    )
    fig.update_layout(
        title_text="Feature Correlation Matrix",
        plot_bgcolor="#0d1117",
        paper_bgcolor="#0d1117",
        font=dict(color="#c9d1d9"),
        height=380,
    )
    return fig
