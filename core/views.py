from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json

from .models import Post, Comment, Community, CustomUser, Vote
from .forms import PostForm, CommentForm, CommunityForm, BotUserCreationForm


def home(request):
    """Homepage with post feed"""
    posts = Post.objects.filter(is_deleted=False).select_related(
        'author', 'community'
    ).order_by('-score', '-created_at')
    
    paginator = Paginator(posts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/home.html', {
        'page_obj': page_obj,
        'posts': page_obj.object_list
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
    posts = community.posts.filter(is_deleted=False).select_related(
        'author'
    ).order_by('-score', '-created_at')
    
    paginator = Paginator(posts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Check if user is a member
    is_member = False
    if request.user.is_authenticated:
        is_member = community.communitymembership_set.filter(user=request.user).exists()
    
    return render(request, 'core/community_detail.html', {
        'community': community,
        'page_obj': page_obj,
        'posts': page_obj.object_list,
        'is_member': is_member
    })


def post_detail(request, post_id):
    """Post detail page with comments"""
    post = get_object_or_404(Post, id=post_id, is_deleted=False)
    
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
    
    # Get all comments in a nested structure
    def get_nested_comments(parent=None, level=0):
        comments = post.comments.filter(
            is_deleted=False, 
            parent_comment=parent
        ).select_related('author').order_by('-score', 'created_at')
        
        result = []
        for comment in comments:
            comment.level = level
            result.append(comment)
            result.extend(get_nested_comments(comment, level + 1))
        
        return result
    
    comments = get_nested_comments()
    
    return render(request, 'core/post_detail.html', {
        'post': post,
        'comments': comments
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
