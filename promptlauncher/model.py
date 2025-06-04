import os
import json

class PromptModel:
    """Model for loading and saving prompt data."""
    def __init__(self, path: str):
        self.path = path
        self.prompt_dict: dict[str, dict[str, str]] = {}
        self.usage_counts: dict[str, dict[str, int]] = {}
        self.load()

    def load(self):
        if not os.path.exists(self.path):
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump({"default": {}}, f, ensure_ascii=False, indent=2)

        with open(self.path, 'r', encoding='utf-8') as f:
            data = json.load(f) or {}

        self.prompt_dict = {}
        self.usage_counts = {}
        for grp, amap in data.items():
            self.prompt_dict[grp] = {}
            self.usage_counts[grp] = {}
            for alias, val in amap.items():
                self.prompt_dict[grp][alias] = val.get('text', '')
                self.usage_counts[grp][alias] = val.get('count', 0)

    def save(self):
        out: dict[str, dict[str, dict[str, int | str]]] = {}
        for grp, amap in self.prompt_dict.items():
            out[grp] = {}
            for alias, text in amap.items():
                cnt = self.usage_counts.get(grp, {}).get(alias, 0)
                out[grp][alias] = {'text': text, 'count': cnt}
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

    # ---------- prompt/group operations ----------
    def add_group(self, name: str):
        if name not in self.prompt_dict:
            self.prompt_dict[name] = {}
            self.usage_counts[name] = {}
            self.save()

    def delete_group(self, name: str):
        if name in self.prompt_dict:
            self.prompt_dict.pop(name, None)
            self.usage_counts.pop(name, None)
            self.save()

    def rename_group(self, old: str, new: str):
        if old in self.prompt_dict and new not in self.prompt_dict:
            self.prompt_dict[new] = self.prompt_dict.pop(old)
            self.usage_counts[new] = self.usage_counts.pop(old)
            self.save()

    def add_prompt(self, group: str, alias: str, text: str):
        self.prompt_dict.setdefault(group, {})[alias] = text
        self.usage_counts.setdefault(group, {}).setdefault(alias, 0)
        self.save()

    def update_prompt(self, group: str, old_alias: str, new_alias: str, text: str):
        if new_alias != old_alias:
            self.prompt_dict[group].pop(old_alias, None)
            self.usage_counts[group].pop(old_alias, None)
        self.prompt_dict.setdefault(group, {})[new_alias] = text
        self.usage_counts.setdefault(group, {}).setdefault(new_alias, 0)
        self.save()

    def delete_prompt(self, group: str, alias: str):
        self.prompt_dict.get(group, {}).pop(alias, None)
        self.usage_counts.get(group, {}).pop(alias, None)
        self.save()

    def increment_usage(self, group: str, alias: str):
        self.usage_counts.setdefault(group, {}).setdefault(alias, 0)
        self.usage_counts[group][alias] += 1
        self.save()
