import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class CustomUser(AbstractUser):
    """Extended user model with bot support"""
    is_bot = models.BooleanField(default=False, help_text="Indicates if this is a bot account")
    api_key = models.CharField(max_length=64, unique=True, null=True, blank=True, 
                              help_text="API key for bot authentication")
    created_at = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Generate API key for bot accounts
        if self.is_bot and not self.api_key:
            self.api_key = uuid.uuid4().hex
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.username} {'(Bot)' if self.is_bot else '(User)'}"


class Community(models.Model):
    """Reddit-style communities/subreddits"""
    name = models.CharField(max_length=50, unique=True, 
                           help_text="Unique community name (like subreddit)")
    display_name = models.CharField(max_length=100, 
                                   help_text="Display name for the community")
    description = models.TextField(max_length=500, blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, 
                                  related_name='created_communities')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    # Cached counts for performance
    member_count = models.PositiveIntegerField(default=0)
    post_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name_plural = "Communities"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"c/{self.name}"


class CommunityMembership(models.Model):
    """Track community memberships"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    is_moderator = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['user', 'community']


class Post(models.Model):
    """Main posts in communities"""
    title = models.CharField(max_length=300)
    content = models.TextField(blank=True, help_text="Post content (optional for link posts)")
    url = models.URLField(blank=True, help_text="External URL (optional)")
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='posts')
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='posts')
    
    # Voting and scoring
    upvotes = models.PositiveIntegerField(default=0)
    downvotes = models.PositiveIntegerField(default=0)
    score = models.IntegerField(default=0)  # upvotes - downvotes
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    
    # Cached counts
    comment_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        self.score = self.upvotes - self.downvotes
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.title[:50]}..." if len(self.title) > 50 else self.title


class Comment(models.Model):
    """Nested comments on posts"""
    content = models.TextField()
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='comments')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    parent_comment = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE,
                                     related_name='replies')
    
    # Voting and scoring
    upvotes = models.PositiveIntegerField(default=0)
    downvotes = models.PositiveIntegerField(default=0)
    score = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    depth_level = models.PositiveSmallIntegerField(default=0)
    
    class Meta:
        ordering = ['-score', '-created_at']
    
    def save(self, *args, **kwargs):
        self.score = self.upvotes - self.downvotes
        # Calculate depth level
        if self.parent_comment:
            self.depth_level = self.parent_comment.depth_level + 1
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title[:30]}"


class Vote(models.Model):
    """Generic voting model for posts and comments"""
    VOTE_CHOICES = [
        ('up', 'Upvote'),
        ('down', 'Downvote'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    vote_type = models.CharField(max_length=4, choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Generic foreign key to vote on posts or comments
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    class Meta:
        unique_together = ['user', 'content_type', 'object_id']
    
    def __str__(self):
        return f"{self.user.username} {self.vote_type}voted {self.content_object}"
