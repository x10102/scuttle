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
    }).then(async response => {
        if(response.status == 200) {
            $("#save-result").removeClass("text-red-600 bg-red-300/5 border-red-300/10")
            $("#save-result").addClass("text-green-600 bg-green-300/5 border-green-300/10")
            $("#save-result").text("Konfigurace úspěšně uložena")
            logMessage("Konfigurace uložena")
        } else {
            const reason = await response.text()
            $("#save-result").removeClassClass("text-green-600 bg-green-300/5 border-green-300/10")
            $("#save-result").addClass("text-red-600 bg-red-300/5 border-red-300/10")
            $("#save-result").text(reason)
            logMessage(`Konfiguraci nelze uložit: ${reason}`)
        }
        $("#save-result").fadeIn(500).fadeOut(2000)
    })
}

// Setup click handlers
$("#btn-start").on("click", start_backup);
$("#btn-config").on("click", () => {$('#config-container').fadeToggle()});
$("#save-config").on("click", save_config)

// Load current config into ui
$(function() {
    // Hide the save result for now
    $("#save-result").toggle()
    // Fetch the config from server and load it into the form fields
    fetch('/backup/config').then(response => response.json()).then(data => {
        console.log(data)
        $("#socks-proxy").val(data.config.socks_proxy)
        $("#http-proxy").val(data.config.http_proxy)
        $("#delay").val(data.config.delay)
        $("#rlimit-size").val(data.config.ratelimit_size)
        $("#rlimit-refill").val(data.config.ratelimit_refill)
        $("#blacklist").val(data.config.blacklist)
        data.wikis.forEach(wiki => $("#wikilist").append(wiki.url+'\n'))
    })
})

function setProgressVal(progressbar_id, progress) {
    $(`#${progressbar_id} > div`).css("width", `${progress*100}%`)
}
