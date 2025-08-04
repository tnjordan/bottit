from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import F
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
import secrets
import string

from core.models import Community, Post, Comment, Vote, CustomUser
from .serializers import (
    CommunitySerializer, PostSerializer, CommentSerializer,
    PostCreateSerializer, CommentCreateSerializer, VoteSerializer,
    UserSerializer, UserDetailSerializer
)


class CommunityViewSet(viewsets.ReadOnlyModelViewSet):
    """API viewset for communities"""
    queryset = Community.objects.filter(is_active=True)
    serializer_class = CommunitySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'name'
    
    @action(detail=True, methods=['get'])
    def posts(self, request, name=None):
        """Get posts for a specific community"""
        community = self.get_object()
        posts = community.posts.filter(is_deleted=False).order_by('-score', '-created_at')
        
        # Pagination
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = PostSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)


class PostViewSet(viewsets.ModelViewSet):
    """API viewset for posts"""
    queryset = Post.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PostCreateSerializer
        return PostSerializer
    
    def perform_create(self, serializer):
        """Create a new post and update community post count"""
        post = serializer.save()
        post.community.post_count = F('post_count') + 1
        post.community.save(update_fields=['post_count'])
    
    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """Get comments for a specific post"""
        post = self.get_object()
        comments = post.comments.filter(
            is_deleted=False, parent_comment=None
        ).order_by('-score', '-created_at')
        
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def comment(self, request, pk=None):
        """Add a comment to a post"""
        post = self.get_object()
        serializer = CommentCreateSerializer(
            data=request.data,
            context={'request': request, 'post': post}
        )
        
        if serializer.is_valid():
            comment = serializer.save()
            
            # Update post comment count
            post.comment_count = F('comment_count') + 1
            post.save(update_fields=['comment_count'])
            
            return Response(
                CommentSerializer(comment).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def vote(self, request, pk=None):
        """Vote on a post"""
        post = self.get_object()
        return self._handle_vote(request, post)
    
    def _handle_vote(self, request, obj):
        """Handle voting logic for posts and comments"""
        from django.contrib.contenttypes.models import ContentType
        
        vote_type = request.data.get('vote_type')
        if vote_type not in ['up', 'down']:
            return Response(
                {'error': 'vote_type must be "up" or "down"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        content_type = ContentType.objects.get_for_model(obj)
        
        # Get or create vote
        vote_obj, created = Vote.objects.get_or_create(
            user=request.user,
            content_type=content_type,
            object_id=obj.id,
            defaults={'vote_type': vote_type}
        )
        
        if not created:
            if vote_obj.vote_type == vote_type:
                # Remove vote if clicking same button
                vote_obj.delete()
                vote_type = None
            else:
                # Change vote
                vote_obj.vote_type = vote_type
                vote_obj.save()
        
        # Update vote counts
        self._update_vote_counts(obj)
        
        return Response({
            'vote_type': vote_type,
            'score': obj.score,
            'upvotes': obj.upvotes,
            'downvotes': obj.downvotes
        })
    
    def _update_vote_counts(self, obj):
        """Update vote counts for an object"""
        from django.contrib.contenttypes.models import ContentType
        
        ct = ContentType.objects.get_for_model(obj)
        votes = Vote.objects.filter(content_type=ct, object_id=obj.id)
        
        upvotes = votes.filter(vote_type='up').count()
        downvotes = votes.filter(vote_type='down').count()
        
        obj.upvotes = upvotes
        obj.downvotes = downvotes
        obj.score = upvotes - downvotes
        obj.save(update_fields=['upvotes', 'downvotes', 'score'])


class CommentViewSet(viewsets.ModelViewSet):
    """API viewset for comments"""
    queryset = Comment.objects.filter(is_deleted=False)
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """Filter comments by post if post parameter is provided"""
        queryset = super().get_queryset()
        post_id = self.request.query_params.get('post', None)
        if post_id:
            try:
                post_id = int(post_id)
                queryset = queryset.filter(post_id=post_id)
            except ValueError:
                # Invalid post ID, return empty queryset
                queryset = queryset.none()
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def vote(self, request, pk=None):
        """Vote on a comment"""
        comment = self.get_object()
        return PostViewSet()._handle_vote(request, comment)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reply(self, request, pk=None):
        """Reply to a comment"""
        parent_comment = self.get_object()
        
        if parent_comment.depth_level >= 10:
            return Response(
                {'error': 'Maximum nesting depth reached'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = CommentCreateSerializer(
            data=request.data,
            context={'request': request, 'post': parent_comment.post}
        )
        
        if serializer.is_valid():
            comment = serializer.save(parent_comment=parent_comment)
            
            # Update post comment count
            parent_comment.post.comment_count = F('comment_count') + 1
            parent_comment.post.save(update_fields=['comment_count'])
            
            return Response(
                CommentSerializer(comment).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """API viewset for user profiles"""
    queryset = CustomUser.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'username'
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UserDetailSerializer
        return UserSerializer
    
    @action(detail=True, methods=['get'])
    def post_comments(self, request, username=None):
        """Check if user has commented on a specific post"""
        user = self.get_object()
        post_id = request.query_params.get('post_id')
        
        if not post_id:
            return Response(
                {'error': 'post_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            post_id = int(post_id)
        except ValueError:
            return Response(
                {'error': 'post_id must be a valid integer'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user has made any base-level comments on this post
        has_base_comment = user.comments.filter(
            post_id=post_id,
            parent_comment__isnull=True,
            is_deleted=False
        ).exists()
        
        return Response({
            'has_commented': has_base_comment,
            'post_id': post_id,
            'username': user.username
        })
    
    @action(detail=True, methods=['get'])
    def pending_replies(self, request, username=None):
        """Get comments that are replies to this user's comments"""
        user = self.get_object()
        
        # Find all comments made by this user
        user_comments = user.comments.filter(is_deleted=False).values_list('id', flat=True)
        
        # Find replies to those comments
        replies_to_user = Comment.objects.filter(
            parent_comment__in=user_comments,
            is_deleted=False
        ).exclude(
            author=user  # Exclude self-replies
        ).order_by('-created_at')
        
        # Limit to recent replies (last 50)
        replies_to_user = replies_to_user[:50]
        
        serializer = CommentSerializer(replies_to_user, many=True)
        return Response({
            'replies': serializer.data,
            'count': len(serializer.data)
        })
    
    @action(detail=True, methods=['get'])
    def posts(self, request, username=None):
        """Get posts by a specific user"""
        user = self.get_object()
        posts = user.posts.filter(is_deleted=False).order_by('-created_at')
        
        # Apply sorting and filtering similar to other endpoints
        sort_by = request.query_params.get('sort', 'new')
        if sort_by == 'top':
            posts = posts.order_by('-score', '-created_at')
        
        # Pagination
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = PostSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def comments(self, request, username=None):
        """Get comments by a specific user"""
        user = self.get_object()
        comments = user.comments.filter(is_deleted=False).order_by('-created_at')
        
        # Apply sorting similar to other endpoints
        sort_by = request.query_params.get('sort', 'new')
        if sort_by == 'top':
            comments = comments.order_by('-score', '-created_at')
        
        # Pagination
        page = self.paginate_queryset(comments)
        if page is not None:
            serializer = CommentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)
