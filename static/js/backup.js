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