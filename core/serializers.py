from rest_framework import serializers

from core.models.models import Client

class ClientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Client
        fields = (
            'company', 'address1', 'address2', 'city', 'country', 'state', 'zip_code',
            'phone', 'fax', 'id'
        )
        read_only_fields = ('id',)

    # def to_internal_value(self, data):
    #     mutable_data = dict(data)

    #     vat_id = mutable_data.get('vat_id')
    #     if vat_id:
    #         mutable_data['vat_id'] = vat_id.strip().upper()

    #     return super().to_internal_value(data=mutable_data)
