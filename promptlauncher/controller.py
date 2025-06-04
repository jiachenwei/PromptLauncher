from .model import PromptModel

class PromptController:
    """High level operations for PromptWindow."""
    def __init__(self, model: PromptModel):
        self.model = model

    def save(self):
        self.model.save()

    # group operations
    def add_group(self, name: str):
        self.model.add_group(name)

    def delete_group(self, name: str):
        self.model.delete_group(name)

    def rename_group(self, old: str, new: str):
        self.model.rename_group(old, new)

    # prompt operations
    def add_prompt(self, group: str, alias: str, text: str):
        self.model.add_prompt(group, alias, text)

    def update_prompt(self, group: str, old_alias: str, new_alias: str, text: str):
        self.model.update_prompt(group, old_alias, new_alias, text)

    def delete_prompt(self, group: str, alias: str):
        self.model.delete_prompt(group, alias)

    def increment_usage(self, group: str, alias: str):
        self.model.increment_usage(group, alias)

    def get_prompt_text(self, group: str, alias: str) -> str:
        return self.model.prompt_dict.get(group, {}).get(alias, "")
