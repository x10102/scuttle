from db import Backup
from datetime import datetime, timedelta
from logging import info
from flask import current_app, Flask
from blueprints.autobackup import backup

# TODO: Having to pass the app object like this is ugly, rethink the design
def run_backup_task(backup_interval: int, app: Flask):
    latest_backup = Backup.select().order_by(Backup.date.desc()).first()
    if not latest_backup:
        info("Skipping auto backup check (no previous backups found)")
        return
    if not latest_backup.is_finished:
        info("Skipping auto backup check (backup already in progress)")
    next_scheduled_backup = latest_backup.date + timedelta(seconds=backup_interval)
    if next_scheduled_backup < datetime.now():
        info("Running scheduled backup")
        with app.app_context():
            backup()