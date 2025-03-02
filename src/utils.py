import configparser
from pathlib import Path

import yaml


def read_yaml(yaml_path: str | Path) -> dict:
    """ Load .read_yaml file as dict """
    with open(yaml_path, encoding='utf-8', errors='ignore') as f:
        return yaml.safe_load(f)


def write_yaml(data: dict, yaml_path: str | Path):
    """ Load .read_yaml file as dict """
    with open(yaml_path, 'w', encoding='utf-8') as f:
        return yaml.safe_dump(data, f, default_flow_style=False)


def load_ini_config(ini_path: str | Path, section: str | None = None) -> dict:
    """ Load .ini file as dict """
    config_object = configparser.ConfigParser()
    with open(ini_path, encoding='utf-8', errors='ignore') as f:
        config_object.read_file(f)
        output_dict = dict()
        if section:
            sections = [section]
        else:
            sections = config_object.sections()
        for s in sections:
            items = config_object.items(s)
            output_dict[s] = dict(items)
    if section:
        output_dict = output_dict[section]
    return output_dict
