from pathlib import Path

import yaml


def read_yaml(yaml_path: str | Path) -> dict:
    """ Load yaml file as dict """
    with open(yaml_path, encoding='utf-8', errors='ignore') as f:
        return yaml.safe_load(f)


def write_yaml(data: dict, yaml_path: str | Path):
    """ Save dict to yaml file """
    with open(yaml_path, 'w', encoding='utf-8') as f:
        return yaml.safe_dump(data, f, default_flow_style=False)
