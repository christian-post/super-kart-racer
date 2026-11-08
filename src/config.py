import shutil
from pathlib import Path
import tomlkit
from tomlkit.items import Table


class Config:
    """
    Combined access to two TOML files:
    - settings.toml: user-changeable values (created from settings.example.toml, saved on exit)
    - config.toml: fixed constants (read-only, tracked in git)
    Lookups check settings first, then config. Only settings can be changed/saved.
    """
    def __init__(self, settings_file : Path, settings_example_file : Path, constants_file : Path):
        self.settings_file = settings_file
        self.settings_example_file = settings_example_file
        self.constants_file = constants_file
        self.load()

    def load(self):
        # create user settings from example on first run
        if not self.settings_file.exists():
            shutil.copy(self.settings_example_file, self.settings_file)

        with open(self.settings_file, "r", encoding="utf-8") as f:
            self._settings = tomlkit.load(f)
        with open(self.settings_example_file, "r", encoding="utf-8") as f:
            example = tomlkit.load(f)
        with open(self.constants_file, "r", encoding="utf-8") as f:
            self._constants = tomlkit.load(f)

        # keep user settings in sync with the example (no more deleting settings.toml)
        if self._sync(self._settings, example):
            self.save()

    def _sync(self, user, example):
        # add keys missing from user settings, drop keys no longer in the example
        changed = False
        for key, value in example.items():
            if key not in user:
                user[key] = value
                changed = True
            elif isinstance(value, Table) and isinstance(user[key], Table):
                changed |= self._sync(user[key], value)
        for key in [k for k in user if k not in example]:
            del user[key]
            changed = True
        return changed

    def save(self):
        with open(self.settings_file, "w", encoding="utf-8") as f:
            tomlkit.dump(self._settings, f)

    @staticmethod
    def _find(data, key_path):
        # returns (parent node, key) or None if the path does not exist
        *parents, key = key_path.split(".")
        node = data
        for part in parents:
            if part not in node:
                return None
            node = node[part]
        if key not in node:
            return None
        return node, key

    def __getitem__(self, key_path):
        found = self._find(self._settings, key_path) or self._find(self._constants, key_path)
        if found is None:
            raise KeyError(f"Unknown config key '{key_path}'")
        node, key = found
        return node[key]

    def __setitem__(self, key_path, value):
        found = self._find(self._settings, key_path)
        if found is None:
            raise KeyError(f"'{key_path}' is not a user setting (constants are read-only)")
        node, key = found
        old = node[key]
        old_type = type(old.unwrap() if hasattr(old, "unwrap") else old)
        if old_type is not type(value):
            raise TypeError(f"'{key_path}' expects {old_type.__name__}, "
                            f"got {type(value).__name__}")
        node[key] = value