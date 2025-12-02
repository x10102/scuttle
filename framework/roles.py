import yaml
from logging import info, error, critical
from functools import lru_cache
from .framework import render_template_file, FrameworkError
import os

MODULE_DIR = os.path.dirname(__file__)
role_cache = None

def load_role_file():
    global role_cache
    try:
        with open(os.path.join(MODULE_DIR, 'config', 'roles.yaml'), 'r', encoding='utf-8') as rolefile:
            # Load the config
            role_data = yaml.safe_load(rolefile)
    except Exception as e:
        critical(f"Framework error: failed to load roles ({str(e)})")
        raise FrameworkError(f"Failed to load roles ({str(e)})")
    if not isinstance(role_data, dict):
        print(role_data)
        critical(f"Framework error: malformed role configuration")
        raise FrameworkError("Malformed role configuration")
    for role_type, data in role_data.items():
        role_data[role_type].get("roles").sort(key=lambda r: r['point_limit'], reverse=True)
    role_cache = role_data

# This one doesn't strictly need to be cached as the config is only loaded once but whatever
@lru_cache(maxsize=4096)
def get_role(points, type='translator'):
    global role_cache # Evil ass global variable 
    if role_cache is None:
        load_role_file()
    if not role_cache.get(type, None):
        error(f"No role badge configured for type \"{type}\"")
        return ""
    role_type = role_cache[type]
    if points < role_type['min_points']: return role_type['no_role']
    for role in role_type['roles']:
        if role['point_limit'] <= points:
            return role

# Caching to not use unnecessary I/O
@lru_cache(maxsize=4096)
def role_badge(points, type='translator', classes="", override_classes = False) -> str:
    role = get_role(points, type)
    return render_template_file(os.path.join(MODULE_DIR, 'templates', 'role_badge.j2'),\
                                name=role['name'],\
                                classes=role['badge_css']+f" {classes}",\
                                override_classes=override_classes)