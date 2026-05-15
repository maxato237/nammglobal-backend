from flask import request


def get_pagination_params() -> tuple[int, int]:
    """Extrait page et per_page depuis les query params."""
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    return max(page, 1), per_page


def paginate_query(query, page: int, per_page: int) -> dict:
    """Pagine une SQLAlchemy query et retourne un dict standard."""
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        "items": paginated.items,
        "total": paginated.total,
        "page": paginated.page,
        "pages": paginated.pages,
        "per_page": paginated.per_page,
        "has_next": paginated.has_next,
        "has_prev": paginated.has_prev,
    }
