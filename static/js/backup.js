const dummy_status = [
    {
      "finished_articles": 67,
      "messages": [
        {
          "error_kind": null,
          "error_message": null,
          "msg_type": 2,
          "name": null,
          "status": 0,
          "tag": "o5-cs",
          "total": null
        },
        {
          "error_kind": null,
          "error_message": null,
          "msg_type": 1,
          "name": null,
          "status": null,
          "tag": "o5-cs",
          "total": 67
        },
        {
          "error_kind": null,
          "error_message": null,
          "msg_type": 2,
          "name": null,
          "status": 1,
          "tag": "o5-cs",
          "total": null
        },
        {
          "error_kind": null,
          "error_message": null,
          "msg_type": 2,
          "name": null,
          "status": 1,
          "tag": "o5-cs",
          "total": null
        },
        {
          "error_kind": null,
          "error_message": null,
          "msg_type": 2,
          "name": null,
          "status": 2,
          "tag": "o5-cs",
          "total": null
        },
        {
          "error_kind": null,
          "error_message": null,
          "msg_type": 2,
          "name": null,
          "status": 4,
          "tag": "o5-cs",
          "total": null
        },
        {
          "error_kind": null,
          "error_message": null,
          "msg_type": 2,
          "name": null,
          "status": 3,
          "tag": "o5-cs",
          "total": null
        },
        {
          "error_kind": null,
          "error_message": null,
          "msg_type": 2,
          "name": null,
          "status": 5,
          "tag": "o5-cs",
          "total": null
        },
        {
          "error_kind": null,
          "error_message": null,
          "msg_type": 5,
          "name": null,
          "status": null,
          "tag": "o5-cs",
          "total": null
        }
      ],
      "postponed_articles": 0,
      "status": 8,
      "total_articles": 67,
      "total_errors": 0,
      "wiki_tag": "o5-cs"
    }
  ]

const MessageType = Object.freeze({
  Handshake: 0,
  Preflight: 1,
  Progress: 2,
  ErrorFatal: 3,
  ErrorNonfatal: 4,
  FinishSuccess: 5,
  PageDone: 6,
  PagePostponed: 7
})

const Status = Object.freeze({
  BuildingSitemap: 0,
  PagesMain: 1,
  ForumsMain: 2,
  PagesPending: 3,
  FilesPending: 4,
  Compressing: 5,
  FatalError: 6,
  Other: 7,
  Done: 8
})

const ErrorKind = Object.freeze({
    ErrorClientOffline: 0,
    ErrorMalformedSitemap: 1,
    ErrorVoteFetch: 2,
    ErrorFileFetch: 3,
    ErrorLockStatusFetch: 4,
    ErrorForumListFetch: 5,
    ErrorForumPostFetch: 6,
    ErrorFileMetaFetch: 7,
    ErrorFileUnlink: 8,
    ErrorForumCountMismatch: 9,
    ErrorWikidotInternal: 10,
    ErrorWhatTheFuck: 11,
    ErrorMetaMissing: 12,
    ErrorGivingUp: 13,
    ErrorTokenInvalidated: 14
})

function errorMessage(error) {
  switch(error) {
    case ErrorKind.ErrorClientOffline: return "Nelze pokračovat. Klient Wikicomma je offline."
    case ErrorKind.ErrorMalformedSitemap: return "Mapa stránky je poškozená."
    case ErrorKind.ErrorVoteFetch: return "Chyba při stahování dat hodnocení."
    case ErrorKind.ErrorFileFetch: return "Chyba při stahování souboru."
    case ErrorKind.ErrorLockStatusFetch: return "Chyba při kontrole statusu uzamčení."
    case ErrorKind.ErrorForumListFetch: return "Chyba při stahování seznamu fór."
    case ErrorKind.ErrorForumPostFetch: return "Chyba při stahování příspěvku na fóru."
    case ErrorKind.ErrorFileMetaFetch: return "Chyba při stahování metadat souboru."
    case ErrorKind.ErrorFileUnlink: return "Soubor nelze smazat."
    case ErrorKind.ErrorForumCountMismatch: return "Chybný počet příspěvků."
    case ErrorKind.ErrorWikidotInternal: return "Interní chyba wikidot serveru (sračka nechce spolupracovat)."
    case ErrorKind.ErrorWhatTheFuck: return "Nevím co se stalo ale podle programátora wikicomma je to zlý."
    case ErrorKind.ErrorMetaMissing: return "Chybí metadata když by chybět neměla."
    case ErrorKind.ErrorGivingUp: return "Stahování revize opakovaně selhalo. Vzdávám to."
    case ErrorKind.ErrorTokenInvalidated: return "Wikidot zneplatnil token. Čekáme 30s."
  }
}

function statusMessage(status) {
  switch(status) {
    case Status.BuildingSitemap: return "Vytvářím mapu stránky."
    case Status.PagesMain: return "Zálohuji stránky."
    case Status.ForumsMain: return "Zálohuji fóra."
    case Status.PagesPending: return "Zpracovávám chybějící stránky."
    case Status.FilesPending: return "Zpracovávám chybějící soubory."
    case Status.Compressing: return "Komprimuji data."
    case Status.FatalError: return "Fatální chyba klienta. Nelze pokračovat."
    case Status.Done: return "Hotovo, WikiComma klient se ukončuje"
  }
}

let updateIntervalId = 0;

function updateStatus() {
  fetch('/backup/status').then(response => response.json()).then(data => {
    messages = []
    messageStrings = []
    data.forEach(wiki => {
      $(`#${wiki.wiki_tag}-count`).text(`${wiki.finished_articles} / ${wiki.total_articles}`)
      $(`#${wiki.wiki_tag}-progress`).animate({width: `${(wiki.total_articles / wiki.finished_articles) * 100}%`})
      messages.push(...wiki.messages)
    })
    messages.sort((a, b) => a.timestamp - b.timestamp)
    messages.forEach(msg => {
      switch(msg.msg_type) {
        case MessageType.Handshake: messageStrings.push(`[${msg.tag}] Klient připojen`); break;
        case MessageType.Preflight: messageStrings.push(`[${msg.tag}] Nalezeno ${msg.total} stránek k záloze`); break;
        case MessageType.Progress:
          if(msg.status == Status.PagesMain) {
            break;
          } else {
            messageStrings.push(`[${msg.tag}] ${statusMessage(msg.status)}`); break;
          }
        case MessageType.ErrorNonfatal: messageStrings.push(`[${msg.tag}] Chyba: ${msg.error_message}`); break;
        case MessageType.ErrorFatal: messageStrings.push(`[${msg.tag}] Kritická chyba: ${msg.error_message}`); break;
        case MessageType.FinishSuccess:
          messageStrings.push(`[${msg.tag}] Záloha dokončena, zpracovávám data`);
          clearInterval(updateIntervalId);
          break;
      }
    })
    $("#log-area").text(messageStrings.join('\n'))
  })
}

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
    setInterval(updateStatus, 2000);
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

// Run this on page load
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
