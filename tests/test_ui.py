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
            app.button[-1].click().run()
            assert not app.exception
            assert len(app.chat_message) == 2
    app.sidebar.radio[0].set_value("Executive overview").run()
    app.sidebar.multiselect[1].set_value(["Food"]).run()
    assert not app.exception
    assert "193,130,713" in app.metric[0].value
    app.sidebar.multiselect[0].set_value([]).run()
    assert not app.exception
    assert any("No transactions" in x.value for x in app.info)
