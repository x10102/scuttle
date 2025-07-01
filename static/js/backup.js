async function start_backup() {
    let response = await fetch('/backup/start')
    switch(response.status) {
        case 200:
            $('#status-text').text('Záloha spuštěna')
            $('#log-area').append('Záloha úspěsně spuštěna')
        case 500:
            $('#status-text').text('Chyba')
            $('#log-area').append(await response.text()+"\n")
    }
}

$("#btn-start").on("click", start_backup);
last_status_id = -1
const backupTrigger = document.currentScript.getAttribute('run_url')

function timeStr() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    return `[${hours}:${minutes}:${seconds}]`;
}

function logEvent(text) {
    $('#backup-log').text($('#backup-log').text() + `${timeStr()} ${text}`)
}

function runBackup() {
    logEvent("Spouštím zálohu")
}

function setProgressVal(progressbar_id, progress) {
    $(`#${progressbar_id} > div`).css("width", `${progress*100}%`)
}
