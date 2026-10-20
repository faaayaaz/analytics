"""Check startup when an older filter-helper module is already in memory."""

from pathlib import Path
import sys
import types
from streamlit.testing.v1 import AppTest
from modules import usability


def test_assistant_works_with_legacy_cached_filter_helpers(monkeypatch):
    legacy = types.ModuleType("modules.usability")
    for name in ["reset_filters", "set_period", "navigate", "set_scenario"]:
        setattr(legacy, name, getattr(usability, name))
    assert not hasattr(legacy, "open_assistant")
    assert not hasattr(legacy, "queue_question")
    monkeypatch.setitem(sys.modules, "modules.usability", legacy)
    app = AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=120
    ).run()
    assert not app.exception
    app.button(key="summary_supplyiq").click().run()
    assert not app.exception
    assert app.radio(key="workspace").value == "SupplyIQ assistant"
    assert len(app.chat_message) == 2
