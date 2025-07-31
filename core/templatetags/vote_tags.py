from django import template
from django.contrib.contenttypes.models import ContentType

register = template.Library()


@register.filter
def get_user_vote(user_votes, obj):
    """Get user's vote for an object"""
    if not user_votes:
        return None
    
    ct = ContentType.objects.get_for_model(obj)
    key = f"{ct.app_label}.{ct.model}_{obj.id}"
    return user_votes.get(key)


@register.filter
def has_voted_up(user_votes, obj):
    """Check if user has upvoted the object"""
    vote = get_user_vote(user_votes, obj)
    return vote == 'up'


@register.filter
def has_voted_down(user_votes, obj):
    """Check if user has downvoted the object"""
    vote = get_user_vote(user_votes, obj)
    return vote == 'down'
