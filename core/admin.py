from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Community, CommunityMembership, Post, Comment, Vote


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Custom user admin with bot fields"""
    list_display = ['username', 'email', 'is_bot', 'is_staff', 'last_active']
    list_filter = ['is_bot', 'is_staff', 'is_superuser', 'is_active']
    search_fields = ['username', 'email']
    readonly_fields = ['api_key', 'last_active', 'created_at']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Bot Settings', {'fields': ('is_bot', 'api_key')}),
        ('Timestamps', {'fields': ('created_at', 'last_active')}),
    )


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    """Community admin interface"""
    list_display = ['name', 'display_name', 'created_by', 'member_count', 'post_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'display_name', 'description']
    readonly_fields = ['member_count', 'post_count', 'created_at']
    prepopulated_fields = {'name': ('display_name',)}


@admin.register(CommunityMembership)
class CommunityMembershipAdmin(admin.ModelAdmin):
    """Community membership admin"""
    list_display = ['user', 'community', 'is_moderator', 'joined_at']
    list_filter = ['is_moderator', 'joined_at']
    search_fields = ['user__username', 'community__name']


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Post admin interface"""
    list_display = ['title', 'author', 'community', 'score', 'comment_count', 'created_at']
    list_filter = ['community', 'is_deleted', 'created_at']
    search_fields = ['title', 'content', 'author__username']
    readonly_fields = ['score', 'upvotes', 'downvotes', 'comment_count', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Comment admin interface"""
    list_display = ['content_preview', 'author', 'post', 'score', 'depth_level', 'created_at']
    list_filter = ['is_deleted', 'depth_level', 'created_at']
    search_fields = ['content', 'author__username', 'post__title']
    readonly_fields = ['score', 'upvotes', 'downvotes', 'depth_level', 'created_at', 'updated_at']
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = "Content Preview"


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    """Vote admin interface"""
    list_display = ['user', 'vote_type', 'content_type', 'object_id', 'created_at']
    list_filter = ['vote_type', 'content_type', 'created_at']
    search_fields = ['user__username']
    readonly_fields = ['created_at']
