import plotly.express as px
import streamlit as st

COLORS = ["#009e98", "#173454", "#4b82b8", "#efb44f", "#a178b6", "#db6b67"]


LABELS = {
    "month": "Month",
    "sales": "Net sales (AED)",
    "quantity": "Net demand (EA)",
    "cost": "Cost of sales (AED)",
    "product": "Product code",
    "category": "Category",
    "division": "Division",
    "channel": "Sales channel",
    "demand_cv": "Demand CV",
    "net_sales_aed": "Net sales (AED)",
    "net_units": "Net demand (EA)",
    "growth_pct": "Demand growth (%)",
    "abc": "ABC revenue class",
    "SKUs": "Products",
}


def chart_guide(fig):
    title = (fig.layout.title.text or "").lower()
    guides = [
        (
            "division sales and gross margin",
            "Bars use the left axis for signed net sales in AED. The line uses the right axis for gross margin: (sales − cost) / sales × 100. Compare revenue scale and profitability separately.",
        ),
        (
            "pareto",
            "Products are sorted by positive net revenue. Bars show AED sales on the left axis; the line shows cumulative eligible revenue percentage on the right. Boundary-crossing products stay in their starting ABC class. Nonpositive-revenue products are excluded.",
        ),
        (
            "abc distribution",
            "Each bar counts products in an ABC revenue class. A and B use your configured cumulative revenue boundaries; C is the remainder. N means nonpositive revenue, outside the standard ABC ranking.",
        ),
        (
            "abc–xyz",
            "Rows are revenue classes A/B/C; columns are demand variability X/Y/Z. Each cell counts products. Darker cells contain more products, not greater inventory risk. N classifications are excluded. Use the segment selector below for recommendations.",
        ),
        (
            "adjacent-month",
            "Rows are divisions and columns are months. Each cell shows net-demand growth versus the preceding calendar month. Green indicates growth and red indicates decline; neither alone proves good or bad performance. Blank cells mean no valid positive prior denominator or an excluded prior month.",
        ),
        (
            "historical net demand",
            "The solid line is observed 2024 net demand in EA. Dashed lines are January–March 2025 baseline and scenario estimates. Hover to compare values; click a legend item to hide or restore a series. Estimates are not purchase requirements.",
        ),
        (
            "top 10",
            "Products are ranked by signed net sales in AED within the dashboard filters. Taller bars indicate more revenue, not more units or stock. Hover over each bar for its product and exact sales.",
        ),
        (
            "category net sales",
            "Horizontal bars compare signed net revenue by category in AED. Longer bars mean larger revenue contribution in the selected scope. Returns and credits remain included.",
        ),
        (
            "channel net revenue",
            "Bars show signed net sales in AED by customer sales channel. Compare commercial contribution; this is not physical channel inventory or forecast demand.",
        ),
        (
            "monthly net sales",
            "Each point is the signed net sales total in AED for an included month. Returns and credits reduce sales. Hover for exact values; use the legend, zoom and reset controls to explore.",
        ),
        (
            "monthly net demand",
            "Each point is the signed quantity total in EA for an included month. Negative transactions reduce net demand. Zero represents no net demand in an included month, not missing inventory. EA does not standardize pack sizes across products.",
        ),
        (
            "verified analytical result",
            "This chart visualizes the verified assistant result table above. Axis labels identify the measure and unit. Hover for values and compare them with the table; all results respect the dashboard filters.",
        ),
    ]
    for match, description in guides:
        if match in title:
            return description
    return "Hover over a data point for its exact values. Axis labels show the measure and unit. Click legend entries to hide or restore a series; use zoom and autoscale to explore. All values reflect the selected dashboard scope."


def prepare_chart(fig, help_text=None):
    description = help_text or chart_guide(fig)
    title = (fig.layout.title.text or "").lower()
    if "abc–xyz" in title:
        fig.update_traces(
            hovertemplate="ABC class: %{y}<br>XYZ class: %{x}<br>Products: %{z:,.0f}<extra></extra>"
        )
    elif "adjacent-month" in title:
        fig.update_traces(
            hovertemplate="Division: %{y}<br>Month: %{x}<br>Net demand growth: %{z:.2f}%<extra></extra>"
        )
    return description


def show(fig, key=None, help_text=None):
    description = prepare_chart(fig, help_text)
    st.caption("About this chart", help=description)

    fig.update_layout(
        template="plotly_white",
        colorway=COLORS,
        font=dict(family="Arial", color="#20344c"),
        margin=dict(l=12, r=12, t=45, b=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend_title_text="",
        hovermode="x unified"
        if any(t.type == "scatter" for t in fig.data)
        else "closest",
        hoverlabel=dict(bgcolor="#132c43", font_color="white", bordercolor="#009e98"),
        transition=dict(duration=250),
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
        labels=LABELS,
    )


def bar(data, x, y, title, color=None):
    return px.bar(
        data,
        x=x,
        y=y,
        color=color,
        title=title,
        color_discrete_sequence=COLORS,
        labels=LABELS,
    )
