from logging import warning, info, error, debug
from dataclasses import dataclass
from flask import Blueprint, redirect, render_template, url_for, current_app,jsonify, request
from flask_login import current_user, login_required
from connectors.portainer import PortainerError
from extensions import portainer
from connectors.wikicomma import Status, Message
from typing import List
from db import WikiCommaConfig, Wiki, Backup
from jsonschema import validate
from threading import Lock
from os import system
import urllib.parse
import json

@dataclass
class BackupStatus:
    wiki_tag: str
    messages: List[Message]
    total_articles: int = 0
    finished_articles: int = 0
    postponed_articles: int = 0
    total_errors: int = 0
    status: Status = Status.Other

@dataclass
class StatusMutex:
    mutex: Lock
    status: BackupStatus

statuses = {}

backup_config_schema = {
    'type': 'object',
    'properties': {
        'socks_proxy': {
            'type': ['string', 'null']
        },
        'http_proxy': {
            'type': ['string', 'null']
        },
        'blacklist': {
            'type': ['string', 'null']
        },
        'wikis': {
            'type': ['string', 'null']
        },
        'delay': {
            'type': ['integer', 'null'],
            'inclusiveMinimum': 0        
        },
        'ratelimit_size': {
            'type': ['integer', 'null'],
            'inclusiveMinimum': 0        
        },
        'ratelimit_refill': {
            'type': ['integer', 'null'],
            'inclusiveMinimum': 0        
        },
    }
}

# TODO: require auth

AutobackupController = Blueprint("AutobackupController", __name__)

@AutobackupController.route('/backups', methods=["GET"])
def backup_index():
    return render_template('backups/backup_index.j2', wikis=Wiki.select())

@AutobackupController.route('/backup/status', methods=["GET", "POST"])
def backup_status():
    if request.method == "GET":
        return "OK"
    print(f"Received: {request.data}")
    return "OK"

@AutobackupController.route('/backup/config', methods=["GET", "POST"])
@login_required
def backup_config():
    if request.method == "GET":
        # TODO: Return current config to be displayed on the cfg page
        current_config = WikiCommaConfig.get_or_create()
        return "OK", 200
    try:
        # Parse the payload and make sure it's valid
        data = json.loads(request.data)
        validate(data, schema=backup_config_schema)
        # There's always just a single row in the WikiCommaConfig table
        current_config = WikiCommaConfig.get_or_create()[0]
        current_config.blacklist = data['blacklist']
        current_config.http_proxy = data['http_proxy']
        current_config.socks_proxy = data['socks_proxy']
        current_config.delay = data['delay']
        current_config.ratelimit_refill = data['ratelimit_refill']
        current_config.ratelimit_size = data['ratelimit_size']
        current_config.save()
        # Drop everything from the Wiki table
        Wiki.delete().execute()
        # Add the new wiki list
        if data['wikis'] is not None:
            for wiki in data['wikis'].strip().split('\n'):
                Wiki.get_or_create(url=wiki, name=str(urllib.parse.urlparse(wiki).netloc).split('.')[0])
        # Log it just in case
        info(f"Accepted new WikiComma config by {current_user.nickname} (ID: {current_user.get_id()})")
        return "OK", 200
    except Exception as e:
        error(f"Invalid config JSON: {str(e)}")
        return "Invalid JSON", 400

@AutobackupController.route('/backup/start', methods=["GET"])
def run_backup():
    if current_app.config.get('BACKUP', {}).get('WIKICOMMA_START_METHOD') not in ['container', 'command']:
        error("WikiComma start method not set or invalid")
        return "WikiComma start method not set or invalid", 500
    info("Preparing to start backup")

    # Check that we can login to Portainer if we're running WikiComma in a container
    if current_app.config['BACKUP']['WIKICOMMA_START_METHOD'] == 'container':
        if not portainer.is_initialized():
            error("Portainer connector is not initialized, can't proceed")
            return "Konfigurace Portaineru chybí. Nelze pokračovat.", 500
        try:
            portainer.login()
        except PortainerError as e:
            error(f"Cannot login to portainer ({str(e)})")
            return "Přihlášení k portaineru selhalo. Nelze pokračovat", 500
        info('Successfully logged in to portainer')
    else:
        # Otherwise make sure we have a valid start command
        start_command = current_app.config.get('BACKUP', {}).get('START_CMD')
        if not start_command:
            error("Invalid start command")
            return "Invalid start command", 500

    # Iterate over the wiki list, create status objects and mutexes
    for wiki in Wiki.select():
        statuses[wiki.name] = StatusMutex(Lock(), BackupStatus(wiki.name, messages=[], status=Status.Other))

    info('Starting Wikicomma container')
    if current_app.config['BACKUP']['WIKICOMMA_START_METHOD'] == 'container':
        try:
            portainer.start_container()
        except PortainerError as e:
            error(f"Couldn't start container, can't proceed ({str(e)})")
            return "Chyba: Kontejner nelze spustit", 500
    else:
        system(start_command)

    info('Container started')
    return "Záloha byla spuštěna"