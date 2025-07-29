from rest_framework import serializers
from core.models import CustomUser, Community, Post, Comment, Vote


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user data"""
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'is_bot', 'created_at', 'last_active']
        read_only_fields = ['id', 'created_at', 'last_active']


class CommunitySerializer(serializers.ModelSerializer):
    """Serializer for community data"""
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Community
        fields = [
            'id', 'name', 'display_name', 'description', 
            'created_by', 'created_at', 'member_count', 'post_count'
        ]
        read_only_fields = ['id', 'created_at', 'member_count', 'post_count']


class PostSerializer(serializers.ModelSerializer):
    """Serializer for post data"""
    author = UserSerializer(read_only=True)
    community_name = serializers.CharField(source='community.name', read_only=True)
    
    class Meta:
        model = Post
        fields = [
            'id', 'title', 'content', 'url', 'author', 'community', 
            'community_name', 'upvotes', 'downvotes', 'score', 
            'comment_count', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'author', 'upvotes', 'downvotes', 'score',
            'comment_count', 'created_at', 'updated_at'
        ]


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for comment data"""
    author = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'content', 'author', 'post', 'parent_comment',
            'upvotes', 'downvotes', 'score', 'depth_level',
            'created_at', 'updated_at', 'replies'
        ]
        read_only_fields = [
            'id', 'author', 'upvotes', 'downvotes', 'score',
            'depth_level', 'created_at', 'updated_at'
        ]
    
    def get_replies(self, obj):
        """Get nested replies for a comment"""
        if obj.depth_level < 5:  # Limit nesting depth for API
            replies = obj.replies.filter(is_deleted=False)
            return CommentSerializer(replies, many=True, context=self.context).data
        return []


class VoteSerializer(serializers.ModelSerializer):
    """Serializer for vote data"""
    class Meta:
        model = Vote
        fields = ['vote_type']


class PostCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating posts"""
    community_name = serializers.CharField(write_only=True)
    
    class Meta:
        model = Post
        fields = ['title', 'content', 'url', 'community_name']
    
    def validate_community_name(self, value):
        """Validate that the community exists and is active"""
        try:
            community = Community.objects.get(name=value, is_active=True)
            return community
        except Community.DoesNotExist:
            raise serializers.ValidationError(f"Community '{value}' does not exist or is inactive")
    
    def create(self, validated_data):
        """Create a new post"""
        community = validated_data.pop('community_name')
        validated_data['community'] = community
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class CommentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating comments"""
    class Meta:
        model = Comment
        fields = ['content', 'parent_comment']
    
    def create(self, validated_data):
        """Create a new comment"""
        validated_data['author'] = self.context['request'].user
        validated_data['post'] = self.context['post']
        return super().create(validated_data)
