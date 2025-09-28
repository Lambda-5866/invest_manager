from django.db import models

class Asset(models.Model):
    ASSET_TYPES = [
        ('KRW', 'Korea Won'),
        ('GOLD', 'Gold'),
        ('USD', 'US Dollar'),
        ('JPY', 'Japan Yen'),
        ('CNY', 'China Yuan'),
    ]

    name = models.CharField(max_length=50)
    asset_type = models.CharField(max_length=10, choices=ASSET_TYPES)
    amount = models.DecimalField(max_digits=20, decimal_places=4)
    buy_price = models.DecimalField(max_digits=20, decimal_places=2)
    buy_date = models.DateField()


    def __str__(self):
        return f"{self.name} ({self.asset_type})"