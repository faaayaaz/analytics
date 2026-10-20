import plotly.express as px
import streamlit as st

COLORS = ["#009e98", "#173454", "#4b82b8", "#efb44f", "#a178b6", "#db6b67"]


def show(fig, key=None):
    fig.update_layout(
        template="plotly_white",
        colorway=COLORS,
        font=dict(family="Arial", color="#20344c"),
        margin=dict(l=12, r=12, t=45, b=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend_title_text="",
        hovermode="closest",
    )
    st.plotly_chart(fig, width="stretch", key=key, config={"displaylogo": False})


def line(data, x, y, title, color=None):
    return px.line(
        data,
        x=x,
        y=y,
        color=color,
        title=title,
        markers=True,
        color_discrete_sequence=COLORS,
    )


def bar(data, x, y, title, color=None):
    return px.bar(
        data, x=x, y=y, color=color, title=title, color_discrete_sequence=COLORS
    )
