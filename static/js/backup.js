function logMessage(message) {
    
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    const timestamp = `[${hours}:${minutes}:${seconds}]`;
    const $textarea = $('#log-area');
    
    $textarea.append(timestamp + ' ' + message + '\n');
    $textarea.scrollTop($textarea[0].scrollHeight);
}

async function start_backup() {
    let response = await fetch('/backup/start')
    switch(response.status) {
        case 200:
            $('#status-text').text('Záloha spuštěna');
            logMessage("Záloha úspěšně spuštěna");
            break;
        case 500:
            $('#status-text').text('Chyba');
            logMessage(response.text());
            break;
    }
}

async function save_config() {
    const payload = {
        socks_proxy: $('#socks-proxy').val() || null,
        http_proxy: $('#http-proxy').val() || null,
        wikis: $('#wikilist').val() || null,
        blacklist: $('#blacklist').val() || null,
        delay: parseInt($('#delay').val(), 10) || null,
        ratelimit_size: parseInt($('#rlimit_size').val()) || null,
        ratelimit_refill: parseInt($('#rlimit_refill').val()) || null,
    }
    await fetch('/backup/config', {
        method: "POST",
        body: JSON.stringify(payload)
    })
}

$("#btn-start").on("click", start_backup);
$("#btn-config").on("click", () => {$('#config-container').fadeToggle()});
$("#save-config").on("click", save_config)
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
