from logging import warning, info, error, debug
from queue import Queue
from threading import Thread
from flask import Blueprint, redirect, render_template, url_for, current_app,jsonify
from connectors.portainer import PortainerError
from connectors.wikicomma import zmq_listener_thread
from extensions import portainer

AutobackupController = Blueprint("AutobackupController", __name__)

zmq_thread: Thread = None
zmq_message_queue = Queue()
zmq_status = {}

@AutobackupController.route('/backups', methods=["GET"])
def backup_index():
    return render_template('backups/backup_index.j2')

@AutobackupController.route('/status', methods=["GET"])
def backup_status():
    return jsonify(zmq_status)

@AutobackupController.route('/backup/start', methods=["GET"])
def run_backup():
    info("Preparing to start backup")
    if not portainer.is_initialized():
        error("Portainer connector is not initialized, can't proceed")
        return "Konfigurace Portaineru chybí. Nelze pokračovat.", 500
    try:
        portainer.login()
    except PortainerError as e:
        error(f"Cannot login to portainer ({str(e)})")
        return "Přihlášení k portaineru selhalo. Nelze pokračovat", 500
    info('Successfully logged in to portainer')

    zmq_url = current_app.config.get("WIKICOMMA", None)
    if zmq_url:
        zmq_url = zmq_url.get('WCMA_ZMQ_URL', None)
    if not zmq_url:
        error("Wikicomma ZeroMQ URL not set, can't proceed")
        return "Chyba: Konfigurace WikiComma chybí.", 500

    zmq_thread = Thread(target=zmq_listener_thread, args=(zmq_url,zmq_status,zmq_message_queue), daemon=True)

    info('Starting ZeroMQ listener')
    zmq_thread.start()

    info('Starting Wikicomma container')
    try:
        portainer.start_container()
    except PortainerError as e:
        error(f"Couldn't start container, can't proceed ({str(e)})")
        return "Chyba: Kontejner nelze spustit", 500

    info('Container started')

    return "Záloha byla spuštěna"