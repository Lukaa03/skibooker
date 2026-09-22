from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import AdminLog


@admin.register(AdminLog)
class AdminLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'admin', 'action', 'target')
    list_filter = ('action', 'created_at')
    search_fields = ('target', 'admin__username')
    readonly_fields = ('admin', 'action', 'target', 'details', 'created_at')
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

admin.site.unregister(User)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    actions = ['blokiraj', 'odblokiraj']

    @admin.action(description='Blokiraj izabrane naloge')
    def blokiraj(self, request, queryset):
        for u in queryset:
            AdminLog.objects.create(admin=request.user, action='blokiraj', target=u.username)
        n = queryset.update(is_active=False)
        self.message_user(request, f'Blokirano naloga: {n}.')

    @admin.action(description='Odblokiraj izabrane naloge')
    def odblokiraj(self, request, queryset):
        n = queryset.update(is_active=True)
        self.message_user(request, f'Odblokirano naloga: {n}.')