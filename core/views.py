from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
import json

from .models import Post, Comment, Community, CustomUser, Vote
from .forms import PostForm, CommentForm, CommunityForm, BotUserCreationForm


def get_date_filter(date_filter):
    """Get date filter for posts based on time period"""
    now = timezone.now()
    if date_filter == 'hour':
        return now - timedelta(hours=1)
    elif date_filter == 'day':
        return now - timedelta(days=1)
    elif date_filter == 'week':
        return now - timedelta(weeks=1)
    else:  # 'all' or any other value
        return None


def apply_post_filters(posts_queryset, sort_by='new', date_filter='all'):
    """Apply sorting and date filtering to posts queryset"""
    # Apply date filter
    date_threshold = get_date_filter(date_filter)
    if date_threshold:
        posts_queryset = posts_queryset.filter(created_at__gte=date_threshold)
    
    # Apply sorting
    if sort_by == 'new':
        posts_queryset = posts_queryset.order_by('-created_at')
    elif sort_by == 'top':
        posts_queryset = posts_queryset.order_by('-score', '-created_at')
    else:  # default to new
        posts_queryset = posts_queryset.order_by('-created_at')
    
    return posts_queryset


def get_user_votes(user, objects):
    """Get user's votes for a list of objects"""
    if not user.is_authenticated:
        return {}
    
    from django.contrib.contenttypes.models import ContentType
    
    # Group objects by type
    votes_dict = {}
    by_type = {}
    
    for obj in objects:
        ct = ContentType.objects.get_for_model(obj)
        key = f"{ct.app_label}.{ct.model}"
        if key not in by_type:
            by_type[key] = {'ct': ct, 'ids': []}
        by_type[key]['ids'].append(obj.id)
    
    # Get votes for each type
    for type_key, data in by_type.items():
        ct = data['ct']
        ids = data['ids']
        
        votes = Vote.objects.filter(
            user=user,
            content_type=ct,
            object_id__in=ids
        ).values('object_id', 'vote_type')
        
        for vote in votes:
            votes_dict[f"{type_key}_{vote['object_id']}"] = vote['vote_type']
    
    return votes_dict


def home(request):
    """Homepage with post feed"""
    # Get filter parameters
    sort_by = request.GET.get('sort', 'new')  # default to 'new' instead of 'hot'
    date_filter = request.GET.get('time', 'all')
    
    posts = Post.objects.filter(is_deleted=False).select_related(
        'author', 'community'
    )
    
    # Apply filters
    posts = apply_post_filters(posts, sort_by, date_filter)
    
    paginator = Paginator(posts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get user votes for the posts
    user_votes = get_user_votes(request.user, page_obj.object_list)
    
    return render(request, 'core/home.html', {
        'page_obj': page_obj,
        'posts': page_obj.object_list,
        'user_votes': user_votes,
        'current_sort': sort_by,
        'current_time_filter': date_filter
    })


def community_list(request):
    """List all communities"""
    communities = Community.objects.filter(is_active=True).order_by('-member_count')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        communities = communities.filter(
            Q(name__icontains=search_query) | 
            Q(display_name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    paginator = Paginator(communities, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/community_list.html', {
        'page_obj': page_obj,
        'communities': page_obj.object_list,
        'search_query': search_query
    })


def community_detail(request, community_name):
    """Community detail page with posts"""
    community = get_object_or_404(Community, name=community_name, is_active=True)
    
    # Get filter parameters
    sort_by = request.GET.get('sort', 'new')  # default to 'new' instead of 'hot'
    date_filter = request.GET.get('time', 'all')
    
    posts = community.posts.filter(is_deleted=False).select_related(
        'author'
    )
    
    # Apply filters
    posts = apply_post_filters(posts, sort_by, date_filter)
    
    paginator = Paginator(posts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Check if user is a member
    is_member = False
    if request.user.is_authenticated:
        is_member = community.communitymembership_set.filter(user=request.user).exists()
    
    # Get user votes for the posts
    user_votes = get_user_votes(request.user, page_obj.object_list)
    
    return render(request, 'core/community_detail.html', {
        'community': community,
        'page_obj': page_obj,
        'posts': page_obj.object_list,
        'is_member': is_member,
        'user_votes': user_votes,
        'current_sort': sort_by,
        'current_time_filter': date_filter
    })


def post_detail(request, post_id):
    """Post detail page with comments"""
    post = get_object_or_404(Post, id=post_id, is_deleted=False)
    
    # Get comment sorting parameter
    comment_sort = request.GET.get('comment_sort', 'top')  # default to 'top'
    
    # Handle comment creation
    if request.method == 'POST' and request.user.is_authenticated:
        content = request.POST.get('content')
        parent_id = request.POST.get('parent_id')
        
        if content:
            comment = Comment(
                post=post,
                author=request.user,
                content=content.strip()
            )
            
            if parent_id:
                parent_comment = get_object_or_404(Comment, id=parent_id)
                comment.parent_comment = parent_comment
            
            comment.save()
            
            # Update post comment count
            post.comment_count = F('comment_count') + 1
            post.save(update_fields=['comment_count'])
            
            messages.success(request, 'Comment added successfully!')
            return redirect('post_detail', post_id=post.id)
    
    # Get all comments in a nested structure with sorting
    def get_nested_comments(parent=None, level=0):
        comments_query = post.comments.filter(
            is_deleted=False, 
            parent_comment=parent
        ).select_related('author')
        
        # Apply sorting
        if comment_sort == 'new':
            comments_query = comments_query.order_by('-created_at')
        else:  # 'top' or default
            comments_query = comments_query.order_by('-score', '-created_at')
        
        result = []
        for comment in comments_query:
            comment.level = level
            result.append(comment)
            result.extend(get_nested_comments(comment, level + 1))
        
        return result
    
    comments = get_nested_comments()
    
    # Get user votes for the post and comments
    all_objects = [post] + comments
    user_votes = get_user_votes(request.user, all_objects)
    
    return render(request, 'core/post_detail.html', {
        'post': post,
        'comments': comments,
        'user_votes': user_votes,
        'current_comment_sort': comment_sort
    })


@login_required
def create_post(request):
    """Create a new post"""
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            
            # Update community post count
            post.community.post_count = F('post_count') + 1
            post.community.save(update_fields=['post_count'])
            
            messages.success(request, 'Post created successfully!')
            return redirect('post_detail', post_id=post.id)
    else:
        form = PostForm()
    
    return render(request, 'core/create_post.html', {'form': form})


@login_required
def create_community(request):
    """Create a new community"""
    if request.method == 'POST':
        form = CommunityForm(request.POST)
        if form.is_valid():
            community = form.save(commit=False)
            community.created_by = request.user
            community.save()
            
            # Auto-join creator as member and moderator
            from .models import CommunityMembership
            CommunityMembership.objects.create(
                user=request.user,
                community=community,
                is_moderator=True
            )
            
            messages.success(request, f'Community c/{community.name} created successfully!')
            return redirect('community_detail', community_name=community.name)
    else:
        form = CommunityForm()
    
    return render(request, 'core/create_community.html', {'form': form})


@login_required
@require_POST
def add_comment(request, post_id):
    """Add a comment to a post"""
    post = get_object_or_404(Post, id=post_id)
    parent_id = request.POST.get('parent_id')
    content = request.POST.get('content')
    
    if not content.strip():
        messages.error(request, 'Comment cannot be empty')
        return redirect('post_detail', post_id=post_id)
    
    comment = Comment.objects.create(
        content=content,
        author=request.user,
        post=post,
        parent_comment_id=parent_id if parent_id else None
    )
    
    # Update post comment count
    post.comment_count = F('comment_count') + 1
    post.save(update_fields=['comment_count'])
    
    messages.success(request, 'Comment added successfully!')
    return redirect('post_detail', post_id=post_id)


@login_required
@require_POST
def vote(request, content_type, object_id):
    """Handle voting on posts and comments"""
    from django.contrib.contenttypes.models import ContentType
    
    vote_type = request.POST.get('vote_type')  # 'up' or 'down'
    
    if vote_type not in ['up', 'down']:
        return JsonResponse({'error': 'Invalid vote type'}, status=400)
    
    # Get the content type and object
    try:
        ct = ContentType.objects.get(model=content_type)
        obj = ct.get_object_for_this_type(id=object_id)
    except (ContentType.DoesNotExist, ct.model_class().DoesNotExist):
        return JsonResponse({'error': 'Object not found'}, status=404)
    
    # Get or create vote
    vote_obj, created = Vote.objects.get_or_create(
        user=request.user,
        content_type=ct,
        object_id=object_id,
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
    _update_vote_counts(obj)
    
    return JsonResponse({
        'success': True,
        'vote_type': vote_type,
        'score': obj.score,
        'upvotes': obj.upvotes,
        'downvotes': obj.downvotes
    })


def _update_vote_counts(obj):
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


def register(request):
    """User registration with bot option"""
    if request.method == 'POST':
        form = BotUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            
            if user.is_bot:
                messages.success(request, f'Bot account created! Your API key is: {user.api_key}')
            else:
                messages.success(request, 'Account created successfully!')
            
            return redirect('home')
    else:
        form = BotUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})
