from django.db import transaction


from rest_framework import viewsets
from rest_framework.response import Serializer
from core.exceptions import APIBadRequest
from core.models.models import Client
from core.permissions import CustomPermissions, EndUserOnly
from core.serializers import ClientSerializer


class ClientViewSet(viewsets.ModelViewSet):
    serializer_class = ClientSerializer
    model = Client
    permission_classes = (CustomPermissions, EndUserOnly,)
    # filter_backends = (filters.OrderingFilter, DjangoFilterBackend, CustomFilter, FleioSearchFilter)
    # ordering_fields = ('id', 'company', 'country', 'city', 'state')/
    search_fields = ('id', 'company',)

    serializer_map = {
        # 'retrieve': ClientSerializer,
        'create': ClientSerializer,
        # 'update': ClientUpdateSerializer,
        # 'send_invitation': InviteUserSerializer,
        # 'dissociate_user': DissociateUserSerializer,
        # 'get_user_notifications_settings': GetNotificationsSettingsSerializer,
    }

    def get_serializer_class(self):
        return self.serializer_map.get(self.action, self.serializer_class)

    def get_queryset(self):
        return self.request.user.managed_clients.all()

    # def get_throttles(self):
    #     if self.action == 'send_invitation':
    #         return [SendClientInvitationThrottle(), ]
    #     return super().get_throttles()

    # @action(detail=False, methods=['get'], permission_classes=(AllowAny,))
    # def create_options(self, request, *args, **kwargs):
    #     del request, args, kwargs  # unused
    #     return Response({'countries': get_countries(),
    #                      'custom_fields': ClientCustomFieldDefinition().definition,
    #                      'currencies': [currency.code for currency in Currency.objects.all()]
    #                      })

    # @action(detail=True, methods=['get'])
    # def can_dissociate_as_owner(self, request, pk):
    #     client = self.get_object()
    #     for u2c in UserToClient.objects.filter(client=client).exclude(user=request.user).exclude(invitation=True):
    #         if u2c.roles.filter(id=Role.objects.get_owner_role().id).count():
    #             # other users with owner roles exist, we can dissociate
    #             return Response({'can_dissociate': True})
    #     return Response({'can_dissociate': False})

    # @staticmethod
    # def user_is_owner(user, client):
    #     user_to_client = UserToClient.objects.filter(user=user, client=client).first()
    #     return user_to_client and user_to_client.roles.filter(id=Role.objects.get_owner_role().id).first()

    # @action(detail=True, methods=['get'])
    # def get_users(self, request, pk):
    #     client = self.get_object()
    #     user = request.user
    #     if ClientViewSet.user_is_owner(user=user, client=client):
    #         u2c = UserToClient.objects.filter(client=client)
    #         return Response({
    #             'users': UserToClientMinSerializer(
    #                 instance=u2c,
    #                 context={'limit_info_for_invitations': True},
    #                 many=True
    #             ).data})
    #     else:
    #         return Response({'users': []})

    # @action(detail=True, methods=['post'])
    # def dissociate_user(self, request, pk):
    #     del pk  # unused
    #     client = self.get_object()
    #     request_user = request.user
    #     if not ClientViewSet.user_is_owner(user=request_user, client=client):
    #         raise APIBadRequest(_('Only owners can dissociate users.'))

    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     try:
    #         user_to_client = UserToClient.objects.get(
    #             id=serializer.validated_data['relation_id'],
    #             client=client,
    #         )
    #     except UserToClient.DoesNotExist:
    #         raise ObjectNotFound({'detail': _('User not found')})
    #     else:
    #         related_user = user_to_client.user
    #         if request_user.pk == related_user.pk:
    #             # owner is dissociating himself, check if there are other owners
    #             has_more_owners = False
    #             for u2c in UserToClient.objects.filter(
    #                     client=client
    #             ).exclude(user=related_user).exclude(invitation=True):
    #                 if u2c.roles.filter(id=Role.objects.get_owner_role().id).count():
    #                     has_more_owners = True
    #             if not has_more_owners:
    #                 raise APIBadRequest(_('Cannot dissociate as the last owner.'))

    #         with transaction.atomic():
    #             # delete the cart related to client
    #             client.carts.filter(user=related_user).delete()
    #             activity_helper.add_current_activity_params(dissociated_user_id=related_user.id)
    #             activity_helper.add_log_to_entity(
    #                 entity_type=LogEntityTypes.user,
    #                 object_id=related_user.id,
    #             )
    #             user_to_client.delete()
    #             if related_user.unregistered:
    #                 related_user.delete()
    #     return Response({'detail': _('User dissociated')})

    # @action(detail=True, methods=['post'])
    # def send_invitation(self, request, pk):
    #     if not active_features.is_enabled('clients&users.invitations'):
    #         raise NotFound()
    #     client = self.get_object()
    #     activity_helper.add_current_activity_params(client_name=client.name)
    #     user = request.user
    #     if not ClientViewSet.user_is_owner(user=user, client=client):
    #         raise APIBadRequest(_('Only owners can send invitations.'))
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     activity_helper.add_current_activity_params(email=serializer.validated_data['user_email'])
    #     user_model = get_user_model()
    #     if active_features.is_enabled('clients&users.roles') and len(serializer.validated_data['roles']) == 0:
    #         raise APIBadRequest(_('You must select at least one role.'))
    #     with transaction.atomic():
    #         try:
    #             invited_user = user_model.objects.get(email=serializer.validated_data['user_email'])
    #         except user_model.DoesNotExist:
    #             invited_user = user_model.create_invited_user(email=serializer.validated_data['user_email'])
    #         try:
    #             u2c = UserToClient.objects.create(
    #                 user=invited_user, client=client, invitation=True,
    #             )
    #         except IntegrityError:
    #             raise APIBadRequest(_('User was already invited.'))
    #         u2c.roles.set(Role.objects.filter(id__in=serializer.validated_data['roles']).all())
    #         # set notifications settings
    #         notifications_settings = serializer.validated_data.get('notifications_settings', [])
    #         user_notifications_settings = user.notifications_settings.filter(
    #             client=client
    #         ).first()  # type: UserNotificationsSettings
    #         if not user_notifications_settings:
    #             user_notifications_settings, created = UserNotificationsSettings.objects.get_or_create(
    #                 user=invited_user, client=client
    #             )
    #         for notification_setting in notifications_settings:
    #             if notification_setting['target_category'] in TargetCategory.editable:
    #                 user_notifications_settings.set_notification_enabled_flag(
    #                     notification_setting['target_category'],
    #                     notification_setting['enabled'],
    #                 )
    #     notifier.send(
    #         name='account.user.invitation',
    #         client=client,
    #         user=invited_user,
    #         priority=notifier.Notification.PRIORITY_NORMAL,
    #         variables={
    #             'full_name': user.get_full_name(),
    #             'client_name': client.name,
    #             'invitation_id': u2c.id,
    #             'frontend_url': fleio_parse_url(settings.FRONTEND_URL),
    #             'token': invitation_token_generator.make_token(user_to_client=u2c)
    #         },
    #     )
    #     return Response({'detail': _('Invitation sent.')})

    # @action(detail=True, methods=['get'])
    # def get_user_notifications_settings(self, request, pk):
    #     client = self.get_object()
    #     request_user = request.user

    #     serializer = GetNotificationsSettingsSerializer(data=request.query_params)
    #     if serializer.is_valid(raise_exception=True):
    #         user_id = serializer.validated_data.get('user_id')
    #         if not user_id:
    #             raise APIBadRequest(_('User ID to get notifications for was not provided.'))

    #         if not ClientViewSet.user_is_owner(user=request_user, client=client) and request_user.id != user_id:
    #             # non-owner cannot get notification settings of another user
    #             raise ForbiddenException(_('Only owners can get notifications settings.'))

    #         preview = serializer.validated_data.get('preview')
    #         user_client_relation = UserToClient.objects.filter(user_id=user_id, client=client).first()
    #         if not user_client_relation:
    #             raise ObjectNotFound(_('Could not find related user.'))

    #         response_data = {}
    #         for target_category in TargetCategory.all if preview else TargetCategory.editable:
    #             response_data[target_category] = {
    #                 'name': target_category,
    #                 'display_name': TargetCategory.display[target_category],
    #                 'enabled': user_client_relation.user.has_notification_enabled(
    #                     template_target_category=target_category,
    #                     client=client,
    #                 ),
    #             }
    #         return Response({
    #             'detail': response_data,
    #         })

    # @action(detail=True, methods=['POST'])
    # def set_user_notifications_settings(self, request, pk):
    #     client = self.get_object()
    #     request_user = request.user
    #     if not ClientViewSet.user_is_owner(user=request_user, client=client):
    #         raise ForbiddenException(_('Only owners can set notifications settings.'))

    #     user_id_to_change = request.data.get('user_id')
    #     user_client_relation = UserToClient.objects.filter(user_id=user_id_to_change, client=client).first()
    #     activity_helper.add_current_activity_params(updated_user_id=user_client_relation.user.id)
    #     activity_helper.add_log_to_entity(
    #         entity_type=LogEntityTypes.user,
    #         object_id=user_client_relation.user.id,
    #     )
    #     if not user_client_relation:
    #         raise ObjectNotFound(_('Could not find related user.'))

    #     with transaction.atomic():
    #         notifications_settings = user_client_relation.user.notifications_settings.filter(client=client).first()
    #         if not notifications_settings:
    #             notifications_settings, created = UserNotificationsSettings.objects.get_or_create(
    #                 user=user_client_relation.user, client=client
    #             )

    #         for target_category, data in request.data['settings'].items():
    #             if target_category in TargetCategory.editable:
    #                 notifications_settings.set_notification_enabled_flag(target_category, data['enabled'])
    #         return Response()

    # @action(detail=True, methods=['get'])
    # def get_available_roles(self, request, pk):
    #     client = self.get_object()
    #     user = request.user

    #     if not ClientViewSet.user_is_owner(user=user, client=client):
    #         raise APIBadRequest(_('Only owners can get available roles for client.'))

    #     roles = Role.objects.filter(Q(public=True) | Q(owner=client)).all()
    #     default_role = Role.objects.get_owner_role()
    #     return Response({
    #         'roles': RoleMinSerializer(instance=roles, many=True).data,
    #         'default_role_id': default_role.id if default_role else None,
    #     })

    # @action(detail=True, methods=['post'])
    # def update_roles(self, request, pk):
    #     del pk  # unused
    #     client = self.get_object()

    #     if not ClientViewSet.user_is_owner(user=request.user, client=client):
    #         raise APIBadRequest(_('Only owners can edit other users roles.'))

    #     serializer = UserUpdateRoleSerializer(data=request.data)
    #     if serializer.is_valid(raise_exception=True):
    #         u2c = UserToClient.objects.filter(client=client, user__id=serializer.validated_data['user_id']).first()
    #         if not u2c:
    #             raise APIBadRequest(_('Specified user is not assigned to client'))
    #         with transaction.atomic():
    #             activity_helper.add_current_activity_params(updated_user_id=u2c.user.id)
    #             activity_helper.add_log_to_entity(
    #                 entity_type=LogEntityTypes.user,
    #                 object_id=u2c.user.id,
    #             )
    #             u2c.roles.clear()
    #             for role_id in serializer.validated_data['roles']:
    #                 u2c.roles.add(Role.objects.get(id=role_id))
    #             u2c.save()

    #     return Response()

    # @action(detail=True, methods=['post'])
    # def dissociate_from_client(self, request, pk):
    #     del pk  # unused

    #     client = self.get_object()
    #     user = request.user
    #     user_to_client = UserToClient.objects.filter(user=user, client=client).first()

    #     user_is_owner = False
    #     for role in user_to_client.roles.all():
    #         if role.id == Role.objects.get_owner_role().id:
    #             user_is_owner = True

    #     has_more_owners = False
    #     for u2c in UserToClient.objects.filter(client=client).exclude(user=user).exclude(invitation=True):
    #         if u2c.roles.filter(id=Role.objects.get_owner_role().id).count():
    #             has_more_owners = True

    #     if user_is_owner and not has_more_owners:
    #         raise APIBadRequest(_('Cannot dissociate as the last owner.'))
    #     with transaction.atomic():
    #         # delete the cart related to user
    #         user.carts.filter(client=client).delete()
    #         UserToClient.objects.filter(user=user, client=client).delete()
    #     return Response({'detail': _('User dissociated')})

    # def perform_create(self, serializer):
    #     try:
    #         with transaction.atomic():
    #             client = serializer.save()
    #             # add_initial_credit(client=client)
    #             client.usertoclient_set.create(user=self.request.user)
    #             # order_metadata = OrderMetadata.from_request(request=self.request)
    #             # client_created.send(
    #             #     sender=self.__class__,
    #             #     client=client,
    #             #     create_auto_order_service=True,  # always create_auto_order_service when end-user adds client
    #             #     request_user=self.request.user.id,
    #             #     order_metadata=order_metadata.to_json(),
    #             # )
    #     except Exception as e:
    #         # LOG.exception(e)
    #         raise APIBadRequest()


    # def destroy(self, request, *args, **kwargs):
    #     """Does not allow a user to delete his own client"""
    #     raise MethodNotAllowed(_('Client delete prohibited'))
