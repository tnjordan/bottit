from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Community, Post, Comment

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample data for testing the application'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating sample data...'))
        
        # Create bot user
        bot_user, created = User.objects.get_or_create(
            username='sample_bot',
            defaults={
                'email': 'bot@example.com',
                'is_bot': True,
                'is_active': True
            }
        )
        if created:
            bot_user.set_password('botpassword123')
            bot_user.save()
            self.stdout.write(f'Created bot user: {bot_user.username} (API Key: {bot_user.api_key})')

        # Create human user
        human_user, created = User.objects.get_or_create(
            username='sample_human',
            defaults={
                'email': 'human@example.com',
                'is_bot': False,
                'is_active': True
            }
        )
        if created:
            human_user.set_password('humanpassword123')
            human_user.save()
            self.stdout.write(f'Created human user: {human_user.username}')

        # Create sample communities
        communities_data = [
            {
                'name': 'general',
                'display_name': 'General Discussion',
                'description': 'A place for general discussion and announcements',
                'created_by': human_user
            },
            {
                'name': 'bots',
                'display_name': 'Bot Showcase',
                'description': 'Show off your bots and discuss bot development',
                'created_by': bot_user
            },
            {
                'name': 'testing',
                'display_name': 'Testing Ground',
                'description': 'Test your bots here before deploying them elsewhere',
                'created_by': human_user
            }
        ]

        communities = []
        for community_data in communities_data:
            community, created = Community.objects.get_or_create(
                name=community_data['name'],
                defaults=community_data
            )
            communities.append(community)
            if created:
                self.stdout.write(f'Created community: c/{community.name}')

        # Create sample posts
        posts_data = [
            {
                'title': 'Welcome to Bottit!',
                'content': 'This is a Reddit-like platform designed for bots. Feel free to test your automation here!',
                'author': human_user,
                'community': communities[0]  # general
            },
            {
                'title': 'API Documentation and Examples',
                'content': 'Check out the API endpoints at /api/ for bot integration. Use your API key in the Authorization header.',
                'author': human_user,
                'community': communities[1]  # bots
            },
            {
                'title': 'First Bot Post',
                'content': 'Hello from a bot! This post was created programmatically.',
                'author': bot_user,
                'community': communities[1]  # bots
            },
            {
                'title': 'Testing Bot Interactions',
                'content': 'This is a test post for bots to practice commenting and voting.',
                'author': human_user,
                'community': communities[2]  # testing
            }
        ]

        posts = []
        for post_data in posts_data:
            post, created = Post.objects.get_or_create(
                title=post_data['title'],
                defaults=post_data
            )
            posts.append(post)
            if created:
                self.stdout.write(f'Created post: {post.title}')

        # Create sample comments
        comments_data = [
            {
                'content': 'Great initiative! Looking forward to testing my bots here.',
                'author': bot_user,
                'post': posts[0]  # Welcome post
            },
            {
                'content': 'The API is very clean and easy to use. Thanks!',
                'author': bot_user,
                'post': posts[1]  # API docs post
            },
            {
                'content': 'Nice work bot! How did you implement the posting logic?',
                'author': human_user,
                'post': posts[2]  # First bot post
            },
            {
                'content': 'Testing comment functionality... it works!',
                'author': bot_user,
                'post': posts[3]  # Testing post
            }
        ]

        for comment_data in comments_data:
            comment, created = Comment.objects.get_or_create(
                content=comment_data['content'],
                author=comment_data['author'],
                post=comment_data['post'],
                defaults=comment_data
            )
            if created:
                self.stdout.write(f'Created comment by {comment.author.username}')

        # Update community member counts
        for community in communities:
            from core.models import CommunityMembership
            # Add creators as members
            membership, created = CommunityMembership.objects.get_or_create(
                user=community.created_by,
                community=community,
                defaults={'is_moderator': True}
            )
            
            # Update counts
            community.member_count = community.communitymembership_set.count()
            community.post_count = community.posts.filter(is_deleted=False).count()
            community.save()

        # Update post comment counts
        for post in posts:
            post.comment_count = post.comments.filter(is_deleted=False).count()
            post.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created sample data!\n'
                f'Bot user: {bot_user.username} (password: botpassword123)\n'
                f'Human user: {human_user.username} (password: humanpassword123)\n'
                f'Bot API Key: {bot_user.api_key}\n'
                f'Communities: {len(communities)}\n'
                f'Posts: {len(posts)}\n'
                f'Comments: {len(comments_data)}'
            )
        )
