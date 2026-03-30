from app import db
from app.models import Request, RequestItemImage, RequestStatus


# Contraintes miroir du modèle, centralisées ici
_MAX_FULL_NAME = 255
_MAX_WHATSAPP  = 50
_MAX_COUNTRY   = 100
_MAX_CITY      = 100
_DEFAULT_QTY   = 1

# Transitions autorisées
_ALLOWED_TRANSITIONS: dict[RequestStatus, set[RequestStatus]] = {
    RequestStatus.PENDING:    {RequestStatus.PROCESSING, RequestStatus.CANCELLED},
    RequestStatus.PROCESSING: {RequestStatus.QUOTED,     RequestStatus.CANCELLED},
    RequestStatus.QUOTED:     {RequestStatus.ACCEPTED,   RequestStatus.REJECTED},
    RequestStatus.ACCEPTED:   {RequestStatus.ORDERED},
    RequestStatus.REJECTED:   set(),
    RequestStatus.ORDERED:    set(),
    RequestStatus.CANCELLED:  set(),
}


class RequestService:

    @staticmethod
    def create(user, data: dict, images: list[dict] | None = None) -> Request:
        """
        Crée une Request et attache ses images en une seule transaction.
        `images` = [{"url": "..."}]
        """
        # ── Validation ────────────────────────────────────────────────────
        full_name = (data.get("fullName") or "").strip() or getattr(user, "full_name", None)
        if not full_name:
            raise ValueError("Le nom complet est requis.")
        if len(full_name) > _MAX_FULL_NAME:
            raise ValueError(f"Le nom complet ne peut pas dépasser {_MAX_FULL_NAME} caractères.")

        whatsapp = (data.get("whatsapp") or getattr(user, "whatsapp", None) or "")
        if len(whatsapp) > _MAX_WHATSAPP:
            raise ValueError(f"Le numéro WhatsApp ne peut pas dépasser {_MAX_WHATSAPP} caractères.")

        country = (data.get("country") or getattr(user, "country", None) or "")
        if len(country) > _MAX_COUNTRY:
            raise ValueError(f"Le pays ne peut pas dépasser {_MAX_COUNTRY} caractères.")

        city = (data.get("city") or getattr(user, "city", None) or "")
        if len(city) > _MAX_CITY:
            raise ValueError(f"La ville ne peut pas dépasser {_MAX_CITY} caractères.")

        try:
            quantity = int(data.get("quantity", _DEFAULT_QTY))
            if quantity < 1:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError("La quantité doit être un entier positif.")

        # ── Création dans une seule transaction ───────────────────────────
        req = Request(
            user_id=user.id if user else None,
            full_name=full_name,
            whatsapp=whatsapp or None,
            country=country  or None,
            city=city        or None,
            notes=data.get("notes"),
            quantity=quantity,
            status=RequestStatus.PENDING,
        )
        db.session.add(req)

        for img in (images or []):
            url = (img.get("url") or "").strip()
            if url:
                req.images.append(RequestItemImage(image_url=url))

        db.session.commit()
        return req

    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def update_status(request: Request, new_status: RequestStatus) -> Request:
        allowed = _ALLOWED_TRANSITIONS.get(request.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"Transition invalide : {request.status.value} → {new_status.value}."
            )
        request.status = new_status
        db.session.commit()
        return request

    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def cancel(request: Request) -> Request:
        return RequestService.update_status(request, RequestStatus.CANCELLED)