from services.views import ServicesViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'services', ServicesViewSet, basename='user')
urlpatterns = router.urls
