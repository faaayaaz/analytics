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
            "Bars show sales after returns in AED, using the left axis. The line shows gross margin on the right axis: the percentage of sales left after product costs. The two axes use different units.",
        ),
        (
            "pareto",
            "Products run from highest to lowest sales. Bars show sales in AED on the left axis. The line on the right shows how much of total positive sales these products add up to. Products with zero or negative sales are left out. A product crossing an ABC cutoff stays in its starting group.",
        ),
        (
            "abc distribution",
            "Each bar counts products in a sales value group. A contains the leading sales contributors, B the next group, and C the rest. Your settings control the cutoffs. N means sales are zero or negative, so the product is not ranked.",
        ),
        (
            "abc–xyz",
            "Rows group products by sales value: A = leading contributors, B = the next group, C = the rest. Columns show how steady demand is: X = steady, Y = some changes, Z = large changes. Each box counts products; darker means more products, not higher stock risk. N products are left out. Choose a group below to see advice.",
        ),
        (
            "adjacent-month",
            "Rows are divisions and columns are months. Each box shows the percentage change in units sold minus returns from the previous month. Green means an increase; red means a decrease. A blank means the previous month was not selected or had zero or negative units. A colour alone does not tell you whether performance is good or bad.",
        ),
        (
            "historical net demand",
            "The solid line shows actual 2024 units sold minus returns. Dashed lines estimate January–March 2025 demand: the original forecast and the forecast after your chosen change. EA means individual units. Hover for values; click a line name to hide or show it. These estimates do not tell you how much to order.",
        ),
        (
            "top 10",
            "Products are ordered by sales after returns, using your selected filters. Taller bars mean more sales in AED, not more units or stock. Hover over a bar to see its product and sales value.",
        ),
        (
            "category net sales",
            "Bars compare sales after returns by category in AED. Longer bars mean more sales for your selection. Returns and credit notes are deducted.",
        ),
        (
            "channel net revenue",
            "Bars show sales after returns in AED for each sales channel. Use them to see which channels bring in more sales. They do not show stock levels or future demand.",
        ),
        (
            "monthly net sales",
            "Each point shows sales after returns in AED for a selected month. Returns and credit notes reduce the total. Hover for exact values, or use the zoom and reset buttons to explore.",
        ),
        (
            "monthly net demand",
            "Each point shows units sold minus returns for a selected month. EA means individual units; pack sizes may differ between products. Zero means sales and returns add up to zero, not that stock is unavailable.",
        ),
        (
            "verified analytical result",
            "This chart shows the calculated results in the assistant table above. Read the axis labels to see what is being measured. Hover for exact values. The chart uses the same filters as the rest of the dashboard.",
        ),
    ]
    for match, description in guides:
        if match in title:
            return description
    return "Hover over a point for its exact value. Axis labels tell you what is measured. Click a name in the chart key to hide or show that line. Use zoom to look closer and Autoscale to fit the chart again. Values follow your dashboard filters."


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
