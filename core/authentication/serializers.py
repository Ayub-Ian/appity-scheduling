from django.conf import Settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from core.models.models import AppUser, Client

class LoginSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=255)
    password = serializers.CharField(max_length=255)
    remember_me = serializers.BooleanField(default=False, required=False)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass




class SignUpSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, max_length=128)
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=30)
    # tos_agreement = serializers.BooleanField(required=False, default=False)
    invitation_id = serializers.CharField(
        write_only=True, required=False, allow_null=True, allow_blank=True, default=None
    )
    invitation_token = serializers.CharField(
        write_only=True, required=False, allow_null=True, allow_blank=True, default=None
    )

    class Meta:
        model = get_user_model()
        fields = (
            'email', 'password', 'first_name', 'last_name', 'language',
            'invitation_id', 'invitation_token',
        )

    def validate(self, attrs):
        attrs = super().validate(attrs=attrs)
        raw_password = attrs.get('password', None)  # type: str
        email = attrs.get('email', None)  # type: str
        if email and raw_password:
            if email.lower() in raw_password.lower():
                raise ValidationError({
                    'detail': _('Cannot use email in password.')
                })
        return attrs


    # @staticmethod
    # def validate_password(password):
    #     validation_result = enduser_password_validator.validate_password(password)
    #     if not validation_result['password_ok']:
    #         raise ValidationError(detail=enduser_password_validator.get_first_relevant_error(validation_result))
    #     return password

    def validate_email(self, email):
        # validate email using sign up settings
        try:
            existing_record = self.Meta.model.objects.get(email=email)
            if existing_record.unregistered:
                # the record shall just be updated and will need email confirmation
                return email
            raise serializers.ValidationError(_('Email address already in use'))
        except self.Meta.model.DoesNotExist:
            return email

    def create(self, validated_data):

        valid_fields = {}
        for field_name, field_value in validated_data.items():
            if field_name in self.Meta.fields:
                valid_fields[field_name] = field_value
        raw_password = validated_data['password']
        valid_fields['password'] = make_password(validated_data['password'])

        # set language on signup
        language = valid_fields.pop('language', None)
        if not language:
            language = getattr(Settings, 'DEFAULT_USER_LANGUAGE', 'en')
        valid_fields['language'] = language



        existing_user = self.Meta.model.objects.filter(email=valid_fields['email']).first()
        valid_fields.pop('invitation_id')
        valid_fields.pop('invitation_token')
        if existing_user and existing_user.unregistered:
            user = super(SignUpSerializer, self).update(existing_user, valid_fields)
            user.set_password(raw_password)
            user.is_active = True
            user.unregistered = False
            user.save(update_fields=['is_active', 'unregistered'])
        else:
            user = super(SignUpSerializer, self).create(valid_fields)
        db_user = AppUser.objects.get(id=user.id)
        return db_user
