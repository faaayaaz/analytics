from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def test_all_pages_and_filters():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
    assert not app.exception
    assert len(app.metric) == 8
    assert "441,894,325" in app.metric[0].value
    for page in [
        "SKU & demand intelligence",
        "Forecasting & scenario lab",
        "SupplyIQ assistant",
        "Data quality & exports",
    ]:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception, [(e.message) for e in app.exception]
        if page == "SKU & demand intelligence":
            assert len(app.dataframe) >= 3
            app.text_input[0].set_value("P001").run()
            assert not app.exception
        if page == "Forecasting & scenario lab":
            app.slider[0].set_value(20).run()
            assert not app.exception
            app.selectbox[0].set_value("Simple exponential smoothing").run()
            assert not app.exception
        if page == "SupplyIQ assistant":
            next(
                button
                for button in app.button
                if button.label == "Analyze selected question"
            ).click().run()
            assert not app.exception
            assert len(app.chat_message) == 2
    app.sidebar.radio[0].set_value("Executive overview").run()
    app.sidebar.multiselect[1].set_value(["Food"]).run()
    assert not app.exception
    assert "193,130,713" in app.metric[0].value
    app.sidebar.multiselect[0].set_value([]).run()
    assert not app.exception
    assert any("No transactions" in x.value for x in app.info)


def test_usability_shortcuts_and_filter_recovery():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()

    def click(label):
        next(button for button in app.button if button.label == label).click().run()
        assert not app.exception

    click("Q4 only")
    assert len(app.multiselect(key="filter_months").value) == 3
    app.multiselect(key="filter_division").set_value(["Food"]).run()
    category = app.multiselect(key="filter_category").options[0]
    app.multiselect(key="filter_category").set_value([category]).run()
    app.multiselect(key="filter_division").set_value(["Durable Goods"]).run()
    assert not app.exception
    assert app.multiselect(key="filter_category").value == []
    click("Reset all filters")
    assert len(app.multiselect(key="filter_months").value) == 12
    assert app.multiselect(key="filter_division").value == []
    assert "441,894,325" in app.metric[0].value
    click("Try a demand scenario")
    assert app.radio(key="workspace").value == "Forecasting & scenario lab"
    click("Growth +20%")
    assert app.slider(key="scenario_pct").value == 20
    assert float(app.metric[2].value.replace(",", "")) > 0
    click("Baseline 0%")
    assert app.slider(key="scenario_pct").value == 0
    assert app.metric[2].value == "+0"
    app.sidebar.radio[0].set_value("Executive overview").run()
    app.multiselect(key="filter_months").set_value([]).run()
    click("Restore full-year view")
    assert "441,894,325" in app.metric[0].value


def test_visual_metric_exploration():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
    assert not app.exception
    assert [tab.label for tab in app.tabs] == [
        "Performance studio",
        "Business mix",
        "Growth & insights",
    ]
    app.button(key="focus_1").click().run()
    assert not app.exception
    assert app.session_state["focus_metric"] == "Net Units Sold"
    assert any(heading.value == "Net Units Sold" for heading in app.subheader)
    assert app.button(key="focus_1").label == "Viewing trend"
    app.button(key="focus_0").click().run()
    assert not app.exception
    assert "441,894,325" in app.metric[0].value


def test_supplyiq_launcher_and_question_buttons():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
    app.multiselect(key="filter_division").set_value(["Food"]).run()
    app.button(key="summary_supplyiq").click().run()
    assert not app.exception
    assert app.radio(key="workspace").value == "SupplyIQ assistant"
    assert len(app.chat_message) == 2
    assert "193,130,712.74" in app.chat_message[1].markdown[0].value
    assert "assistant_pending_question" not in app.session_state
    next(b for b in app.button if b.label == "Top 10 SKUs").click().run()
    assert not app.exception
    assert len(app.chat_message) == 4
    assert app.session_state["chat_context"]["intent"] == "top"
    next(b for b in app.button if b.label == "Monthly demand").click().run()
    assert not app.exception
    assert len(app.chat_message) == 6
    app.run()
    assert len(app.chat_message) == 6  # A queued question is consumed exactly once.
    app.sidebar.radio[0].set_value("Executive overview").run()
    app.button(key="open_supplyiq").click().run()
    assert not app.exception
    assert app.radio(key="workspace").value == "SupplyIQ assistant"
    assert len(app.chat_message) == 6
