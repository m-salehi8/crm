from rest_framework import serializers
from .models import Invoice, InvoiceCover, InvoiceCategory, InvoiceCoverTask
from django_jalali.serializers.serializerfield import JDateField


class SerInvoiceCover(serializers.ModelSerializer):
    unit_name = serializers.CharField(read_only=True, source='unit.title')
    user_name = serializers.CharField(read_only=True, source='user.name')
    begin_date = JDateField()
    end_date = JDateField()
    lock_time = serializers.SerializerMethodField()
    accept_time = serializers.SerializerMethodField()
    confirm1_time = serializers.SerializerMethodField()
    confirm2_time = serializers.SerializerMethodField()
    confirm3_time = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()

    def get_can_edit(self, obj):
        try:
            user = self.context['user']
            return user.groups.filter(name__in=['invoice-confirm1']).exists()
        except:
            return False


    def get_lock_time(self, invoicecover):
        return invoicecover.lock_time.strftime('%Y-%m-%d %H:%M') if invoicecover.lock_time else None

    def get_accept_time(self, invoicecover):
        return invoicecover.accept_time.strftime('%Y-%m-%d %H:%M') if invoicecover.accept_time else None

    def get_confirm1_time(self, invoicecover):
        return invoicecover.confirm1_time.strftime('%Y-%m-%d %H:%M') if invoicecover.confirm1_time else None

    def get_confirm2_time(self, invoicecover):
        return invoicecover.confirm2_time.strftime('%Y-%m-%d %H:%M') if invoicecover.confirm2_time else None

    def get_confirm3_time(self, invoicecover):
        return invoicecover.confirm3_time.strftime('%Y-%m-%d %H:%M') if invoicecover.confirm3_time else None

    class Meta:
        model = InvoiceCover
        fields = ['can_edit', 'id', 'unit', 'unit_name', 'user', 'user_name', 'unit_manager', 'no', 'begin_date', 'end_date', 'locked', 'lock_time', 'accepted', 'accept_time', 'accept_note', 'invoice_count', 'total_price_sum', 'price_sum', 'type', 'sheba', 'sheba_owner', 'setadiran', 'business_license_url', 'id_card_url', 'factor_url', 'slip_url', 'confirm1', 'confirm2', 'confirm3', 'confirm1_note', 'confirm2_note', 'confirm3_note', 'confirm1_time', 'confirm2_time', 'confirm3_time', 'deposit_time']


class SerInvoiceCategory(serializers.ModelSerializer):
    class Meta:
        model = InvoiceCategory
        fields = ['id', 'title']


class SerInvoice(serializers.ModelSerializer):
    unit_name = serializers.CharField(read_only=True, source='unit.title')
    date = JDateField()

    class Meta:
        model = Invoice
        fields = ['id', 'unit', 'unit_name', 'cover', 'category', 'no', 'date', 'has_paper', 'value_added', 'issuer', 'description', 'price']


class SerInvoiceCoverTask(serializers.ModelSerializer):
    user = serializers.CharField(read_only=True, source='user.get_full_name')

    class Meta:
        model = InvoiceCoverTask
        fields = ['id', 'status', 'accept', 'user', '_time', 'note']
