from app.models import Stat


class StatService:
    @staticmethod
    def get_page_stats(page: str) -> list:
        return [s.to_dict() for s in Stat.query.filter_by(page=page, is_active=True).order_by(Stat.sort_order).all()]

    @staticmethod
    def get_homepage_stats() -> list:
        return StatService.get_page_stats("homepage")

    @staticmethod
    def get_community_stats() -> list:
        return StatService.get_page_stats("community")
