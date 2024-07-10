from django.db import DataError
from django.db import models

# from common.logger import get_fleio_logger
from .models import Client
# from .models import PermissionSet

# LOG = get_fleio_logger(__name__)


class RoleManager(models.Manager):
    def get_owner_role(self) -> 'Role':
        owner_role = self.filter(name='Owner', default=True).first()
        if not owner_role:
            # LOG.error('Owner role does not exists.')
            pass
        return owner_role


class Role(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=64, null=False, blank=False)
    default = models.BooleanField(default=False)
    public = models.BooleanField(default=False)
    parent = models.ForeignKey('Role', related_name='children', on_delete=models.SET_NULL, null=True, blank=True)
    owner = models.ForeignKey(Client, related_name='roles', on_delete=models.CASCADE, null=True, blank=True)
    # permissions = models.OneToOneField(PermissionSet, on_delete=models.SET_NULL, null=True, blank=True)

    objects = RoleManager()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        parent = self.parent
        while parent:
            if parent.id == self.id:
                raise DataError('You cannot set a descendant as parent')
            parent = parent.parent

        return super().save(
            force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields,
        )

    @property
    def display_name(self):
        owner = '{}::'.format(self.owner.name) if self.owner else ''
        return '{}{}'.format(owner, self.name)

    def __str__(self):
        return '{}({})'.format(self.display_name, self.id)
