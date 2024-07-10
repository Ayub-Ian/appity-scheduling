from django.db import models

class Service(models.Model):
    PRIVATE = 0
    PUBLIC = 1

    ACCESS_CHOICES = [
        (PUBLIC, 'Public'),
        (PRIVATE, 'Private'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(null=True)
    category = models.CharField(max_length=100, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    duration = models.IntegerField()
    access = models.CharField(max_length=50, choices=ACCESS_CHOICES, default=PUBLIC)

    class Meta:
        app_label = 'core'
        verbose_name = 'services'

    def __str__(self):
        return self.name
