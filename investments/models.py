from django.db import models
from decimal import Decimal

class Asset(models.Model):
    ASSET_TYPES = [
        ('KRW', 'KRW'),
        ('GOLD', 'GOLD'),
        ('USD', 'USD'),
        ('JPY', 'JPY'),
        ('CNY', 'CNY'),
    ]

    asset_type = models.CharField(max_length=10, choices=ASSET_TYPES)
    amount = models.DecimalField(max_digits=20, decimal_places=0)
    buy_price = models.DecimalField(max_digits=20, decimal_places=4)
    buy_date = models.DateField()

    def __str__(self):
        return f"{self.asset_type}"