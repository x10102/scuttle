from logging import warning, info, error, debug
from dataclasses import dataclass
from flask import Blueprint, redirect, render_template, url_for, current_app,jsonify, request
from flask_login import current_user, login_required
from connectors.portainer import PortainerError
from extensions import portainer
from connectors.wikicomma import Status, Message
from typing import List
from db import WikiCommaConfig, Wiki, Backup
import os
from jsonschema import validate
from threading import Lock
from datetime import datetime
import urllib.parse
import json
import subprocess

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
            'minimum': 0        
        },
        'ratelimit_size': {
            'type': ['integer', 'null'],
            'minimum': 0        
        },
        'ratelimit_refill': {
            'type': ['integer', 'null'],
            'minimum': 0        
        },
    }
}

status_message_schema = {
    'type': 'object',
    'properties': {
        'type': {
            'type': 'integer',
            'minimum': 0,
            'maximum': 7
        },
        'tag': {
            'type': 'string'
        }
    },
    'required': ['type', 'tag'],
    'oneOf': [ 
        { 'properties': {
            'type': { 'enum': [0, 5, 6, 7] }
        }, 'additionalProperties': False },
        { 'properties': {
            'type': {'const': 1},
            'total': {'type': 'integer', 'minimum': 0}
        }, 'required': ['total']},
        { 'properties': {
            'type': {'enum': [3, 4]},
            'errorKind': {'type': 'integer', 'minimum': 0, 'maximum': 14}
        }, 'required': ['errorKind'],
            'oneOf': [
                {   'properties': {
                    'errorKind': {'enum': [0, 1, 5, 6, 7, 9, 10, 11, 12, 14]}
                }},
                {   'properties': {
                    'errorKind': {'enum': [2, 3, 4, 8, 13]},
                    'name': {'type': 'string'}
                }, 'required': ['name']}
        ]},
        { 'properties': {
            'type': {'const': 2},
            'status': {'type': 'integer', 'minimum': 0, 'maximum': 8}
        }, 'required': ['status'],
            'oneOf': [
                { 'properties': {
                    'status': {'enum': [0, 2, 3, 4, 5]}
                }},
                { 'properties': {
                    'status': {'const': 2},
                    'done': {'type': 'integer', 'minimum': 0},
                    'postponed': {'type': 'integer', 'minimum': 0}
                }, 'required': ['done', 'postponed']}
            ]}
    ]
}

# TODO: require auth

AutobackupController = Blueprint("AutobackupController", __name__)

@AutobackupController.route('/backups', methods=["GET"])
def backup_index():
    return render_template('backups/backup_index.j2', wikis=Wiki.select(), backups=Backup.select())

@AutobackupController.route('/backup/status', methods=["GET", "POST"])
def backup_status():
    if request.method == "GET":
        return jsonify([s.status for s in statuses.values()])
    try:
        message = json.loads(request.data)
        validate(message, status_message_schema)
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
        
        # TODO: Should validate the URLs and normalize them (scheme, trailing slash, remove path)
        # Add the new wiki list
        # We don't want to drop the previous wikis from the database as the backup model references them
        if data['wikis'] is not None:
            wiki_urls = data['wikis'].strip().split('\n')
            # We upsert the new URLs and mark them as active
            for wiki in wiki_urls:
                # Skip possible blank lines
                if not wiki: continue
                row, is_new = Wiki.get_or_create(url=wiki, name=str(urllib.parse.urlparse(wiki).netloc).split('.')[0])
                if not is_new:
                    row.is_active = True
                    row.save()
            # Then loop over them again and mark the ones not in the new list as inactive
            for wiki in Wiki.select():
                if wiki.url not in wiki_urls:
                    wiki.is_active = False
                    wiki.save()
        else:
            Wiki.update(is_active=False).execute()
        generate_config(path)
        # Log it just in case
        info(f"Accepted new WikiComma config by {current_user.nickname} (ID: {current_user.get_id()})")
        return "Konfigurace uložena", 200
    except Exception as e:
        error(f"Config couldn't be updated: {str(e)}")
        return f"Konfiguraci nelze uložit ({str(e)})", 400

@AutobackupController.route('/backup/start', methods=["GET"])
def run_backup():
    start_method = current_app.config.get('BACKUP', {}).get('WIKICOMMA_START_METHOD')
    if start_method not in ['container', 'command']:
        error("WikiComma start method not set or invalid")
        return "WikiComma start method not set or invalid", 500
    
    info("Preparing to start backup")

    # Check that we can login to Portainer if we're running WikiComma in a container
    if start_method == 'container':
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
    for wiki in Wiki.select().where(Wiki.is_active == True):
        statuses[wiki.name] = StatusMutex(Lock(), BackupStatus(wiki.name, messages=[], status=Status.Other))
        debug(f"SynchronizedStatus created for {wiki.name}")

    info(f"{Wiki.select().where(Wiki.is_active == True).count()} sites are marked for backup")

    # Save to the database
    backup = Backup()
    backup.author = current_user
    backup.date = datetime.now()
    backup.is_finished = False
    backup.save()

    # TODO: Add BackupHasWiki entries

    info('Attempting to start WikiComma')
    if start_method == 'container':
        try:
            info(f"Starting container \"{portainer.get_name()}\"")
            portainer.start_container()
        except PortainerError as e:
            error(f"Couldn't start container, stopping backup ({str(e)})")
            backup.delete_instance()
            return "Chyba: Kontejner nelze spustit", 500
    else:
        try:
            info(f"Running command: {start_command}")
            # subprocess.run(start_command, shell=True).check_returncode()
            os.system(start_command)
        except subprocess.CalledProcessError:
            error("Command failed, stopping backup")
            backup.delete_instance()
            return "Chyba: Spouštěcí příkaz skončil s chybou", 500

    info('WikiComma started')
    return "Záloha byla spuštěna"