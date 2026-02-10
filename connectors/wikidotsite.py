# Builtins
from typing import Optional
from os import PathLike, path, getcwd
from logging import info, error

# Internal


# External
from flask import current_app
from urllib import parse
import wikidot

def get_site_slug(url: str) -> str:
    parsed_url = parse.urlparse(url)
    path = parsed_url.path
    return path.removeprefix('/')

def snapshot_original(url: str, source_wiki_name: str = "scp-wiki", revision_id: int = 0) -> Optional[PathLike]:
    wd_client = wikidot.Client()
    page_name = get_site_slug(url)
    info(f"Saving snapshot of \"{page_name}\", revision ID is {revision_id}")
    original_page = wd_client.site.get(source_wiki_name).page.get(page_name, raise_when_not_found=False)
    if not original_page:
        error(f"Original page \"{page_name}\" not found on source wiki")
        return None
    page_source = original_page.source
    filename = page_name + '-' + str(revision_id) + '.txt'
    file_path = path.join(getcwd(), 'temp', 'snapshots', filename)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(page_source.wiki_text)
    info(f"Snapshot of \"{page_name}\" saved as {file_path}")
