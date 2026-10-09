from django.contrib import admin
from .models import Company, Contact, Deal, Activity


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'industry', 'owner', 'created_at')
    search_fields = ('name', 'inn', 'website')
    list_filter = ('industry',)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'company', 'position', 'email', 'is_primary')
    list_filter = ('company', 'is_primary')
    search_fields = ('full_name', 'email', 'phone')


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'stage', 'amount', 'owner', 'created_at')
    list_filter = ('stage', 'owner', 'company')
    search_fields = ('title', 'company__name', 'description')
    date_hierarchy = 'created_at'


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('kind', 'subject', 'deal', 'company', 'author', 'created_at')
    list_filter = ('kind', 'author')
    search_fields = ('subject', 'body')

from .models import CrmTask


@admin.register(CrmTask)
class CrmTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'priority', 'assignee', 'deal', 'due_date', 'created_at')
    list_filter = ('status', 'priority', 'assignee')
    search_fields = ('title', 'description')
    date_hierarchy = 'created_at'