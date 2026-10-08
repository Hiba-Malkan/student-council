from django.utils.deprecation import MiddlewareMixin

from .audit import clear_current_user, set_current_user


class DisciplineAuditMiddleware(MiddlewareMixin):
    def process_request(self, request):
        set_current_user(getattr(request, 'user', None))

    def process_response(self, request, response):
        clear_current_user()
        return response