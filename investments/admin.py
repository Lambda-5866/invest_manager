from django.contrib import admin
from .models import Asset


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('asset_type', 'amount', 'buy_price', 'buy_date')
    list_filter = ('asset_type',)
