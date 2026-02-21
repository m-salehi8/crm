from django.contrib import admin
import django_jalali.admin as jadmin
from unfold.admin import ModelAdmin, TabularInline
from .models import InvoiceCover, InvoiceCategory, Invoice


class InvoiceInline(TabularInline):
    model = Invoice
    extra = 0


@admin.register(InvoiceCover)
class InvoiceCoverAdmin(ModelAdmin):
    list_display = ['no', 'type', 'unit', 'invoice_count', 'price_sum', 'locked', 'accepted']
    list_filter = ['type', 'locked', 'accepted', 'unit']
    search_fields = ['no']
    inlines = [InvoiceInline]
    raw_id_fields = ['user']


@admin.register(InvoiceCategory)
class InvoiceCategoryAdmin(ModelAdmin):
    list_display = ['id', 'title', 'is_available']

