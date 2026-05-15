from enum import Enum


# ── Rôles utilisateur ─────────────────────────────────────────────────────────
class UserRole(str, Enum):
    CLIENT = "client"
    OPERATOR = "operator"
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"  # alias legacy


# ── Statuts demande (Request) ─────────────────────────────────────────────────
class RequestStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    QUOTED = "quoted"
    ACCEPTED = "accepted"
    PARTIALLY_ACCEPTED = "partially_accepted"
    REJECTED = "rejected"
    ORDERED = "ordered"
    CANCELLED = "cancelled"


REQUEST_STATUS_LABELS = {
    RequestStatus.PENDING: "En attente",
    RequestStatus.PROCESSING: "En traitement",
    RequestStatus.QUOTED: "Devis envoyé",
    RequestStatus.ACCEPTED: "Acceptée",
    RequestStatus.PARTIALLY_ACCEPTED: "Partiellement acceptée",
    RequestStatus.REJECTED: "Refusée",
    RequestStatus.ORDERED: "Commandée",
    RequestStatus.CANCELLED: "Annulée",
}


# ── Statuts devis (Quotation) ─────────────────────────────────────────────────
class QuotationStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    ACCEPTED = "accepted"
    PARTIALLY_ACCEPTED = "partially_accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


# ── Statuts commande (Order) ──────────────────────────────────────────────────
class OrderStatus(str, Enum):
    CONFIRMED = "confirmed"
    SUPPLIER_ORDERED = "supplier_ordered"
    IN_TRANSIT_CN = "in_transit_cn"
    SHIPPED = "shipped"
    CUSTOMS = "customs"
    DELIVERED = "delivered"
    ISSUE = "issue"
    CANCELLED = "cancelled"


ORDER_STATUS_LABELS = {
    OrderStatus.CONFIRMED: "Confirmée",
    OrderStatus.SUPPLIER_ORDERED: "Commandée fournisseur",
    OrderStatus.IN_TRANSIT_CN: "En transit Chine",
    OrderStatus.SHIPPED: "Expédiée",
    OrderStatus.CUSTOMS: "En douane",
    OrderStatus.DELIVERED: "Livrée",
    OrderStatus.ISSUE: "Problème signalé",
    OrderStatus.CANCELLED: "Annulée",
}


# ── Statuts paiement (Payment) ────────────────────────────────────────────────
class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    MTN_MOMO = "mtn_momo"
    ORANGE_MONEY = "orange_money"
    WAVE = "wave"
    AIRTEL = "airtel"
    MOOV = "moov"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"


# ── Statuts vague (Wave) ──────────────────────────────────────────────────────
class WaveStatus(str, Enum):
    PLANNED = "planned"
    OPEN = "open"
    CLOSED = "closed"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


# ── Types événements chinois ──────────────────────────────────────────────────
class ChineseEventType(str, Enum):
    NEW_YEAR = "new_year"
    GOLDEN_WEEK = "golden_week"
    MID_AUTUMN = "mid_autumn"
    QINGMING = "qingming"
    DRAGON_BOAT = "dragon_boat"
    FACTORY_OFF = "factory_off"
    CUSTOM = "custom"


class ChineseEventSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ── Canaux notification ───────────────────────────────────────────────────────
class NotificationChannel(str, Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    WHATSAPP = "whatsapp"


# ── Canal OTP ─────────────────────────────────────────────────────────────────
class OTPChannel(str, Enum):
    WHATSAPP = "whatsapp"
    EMAIL = "email"


# ── Statuts formation ─────────────────────────────────────────────────────────
class ModuleProgressStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class CourseSessionStatus(str, Enum):
    PLANNED = "planned"
    OPEN = "open"
    FULL = "full"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EnrollmentPaymentStatus(str, Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    REFUNDED = "refunded"
    FAILED = "failed"


# ── Contact ───────────────────────────────────────────────────────────────────
class ContactSubject(str, Enum):
    INFO = "info"
    ORDER_ISSUE = "order_issue"
    PARTNERSHIP = "partnership"
    COMPLAINT = "complaint"
    OTHER = "other"


class ContactStatus(str, Enum):
    NEW = "new"
    READ = "read"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


# ── Paramètres système ────────────────────────────────────────────────────────
class SettingValueType(str, Enum):
    STRING = "string"
    INT = "int"
    BOOL = "bool"
    JSON = "json"


# ── Communauté ────────────────────────────────────────────────────────────────
class CommunityPlatform(str, Enum):
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    TIKTOK = "tiktok"


# ── Surcharge produit ─────────────────────────────────────────────────────────
class SurchargeType(str, Enum):
    PER_KG = "per_kg"
    FIXED = "fixed"
    NONE = "none"


# ── Messages API standardisés ─────────────────────────────────────────────────
class Messages:
    NOT_FOUND = "Ressource introuvable."
    FORBIDDEN = "Accès refusé."
    UNAUTHORIZED = "Authentification requise."
    INVALID_TOKEN = "Token invalide."
    TOKEN_EXPIRED = "Token expiré."
    SERVER_ERROR = "Erreur serveur interne."
    CREATED = "Créé avec succès."
    UPDATED = "Mis à jour avec succès."
    DELETED = "Supprimé avec succès."
