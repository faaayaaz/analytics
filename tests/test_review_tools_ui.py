"""Previous-period controls and prepared briefs follow the active dashboard scope."""

import io
import json
from pathlib import Path
from zipfile import ZipFile

import pandas as pd
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def test_comparison_brief_and_scope_invalidation():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
    next(button for button in app.button if button.label == "Q4 only").click().run()
    app.toggle(key="overview_compare").set_value(True).run()
    assert not app.exception
    assert "vs Jul–Sep 2024" in app.metric[0].delta
    app.button(key="prepare_brief").click().run()
    assert not app.exception
    prepared = app.session_state["prepared_brief"]
    with ZipFile(io.BytesIO(prepared[1])) as archive:
        scope = json.loads(archive.read("scope.json"))
        totals = pd.read_csv(io.BytesIO(archive.read("kpis.csv")))
        assert scope["period"] == ["2024-10", "2024-11", "2024-12"]
        assert round(totals["Net Sales (AED)"].iloc[0]) == int(
            app.metric[0].value.replace(",", "")
        )
    assert any(
        item.proto.label == "Download planning brief"
        for item in app.get("download_button")
    )
    app.multiselect(key="filter_division").set_value(["Food"]).run()
    assert not app.exception
    assert not any(
        item.proto.label == "Download planning brief"
        for item in app.get("download_button")
    )
    assert "vs Jul–Sep 2024" in app.metric[0].delta
    next(button for button in app.button if button.label == "Full year").click().run()
    assert not app.exception
    assert not app.metric[0].delta
    assert any("previous period is outside" in note.value for note in app.caption)


def test_missing_source_month_is_not_invented_as_zero_demand():
    # Simulate an incomplete replacement workbook after ingestion, retaining real rows.
    script = (
        (ROOT / "app.py")
        .read_text()
        .replace(
            "data, report = cached_load(payload)",
            "data, report = cached_load(payload)\n"
            "    data = data.loc[data.month.ne(pd.Timestamp('2024-04-01'))].copy()\n"
            "    report = {**report, 'missing_calendar_months': '2024-04'}",
        )
    )
    app = AppTest.from_string(script, default_timeout=120).run()
    assert not app.exception
    assert any("2024-04" in note.value for note in app.warning)
    assert len(app.metric) == 0
    next(
        button for button in app.button if button.label == "Use available months"
    ).click().run()
    assert not app.exception
    assert len(app.multiselect(key="filter_months").value) == 11
    assert pd.Timestamp("2024-04-01") not in app.multiselect(key="filter_months").value
    assert len(app.metric) == 8
    app.sidebar.radio[0].set_value("Demand forecasting").run()
    assert not app.exception
    assert any("six consecutive months" in note.value for note in app.info)
    next(
        button for button in app.button if button.label == "Last 6 months"
    ).click().run()
    assert not app.exception
    assert len(app.metric) == 7
