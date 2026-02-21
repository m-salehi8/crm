from rest_framework.permissions import BasePermission


class IsFlowAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='flow').exists()


class IsProclamationAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='proclamation').exists()


class IsInvoiceCollector(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name__in=['invoice-registrar', 'invoice-confirm1', 'invoice-confirm3', 'invoice-accept', 'invoice-deposit']).exists() or request.user.is_head_of_unit


class IsPmUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='pm').exists()


class IsHrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='hr').exists()


class IsRoomCateringAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='room_catering').exists()


class IsManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.post.is_manager


class HasPost(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.post)
