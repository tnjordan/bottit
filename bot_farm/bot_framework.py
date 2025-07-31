#!/usr/bin/env python3
"""
Bot Framework - Core bot implementation with personality-driven behavior
"""

import google.generativeai as genai
import requests
import random
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

from .personalities import BotPersonality, BotPersonalityType


@dataclass
class BotAction:
    """Represents an action a bot wants to take"""
    action_type: str  # 'create_post', 'comment', 'vote', 'reply'
    target_id: Optional[int] = None  # post_id or comment_id
    content: Optional[str] = None
    vote_type: Optional[str] = None  # 'up' or 'down'
    community_name: Optional[str] = None
    title: Optional[str] = None  # for posts


class BotFramework:
    """Core bot framework that implements personality-driven behavior"""
    
    def __init__(self, bot_id: str, personality: BotPersonality, api_key: str, base_url: str):
        self.bot_id = bot_id
        self.personality = personality
        self.api_key = api_key
        self.base_url = base_url
        self.last_action_time = None
        self.action_history = []
        
    def get_headers(self) -> Dict[str, str]:
        """Get API headers for requests"""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def should_take_action(self) -> bool:
        """Determine if bot should take any action based on activity level and timing"""
        if self.last_action_time is None:
            return True
            
        # Calculate time since last action
        time_since_last = datetime.now() - self.last_action_time
        
        # Base cooldown modified by activity level
        base_cooldown = 1  # 5 minutes
        cooldown = base_cooldown / self.personality.activity_level
        
        if time_since_last.total_seconds() < cooldown:
            return False
            
        # Random factor based on activity level
        return random.random() < self.personality.activity_level
    
    def decide_action(self, available_posts: List[Dict], available_comments: List[Dict]) -> Optional[BotAction]:
        """Decide what action to take based on personality and available content, favoring interaction with latest post"""
        if not self.should_take_action():
            return None
            
        probabilities = self.personality.action_probabilities
        actions = []
        
        # If there's a latest post available, heavily favor interacting with it
        if available_posts:
            # Boost interaction probabilities for the latest post
            actions.extend(['vote_post'] * int(probabilities.vote_on_post * 150))  # 1.5x more likely
            actions.extend(['comment_post'] * int(probabilities.comment_on_post * 200))  # 2x more likely
            
            # If there are comments on the latest post, encourage replies
            if available_comments:
                actions.extend(['vote_comment'] * int(probabilities.vote_on_comment * 150))  # 1.5x more likely
                actions.extend(['reply_comment'] * int(probabilities.reply_to_comment * 200))  # 2x more likely
            
            # Reduce create_post probability when there's an active latest post
            actions.extend(['create_post'] * int(probabilities.create_post * 30))  # Much less likely
        else:
            # No recent post available, heavily favor creating new content
            actions.extend(['create_post'] * int(probabilities.create_post * 300))  # 3x more likely
        
        if not actions:
            return None
            
        chosen_action = random.choice(actions)
        
        if chosen_action == 'create_post':
            return BotAction(
                action_type='create_post',
                community_name=self._choose_community()
            )
        elif chosen_action == 'vote_post' and available_posts:
            post = self._choose_post(available_posts)
            return BotAction(
                action_type='vote_post',
                target_id=post['id'],
                vote_type=self._decide_vote_type()
            )
        elif chosen_action == 'comment_post' and available_posts:
            post = self._choose_post(available_posts)
            return BotAction(
                action_type='comment_post',
                target_id=post['id']
            )
        elif chosen_action == 'vote_comment' and available_comments:
            comment = random.choice(available_comments)
            return BotAction(
                action_type='vote_comment',
                target_id=comment['id'],
                vote_type=self._decide_vote_type()
            )
        elif chosen_action == 'reply_comment' and available_comments:
            comment = random.choice(available_comments)
            return BotAction(
                action_type='reply_comment',
                target_id=comment['id']
            )
        
        return None
    
    def _choose_community(self) -> str:
        """Choose a community based on preferences"""
        if self.personality.preferred_communities:
            return random.choice(self.personality.preferred_communities)
        return "general"
    
    def _choose_post(self, posts: List[Dict]) -> Dict:
        """Choose a post to interact with based on personality"""
        # Filter by community preferences
        filtered_posts = []
        for post in posts:
            # Handle both string community_name and dict community formats
            if 'community_name' in post:
                community = post['community_name']
            elif 'community' in post and isinstance(post['community'], dict):
                community = post['community'].get('name', 'general')
            else:
                community = 'general'
                
            if (community in self.personality.preferred_communities or 
                not self.personality.preferred_communities):
                if community not in self.personality.avoid_communities:
                    filtered_posts.append(post)
        
        if not filtered_posts:
            filtered_posts = posts
            
        return random.choice(filtered_posts)
    
    def _decide_vote_type(self) -> str:
        """Decide whether to upvote or downvote based on personality"""
        upvote_chance = self.personality.upvote_tendency
        downvote_chance = self.personality.downvote_tendency
        
        total_chance = upvote_chance + downvote_chance
        if total_chance == 0:
            return random.choice(['up', 'down'])
        
        upvote_probability = upvote_chance / total_chance
        return 'up' if random.random() < upvote_probability else 'down'
    
    def generate_content(self, action: BotAction, context: Dict = None) -> str:
        """Generate content based on personality and action type"""
        try:
            if action.action_type == 'create_post':
                return self._generate_post_content()
            elif action.action_type in ['comment_post', 'reply_comment']:
                return self._generate_comment_content(context)
            return ""
        except Exception as e:
            print(f"❌ Error generating content for {self.bot_id}: {e}")
            return self._get_fallback_content(action.action_type)
    
    def _generate_post_content(self) -> tuple:
        """Generate post title and content"""
        try:
            # Choose topic based on interests
            topic = random.choice(self.personality.topic_interests)
            
            # Build prompt based on personality
            prompt = self._build_post_prompt(topic)
            
            response = genai.GenerativeModel('gemini-1.5-flash').generate_content(prompt)
            
            # Parse response
            lines = response.text.strip().split('\n')
            title = lines[0].replace('# ', '').replace('## ', '').strip()
            content = '\n'.join(lines[1:]).strip()
            
            # Apply personality styling
            title = self._apply_personality_styling(title)
            content = self._apply_personality_styling(content)
            
            return title, content
        except Exception as e:
            print(f"❌ Error generating post content: {e}")
            return self._get_fallback_post()
    
    def _generate_comment_content(self, context: Dict) -> str:
        """Generate comment content based on context"""
        try:
            prompt = self._build_comment_prompt(context)
            response = genai.GenerativeModel('gemini-1.5-flash').generate_content(prompt)
            content = response.text.strip()
            return self._apply_personality_styling(content)
        except Exception as e:
            print(f"❌ Error generating comment: {e}")
            return self._get_fallback_content('comment')
    
    def _build_post_prompt(self, topic: str) -> str:
        """Build a prompt for post generation based on personality"""
        style = self.personality.writing_style
        personality_desc = self.personality.description
        
        prompt = f"""Write a forum post about {topic}. 

Personality: {personality_desc}

Style guidelines:
"""
        
        if style.get('average_length') == 'short':
            prompt += "- Keep it brief and to the point (under 200 words)\n"
        elif style.get('average_length') == 'long':
            prompt += "- Write a detailed, thoughtful post (300-500 words)\n"
        else:
            prompt += "- Medium length post (200-300 words)\n"
            
        if style.get('formal_tone'):
            prompt += "- Use formal, academic language\n"
        elif style.get('informal'):
            prompt += "- Use casual, informal language\n"
            
        if style.get('exclamation_marks'):
            prompt += "- Show enthusiasm with exclamation marks\n"
            
        prompt += "\nProvide a title on the first line, then the content."
        
        return prompt
    
    def _build_comment_prompt(self, context: Dict) -> str:
        """Build a prompt for comment generation"""
        # Check if this is a reply to a comment or a comment on a post
        if 'content' in context and 'author' in context and 'post' in context:
            # This is a comment we're replying to
            comment_content = context.get('content', '')[:300]  # Truncate for prompt
            comment_author = context.get('author', {}).get('username', 'Unknown')
            post_title = context.get('post', {}).get('title', 'Unknown Post')
            
            personality_desc = self.personality.description
            style = self.personality.writing_style
            
            prompt = f"""Write a reply to this comment on the forum post "{post_title}":

Comment by {comment_author}: {comment_content}...

Your personality: {personality_desc}

Style:
"""
        else:
            # This is a comment on a post
            post_title = context.get('title', 'Unknown Post')
            post_content = context.get('content', '')[:300]  # Truncate for prompt
            
            personality_desc = self.personality.description
            style = self.personality.writing_style
            
            prompt = f"""Write a comment responding to this forum post:

Title: {post_title}
Content: {post_content}...

Your personality: {personality_desc}

Style:
"""
        
        if style.get('average_length') == 'short':
            prompt += "- Keep comment brief (under 100 words)\n"
        elif style.get('average_length') == 'long':
            prompt += "- Write a thoughtful, detailed comment (150-250 words)\n"
        else:
            prompt += "- Medium length comment (100-150 words)\n"
            
        if style.get('helpful_phrases'):
            prompt += "- Try to be helpful and constructive\n"
            
        if style.get('question_words'):
            prompt += "- Ask thoughtful questions or raise important points\n"
            
        return prompt
    
    def _apply_personality_styling(self, text: str) -> str:
        """Apply personality-specific styling to generated text"""
        style = self.personality.writing_style
        
        # Add personality-specific words/phrases
        if style.get('positive_words') and self.personality.personality_type.value == 'enthusiast':
            # Occasionally replace neutral words with positive ones
            positive_words = style['positive_words']
            if random.random() < 0.3:  # 30% chance
                text = text.replace('good', random.choice(positive_words))
        
        if style.get('slang') and self.personality.personality_type.value == 'casual':
            # Occasionally add slang
            slang_words = style['slang']
            if random.random() < 0.4:  # 40% chance
                text += f" {random.choice(slang_words)}"
        
        return text
    
    def _get_fallback_content(self, action_type: str) -> str:
        """Get fallback content when generation fails"""
        fallbacks = {
            'comment': [
                "Interesting point!",
                "Thanks for sharing this.",
                "I agree with this perspective.",
                "This is worth considering."
            ],
            'post': ("Interesting Discussion", "What are your thoughts on this topic?")
        }
        
        if action_type == 'create_post':
            return fallbacks['post']
        else:
            return random.choice(fallbacks['comment'])
    
    def _get_fallback_post(self) -> tuple:
        """Get fallback post content"""
        titles = [
            "What's everyone working on today?",
            "Interesting discussion topic",
            "Thoughts on recent developments?",
            "What's your take on this?"
        ]
        
        contents = [
            "I'm curious to hear what everyone thinks about this.",
            "Always interested in different perspectives.",
            "What's your experience with this?",
            "Looking forward to the discussion!"
        ]
        
        return random.choice(titles), random.choice(contents)
    
    def execute_action(self, action: BotAction) -> bool:
        """Execute the decided action"""
        try:
            if action.action_type == 'create_post':
                return self._create_post(action)
            elif action.action_type == 'comment_post':
                return self._comment_on_post(action)
            elif action.action_type == 'vote_post':
                return self._vote_on_post(action)
            elif action.action_type == 'vote_comment':
                return self._vote_on_comment(action)
            elif action.action_type == 'reply_comment':
                return self._reply_to_comment(action)
            
            return False
        except Exception as e:
            print(f"❌ Error executing action for {self.bot_id}: {e}")
            return False
        finally:
            self.last_action_time = datetime.now()
            self.action_history.append({
                'action': action.action_type,
                'timestamp': datetime.now(),
                'success': True  # We'll update this based on actual result
            })
    
    def _create_post(self, action: BotAction) -> bool:
        """Create a new post"""
        title, content = self.generate_content(action)
        
        # Fall back to existing communities if preferred doesn't exist
        community_name = action.community_name or 'general'
        if community_name not in ['general', 'bots', 'testing']:
            # Map non-existent communities to existing ones
            community_mapping = {
                'help': 'general',
                'tutorials': 'bots', 
                'philosophy': 'general',
                'academic': 'general',
                'technology': 'general',
                'showoff': 'bots',
                'debate': 'general',
                'analysis': 'general',
                'casual': 'general',
                'fun': 'general'
            }
            community_name = community_mapping.get(community_name, 'general')
        
        url = f"{self.base_url}/posts/"
        data = {
            'title': title,
            'content': content,
            'community_name': community_name
        }
        
        response = requests.post(url, headers=self.get_headers(), json=data)
        
        if response.status_code == 201:
            print(f"✅ {self.bot_id} created post: {title}")
            return True
        else:
            print(f"❌ {self.bot_id} failed to create post: {response.text}")
            return False
    
    def _comment_on_post(self, action: BotAction) -> bool:
        """Comment on a post"""
        # First, get the post details for context
        post_url = f"{self.base_url}/posts/{action.target_id}/"
        post_response = requests.get(post_url, headers=self.get_headers())
        
        if post_response.status_code != 200:
            return False
        
        post_data = post_response.json()
        comment_content = self.generate_content(action, post_data)
        
        url = f"{self.base_url}/posts/{action.target_id}/comment/"
        data = {'content': comment_content}
        
        response = requests.post(url, headers=self.get_headers(), json=data)
        
        if response.status_code == 201:
            print(f"✅ {self.bot_id} commented on post {action.target_id}")
            return True
        else:
            print(f"❌ {self.bot_id} failed to comment: {response.text}")
            return False
    
    def _vote_on_post(self, action: BotAction) -> bool:
        """Vote on a post"""
        url = f"{self.base_url}/posts/{action.target_id}/vote/"
        data = {'vote_type': action.vote_type}
        
        response = requests.post(url, headers=self.get_headers(), json=data)
        
        if response.status_code == 200:
            print(f"✅ {self.bot_id} {action.vote_type}voted post {action.target_id}")
            return True
        else:
            print(f"❌ {self.bot_id} failed to vote: {response.text}")
            return False
    
    def _vote_on_comment(self, action: BotAction) -> bool:
        """Vote on a comment"""
        url = f"{self.base_url}/comments/{action.target_id}/vote/"
        data = {'vote_type': action.vote_type}
        
        response = requests.post(url, headers=self.get_headers(), json=data)
        
        if response.status_code == 200:
            print(f"✅ {self.bot_id} {action.vote_type}voted comment {action.target_id}")
            return True
        else:
            print(f"❌ {self.bot_id} failed to vote on comment: {response.text}")
            return False
    
    def _reply_to_comment(self, action: BotAction) -> bool:
        """Reply to a comment"""
        # First, get the comment details for context
        comment_url = f"{self.base_url}/comments/{action.target_id}/"
        comment_response = requests.get(comment_url, headers=self.get_headers())
        
        if comment_response.status_code != 200:
            print(f"❌ {self.bot_id} failed to get comment {action.target_id}: {comment_response.text}")
            return False
        
        comment_data = comment_response.json()
        
        # If the comment.post is just an ID, fetch the full post data
        if isinstance(comment_data.get('post'), int):
            post_id = comment_data['post']
            post_url = f"{self.base_url}/posts/{post_id}/"
            post_response = requests.get(post_url, headers=self.get_headers())
            
            if post_response.status_code == 200:
                post_data = post_response.json()
                # Add the full post data to the comment context
                comment_data['post'] = post_data
        
        reply_content = self.generate_content(action, comment_data)
        
        url = f"{self.base_url}/comments/{action.target_id}/reply/"
        data = {'content': reply_content}
        
        response = requests.post(url, headers=self.get_headers(), json=data)
        
        if response.status_code == 201:
            print(f"✅ {self.bot_id} replied to comment {action.target_id}")
            return True
        else:
            print(f"❌ {self.bot_id} failed to reply to comment: {response.text}")
            return False
