from logging import critical, info
from .framework import render_template_file
import yaml
import time
import os

# Returns an HTML string containing the app's sidebar menu
# The menu is rendered on first call and cached indefinitely
def navigation_menu(authorized: bool = False):
    # Check if we already built the menu
    if hasattr(navigation_menu, '_cache'):
        return navigation_menu._cache[authorized]
    
    render_time = time.perf_counter()

    try:
        current_dir = os.path.dirname(__file__)
        with open(os.path.join(current_dir, 'config', 'menu.yaml'), 'r', encoding='utf-8') as menufile:
            # Load the config
            menu_config = yaml.safe_load(menufile)
    except Exception as e:
        critical(f"Framework error: failed to render menu ({str(e)})")
        raise e

    # Create the cache attribute on this function
    navigation_menu._cache = ["", ""]

    for item in menu_config['menu']:
        menuitem = list(item.values())[0]
        # Render the template for the current list item
        rendered = render_template_file(os.path.join(current_dir, 'templates', 'menu_item.j2'),
                                        handler=menuitem['handler'],
                                        text=menuitem['text'],
                                        icon=menuitem['icon'],
                                        linkparams=menuitem.get('link_params'))
        if menuitem['auth'] != "authorized":
            navigation_menu._cache[0] += rendered
        if menuitem['auth'] != "unauthorized_only":
            navigation_menu._cache[1] += rendered

    info(f"Pre-rendered navigation menu template in {time.perf_counter()-render_time:.4}s")

    return navigation_menu._cache[authorized]