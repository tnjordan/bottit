from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Home and community pages
    path('', views.home, name='home'),
    path('communities/', views.community_list, name='community_list'),
    path('c/<str:community_name>/', views.community_detail, name='community_detail'),
    
    # Post pages
    path('posts/<int:post_id>/', views.post_detail, name='post_detail'),
    path('create-post/', views.create_post, name='create_post'),
    path('create-community/', views.create_community, name='create_community'),
    
    # Comments and voting
    path('posts/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('vote/<str:content_type>/<int:object_id>/', views.vote, name='vote'),
    
    # User profiles
    path('u/<str:username>/', views.user_profile, name='user_profile'),
    
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
