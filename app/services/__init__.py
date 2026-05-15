# ── Services existants ────────────────────────────────────────────────────────
from .notification_service import NotificationService
from .pricing_service      import PricingService
from .request_service      import RequestService
from .quotation_service    import QuotationService
from .order_service        import OrderService
from .payment_service      import PaymentService
from .supplier_service     import SupplierService

# ── Nouveaux services v2 ──────────────────────────────────────────────────────
from .auth_service         import AuthService
from .otp_service          import OTPService
from .audit_service        import AuditService
from .cloudinary_service   import CloudinaryService
from .whatsapp_service     import WhatsAppService
from .pdf_service          import PDFService
from .wave_service         import WaveService
from .stat_service         import StatService
