from logging import error, info
from queue import Queue
import zmq
from dataclasses import dataclass
from enum import IntEnum
import json
from logging import debug, warning

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
    total: int = None

def zmq_listener_thread(address: str, data_dict: dict, message_queue: Queue):

    context = zmq.Context()
    socket = context.socket(zmq.PULL)
    socket.RCVTIMEO = 60 * 5 * 1000  # 5 minutes

    # Connect to the sender's socket
    socket.bind(address)
    print(f"ZMQ receiver bound to {address}")

    while True:
        message = socket.recv_string()
        print("Message received")
        message_json = json.loads(message)
        tag = message_json['tag']
        message_type = MessageType(message_json['type'])
        match message_type:
            case MessageType.PageDone:
                data_dict[tag]['done']+=1
                debug(f"[{tag}] Done: {data_dict[tag]['done']} / {data_dict[tag]['total']}")

            case MessageType.PagePostponed:
                data_dict[tag]['postponed']+=1
                debug(f"[{tag}] Postponed: {data_dict[tag]['postponed']} / {data_dict[tag]['total']}")

            case MessageType.Handshake:
                data_dict[tag] = {
                    'done': 0,
                    'total': 0,
                    'postponed': 0,
                    'finished': False
                }
                message_queue.put_nowait(Message(message_type, tag))
                print(f"[{tag}] Established connection")

            case MessageType.Preflight:
                message_queue.put_nowait(Message(message_type, tag, total=message_json['total']))
                debug(f"[{tag}] Preflight info: {message_json['total']} total pages")
                data_dict[tag]['total'] = message_json['total']

            case MessageType.Progress:
                message_queue.put_nowait(Message(message_type, tag, status=Status(message_json['status'])))
                debug(f"[{tag}] Status: {Status(message_json['status']).name}")

            case MessageType.ErrorNonfatal:
                message_queue.put_nowait(Message(message_type, tag, error_kind=ErrorKind(message_json['errorKind'])))
                warning(f"[{tag}] Encountered Error: {ErrorKind(message_json['errorKind']).name}")

            case MessageType.ErrorFatal:
                message_queue.put_nowait(Message(message_type, tag, error_kind=ErrorKind(message_json['errorKind'])))
                error(f"[{tag}] Encountered Error: {ErrorKind(message_json['errorKind']).name}. Exiting")
                return
            
            case MessageType.FinishSuccess:
                message_queue.put_nowait(Message(MessageType.FinishSuccess, tag))
                data_dict[tag]['finished'] = True
                debug(f"[{tag}] Status: DONE")
                if all([wiki['finished'] for wiki in data_dict.values()]):
                    debug("BACKUP FINISHED")
                    message_queue.put_nowait(Message(MessageType.FinishSuccess, "all"))
                    return
        