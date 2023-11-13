from flask import url_for, render_template, redirect, Blueprint, flash, abort, session, request, g, current_app as c
from flask_login import current_user, login_required
from flask_wtf.csrf import generate_csrf, validate_csrf
from forms import NewNoteForm
from logging import warning, info
from models.note import Note

NoteController = Blueprint('NoteController', __name__)

@NoteController.route('/notes')
@login_required
def notes():
    dbs = c.config['database']
    return render_template('notes.j2', form=NewNoteForm(), notes=dbs.get_notes(), js_token=generate_csrf(None, 'ajax_key'))


@NoteController.route('/notes/add', methods=['POST'])
@login_required
def add_note():
    dbs = c.config['database']

    form = NewNoteForm()
    if not form.validate_on_submit():
        flash('Neplatný požadavek, zkuste to prosím znovu')
        return redirect(url_for('NoteController.notes'))
    note = Note(0, form.title.data, '\r\n'.join(form.note.data.splitlines()), current_user.nickname, current_user.discord)
    dbs.add_note(note, current_user.get_id())
    return redirect(url_for('NoteController.notes'))


@NoteController.route('/notes/delete', methods=['POST'])
@login_required
def delete_note():
    dbs = c.config['database']
    delete = request.form.get('deleteid', None, int)
    if not delete:
        warning(f'Invalid request to AJAX endpoint as user {current_user.nickname} (ID: {current_user.get_id()}) from client IP {request.remote_addr}')
        abort(400)
    info(f'User {current_user.nickname} (ID: {current_user.get_id()}) deleted note ID {delete}')
    dbs.delete_note(delete)
    return "OK", 200

@NoteController.route('/notes/edit', methods=['post'])
@login_required
def update_note():
    dbs = c.config['database']

