from enum import StrEnum


class TicketCategory(StrEnum):
    POS = "POS"
    PRINTING = "PRINTING"
    NETWORK = "NETWORK"
    SOFTWARE = "SOFTWARE"
    INVENTORY = "INVENTORY"
    SALES = "SALES"
    PAYMENT = "PAYMENT"
    ACCESS = "ACCESS"
    HARDWARE = "HARDWARE"
    OTHER = "OTHER"


class TicketPriority(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class TicketStatus(StrEnum):
    NEW = "NEW"
    AI_DIAGNOSING = "AI_DIAGNOSING"
    WAITING_FOR_EMPLOYEE = "WAITING_FOR_EMPLOYEE"
    AI_RESOLVING = "AI_RESOLVING"
    HUMAN_SUPPORT = "HUMAN_SUPPORT"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"


KEYWORD_CATEGORY_HINTS: list[tuple[tuple[str, ...], TicketCategory]] = [
    (("chek", "printer", "qog'oz", "qogoz", "chop"), TicketCategory.PRINTING),
    (("internet", "wifi", "tarmoq", "router", "dns"), TicketCategory.NETWORK),
    (("kassa", "pos", "smena"), TicketCategory.POS),
    (("fom", "f-apteka", "programma", "software"), TicketCategory.SOFTWARE),
    (("narx", "tovar", "ombor", "sotuv"), TicketCategory.SALES),
    (("terminal", "to'lov", "tolov", "click", "payme"), TicketCategory.PAYMENT),
    (("parol", "login", "ruxsat", "access"), TicketCategory.ACCESS),
    (("kompyuter", "monitor", "sichqon", "klaviatura"), TicketCategory.HARDWARE),
]


def classify_category(text: str) -> TicketCategory:
    lowered = text.lower()
    for keywords, category in KEYWORD_CATEGORY_HINTS:
        if any(k in lowered for k in keywords):
            return category
    return TicketCategory.OTHER


def suggest_priority(text: str, category: TicketCategory) -> TicketPriority:
    lowered = text.lower()
    critical_words = ("umuman", "ishlamay", "yopilmayapti", "critical", "stop", "to'xtadi")
    if any(w in lowered for w in critical_words) or category in {
        TicketCategory.POS,
        TicketCategory.PAYMENT,
        TicketCategory.NETWORK,
    }:
        return TicketPriority.HIGH
    return TicketPriority.MEDIUM
