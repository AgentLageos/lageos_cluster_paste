import os
import yaml


def validate_config(config_file):
    if not os.path.isfile(config_file):
        raise ValueError(f"Config file not found: {config_file}")

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML: {e}")

    if not isinstance(config, dict):
        raise ValueError("Config must be a YAML mapping.")

    required_keys = {
        "chunk_size",
        "paste_delay",
    }

    optional_keys = {
        "retry_hint",
    }

    missing = required_keys - set(config.keys())
    unknown = set(config.keys()) - required_keys - optional_keys

    if missing:
        raise ValueError(
            f"Config is missing: "
            f"{', '.join(sorted(missing))}"
        )

    if unknown:
        raise ValueError(
            f"Unknown config keys: "
            f"{', '.join(sorted(unknown))}"
        )

    if not isinstance(config["chunk_size"], int):
        raise ValueError("chunk_size must be an integer.")

    if not isinstance(config["paste_delay"], (int, float)):
        raise ValueError("paste_delay (in seconds) must be a number.")

    if "retry_hint" in config and not isinstance(config["retry_hint"], bool):
        raise ValueError("retry_hint must be true or false.")

    return True



