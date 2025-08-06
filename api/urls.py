from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, admin_views

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'communities', views.CommunityViewSet)
router.register(r'posts', views.PostViewSet)
router.register(r'comments', views.CommentViewSet)
router.register(r'users', views.UserViewSet)

urlpatterns = [
    # Router URLs (includes all CRUD operations and custom actions)
    path('', include(router.urls)),
    
    # Admin endpoints
    path('admin/create-bot-user/', admin_views.create_bot_user, name='create-bot-user'),
]
