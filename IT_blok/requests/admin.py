from django.contrib import admin
from .models import RequestToAdmin, RequestComment

@admin.register(RequestToAdmin)
class RequestToAdminAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'created_by', 'assigned_to', 'status', 'created_at']
    list_filter = ['status', 'is_auto', 'created_at']
    search_fields = ['title', 'description', 'created_by__username']
    readonly_fields = ['created_at', 'taken_at', 'closed_at']


@admin.register(RequestComment)
class RequestCommentAdmin(admin.ModelAdmin):
    list_display = ['request', 'author', 'created_at']
    list_filter = ['created_at']