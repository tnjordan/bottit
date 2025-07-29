from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Post, Comment, Community


class BotUserCreationForm(UserCreationForm):
    """Custom user creation form with bot option"""
    is_bot = forms.BooleanField(
        required=False,
        help_text="Check this if you're creating a bot account"
    )
    
    class Meta:
        model = CustomUser
        fields = ("username", "email", "is_bot", "password1", "password2")
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_bot = self.cleaned_data["is_bot"]
        if commit:
            user.save()
        return user


class PostForm(forms.ModelForm):
    """Form for creating and editing posts"""
    
    class Meta:
        model = Post
        fields = ['title', 'content', 'url', 'community']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter post title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Enter post content (optional)'
            }),
            'url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter URL (optional)'
            }),
            'community': forms.Select(attrs={
                'class': 'form-control'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['community'].queryset = Community.objects.filter(is_active=True)


class CommentForm(forms.ModelForm):
    """Form for creating and editing comments"""
    
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Write your comment...'
            })
        }


class CommunityForm(forms.ModelForm):
    """Form for creating and editing communities"""
    
    class Meta:
        model = Community
        fields = ['name', 'display_name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'community_name'
            }),
            'display_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Community Display Name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe what this community is about...'
            })
        }
