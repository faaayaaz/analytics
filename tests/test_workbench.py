"""Planner controls combine without changing the dashboard comparison population."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def test_workbench_segment_filters_sort_empty_reset_and_history():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
    app.sidebar.radio[0].set_value("SKU analysis").run()
    assert not app.exception
    assert len(app.dataframe[2].value) == 250

    app.selectbox(key="matrix_segment").set_value("AZ").run()
    app.button(key="apply_workbench_segment").click().run()
    assert not app.exception
    assert app.multiselect(key="workbench_abc").value == ["A"]
    assert app.multiselect(key="workbench_xyz").value == ["Z"]
    visible = app.dataframe[2].value
    assert len(visible) == 14
    assert set(visible["segment"]) == {"AZ"}
    # Matrix/explorer filters narrow the view, rather than reclassifying 14 products as a new universe.
    assert visible["contribution_pct"].sum() < 100

    app.selectbox(key="workbench_sort").set_value("Demand CV ↓").run()
    visible = app.dataframe[2].value
    assert visible["demand_cv"].is_monotonic_decreasing
    sku = visible.iloc[0]["product"]
    app.text_input(key="sku_search").set_value(sku).run()
    assert not app.exception
    assert app.dataframe[2].value["product"].tolist() == [sku]
    assert app.selectbox(key="detail_product").value == sku

    # Literal search must not treat a user's '[' as a regex or retain an unrelated history panel.
    app.text_input(key="sku_search").set_value("[").run()
    assert not app.exception
    assert app.dataframe[2].value.empty
    assert not any(box.key == "detail_product" for box in app.selectbox)
    assert any("No SKUs match" in note.value for note in app.info)

    app.button(key="workbench_reset").click().run()
    assert not app.exception
    assert len(app.dataframe[2].value) == 250
    assert app.text_input(key="sku_search").value == ""
    assert app.multiselect(key="workbench_abc").value == []
    assert app.multiselect(key="workbench_xyz").value == []

    app.multiselect(key="filter_division").set_value(["Food"]).run()
    app.text_input(key="sku_search").set_value("not a product").run()
    app.button(key="workbench_reset").click().run()
    assert not app.exception
    assert app.multiselect(key="filter_division").value == ["Food"]
    assert set(app.dataframe[2].value["division"]) == {"Food"}
    assert 0 < len(app.dataframe[2].value) < 250
