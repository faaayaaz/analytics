import pandas as pd
import plotly.express as px
from modules.visualizations import prepare_chart, chart_guide, line


def test_chart_help_has_meaning_and_units():
    fig = px.bar(x=["Food"], y=[10], title="Division sales and gross margin")
    description = prepare_chart(fig)
    assert "left axis" in description and "right axis" in description
    assert description == chart_guide(fig)


def test_matrix_tooltip_and_plain_language_axes():
    matrix = px.imshow(
        [[2]], x=["X"], y=["A"], title="ABC–XYZ planning matrix • product counts"
    )
    prepare_chart(matrix)
    assert "Products: %{z:,.0f}" in matrix.data[0].hovertemplate
    fig = line(
        pd.DataFrame({"month": ["Jan"], "quantity": [10]}),
        "month",
        "quantity",
        "Monthly net demand • EA",
    )
    assert fig.layout.yaxis.title.text == "Units sold minus returns (EA)"
    assert "units sold minus returns" in chart_guide(fig)
