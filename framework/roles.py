import yaml
from logging import info, error, critical
from .framework import render_template_file, FrameworkError
import os

def role_badge(points, type='translator', classes="") -> str:
    #! New idea: only cache the role file, render template on demand with classes and cache the results using a LRU cache
    if hasattr(role_badge, '_roles'):
        if not role_badge._roles.get(type, None):
            error(f"No role badge configured for type \"{type}\"")
            return ""
        for role in role_badge._roles:
            # The list is sorted at this point
            if points > role.point_limit:
                #! Hold up this doesnt work
                badge = role.badge + f" {classes}"
                return badge
        # Under the minimum limit
        return ""
    try:
        current_dir = os.path.dirname(__file__)
        with open(os.path.join(current_dir, 'config', 'roles.yaml'), 'r', encoding='utf-8') as rolefile:
            # Load the config
            role_data = yaml.safe_load(rolefile)
    except Exception as e:
        critical(f"Framework error: failed to load roles ({str(e)})")
        raise FrameworkError(f"Failed to load roles ({str(e)})")
    if not role_data is list:
        critical(f"Framework error: malformed role configuration")
        raise FrameworkError("Malformed role configuration")
    for role_type in role_data:
        for role in role_type.roles:
            role.badge = render_template_file(os.path.join(current_dir, 'templates', 'role_badge.j2'), classes)