from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('reviewer', 'target', 'rating', 'created_at', 'is_removed')
    list_filter = ('is_removed', 'rating', 'created_at')
    search_fields = ('reviewer__user__first_name', 'reviewer__user__last_name', 'comment')
    actions = ['ukloni_recenzije', 'vrati_recenzije']

    def target(self, obj):
        return obj.instructor or obj.ski_center or obj.rental or '—'
    target.short_description = 'Subjekat'

    @admin.action(description='Ukloni izabrane recenzije (moderacija)')
    def ukloni_recenzije(self, request, queryset):
        from accounts.models import AdminLog
        for r in queryset:
            AdminLog.objects.create(admin=request.user, action='ukloni_recenziju', target=str(r))
        n = queryset.update(is_removed=True)
        self.message_user(request, f'Uklonjeno recenzija: {n}.')

    @admin.action(description='Vrati izabrane recenzije')
    def vrati_recenzije(self, request, queryset):
        n = queryset.update(is_removed=False)
        self.message_user(request, f'Vracena recenzija: {n}.')

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions