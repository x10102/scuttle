from logging import error, info
from queue import Queue
from dataclasses import dataclass, field
from enum import IntEnum
from flask import current_app
import json
from logging import debug, warning
import datetime
from db import WikiCommaConfig, Wiki

class MessageType(IntEnum):
    Handshake = 0,
    Preflight = 1,
    Progress = 2,
    ErrorFatal = 3,
    ErrorNonfatal = 4,
    FinishSuccess = 5,
    PageDone = 6,
    PagePostponed = 7

class Status(IntEnum):
    BuildingSitemap = 0,
    PagesMain = 1,
    ForumsMain = 2,
    PagesPending = 3,
    FilesPending = 4,
    Compressing = 5,
    FatalError = 6,
    Other = 7,
    Done = 8

    def __str__(self) -> str:
        match self.value:
            case Status.BuildingSitemap: return "Vytvářím mapu stránky."
            case Status.PagesMain: return "Zálohuji stránky."
            case Status.ForumsMain: return "Zálohuji fóra."
            case Status.PagesPending: return "Zpracovávám chybějící stránky."
            case Status.FilesPending: return "Zpracovávám chybějící soubory."
            case Status.Compressing: return "Komprimuji data."
            case Status.FatalError: return "Fatální chyba klienta. Nelze pokračovat."
            case Status.Done: return "Hotovo, WikiComma klient se ukončuje"
            case _: return "Neznámý status."

class ErrorKind(IntEnum):
    ErrorClientOffline = 0
    ErrorMalformedSitemap = 1
    ErrorVoteFetch = 2
    ErrorFileFetch = 3
    ErrorLockStatusFetch = 4
    ErrorForumListFetch = 5
    ErrorForumPostFetch = 6
    ErrorFileMetaFetch = 7
    ErrorFileUnlink = 8
    ErrorForumCountMismatch = 9
    ErrorWikidotInternal = 10
    ErrorWhatTheFuck = 11
    ErrorMetaMissing = 12
    ErrorGivingUp = 13,
    ErrorTokenInvalidated = 14

    def __str__(self) -> str:
        match self.value:
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

@dataclass
class Message:
    msg_type: MessageType
    tag: str
    name: str = None
    status: Status = None
    error_kind: ErrorKind = None
    error_message: str = None
    total: int = None
    timestamp: datetime.datetime = field(default_factory=lambda: datetime.datetime.timestamp(datetime.datetime.now()))

def generate_config(path: str) -> bool:
    cfg = current_app.config.get("BACKUP")
    if not cfg:
        error(f"Cannot generate config - missing key")
        return False
    for param in ['SELF_ADDRESS', 'BACKUP_COMMON_PATH', 'BACKUP_ARCHIVE_PATH']: 
        if param not in cfg: 
            error(f"Cannot generate backup config - missing parameter {param}")
            return False
    wc_config: WikiCommaConfig = WikiCommaConfig.get_or_none()
    if not wc_config:
        error("Cannot generate config - missing data")
        return False
    config = {
        "base_directory": cfg['BACKUP_COMMON_PATH'],
        "wikis": [{"name": w.name, "url": w.url} for w in Wiki.select().where(Wiki.is_active == True)],
        "delay_ms": wc_config.delay,
        "socks_proxy": wc_config.socks_proxy,
        "http_proxy": wc_config.http_proxy,
        "user_list_cache_freshness": 86400,
        "maximum_jobs": None,
        "scuttle_url": cfg['SELF_ADDRESS'],
        "blacklist": [w for w in wc_config.blacklist.split('\n') if w] if wc_config.blacklist else [],
        "ratelimit": {
            "bucket_size": wc_config.ratelimit_size or 60,
            "refill_seconds": wc_config.ratelimit_refill or 60
        }
    }
    try:
        with open(path, "w") as cfg_file:
            json.dump(config, cfg_file, indent=4)
    except:
        error("Cannot generate config - I/O error")
        return False
    return True