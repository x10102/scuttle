from db import Backup
from datetime import datetime, timedelta
from logging import info, error
from flask import current_app
from blueprints.autobackup import run_backup

def run_backup_task(backup_interval: int):
    latest_backup = Backup.select().order_by(Backup.date.desc()).first()
    if not latest_backup:
        info("Skipping auto backup check as no previous backups have been found")
        return
    next_scheduled_backup = latest_backup.date + timedelta(seconds=backup_interval)
    if next_scheduled_backup < datetime.now():
        info("Running scheduled backup")
        run_backup()