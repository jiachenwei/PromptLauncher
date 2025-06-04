import sys
from pathlib import Path
import importlib.util

# Avoid importing the package which depends on PyQt6
file_path = Path(__file__).parents[1] / "promptlauncher" / "model.py"
spec = importlib.util.spec_from_file_location("promptlauncher.model", file_path)
model_mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = model_mod
spec.loader.exec_module(model_mod)
PromptModel = model_mod.PromptModel


def test_promptmodel_add_and_increment(tmp_path):
    path = tmp_path / 'data.json'
    m = PromptModel(str(path))
    m.add_group('g1')
    m.add_prompt('g1', 'a1', 'hello')
    m.increment_usage('g1', 'a1')
    assert m.prompt_dict['g1']['a1'] == 'hello'
    assert m.usage_counts['g1']['a1'] == 1
