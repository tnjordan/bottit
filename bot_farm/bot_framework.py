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
    
    def has_base_comment_on_post(self, post_id: int) -> bool:
        """Check if this bot has already made a base-level comment on the given post"""
        try:
            url = f"{self.base_url}/users/{self.bot_id}/post_comments/"
            params = {'post_id': post_id}
            response = requests.get(url, headers=self.get_headers(), params=params)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('has_commented', False)
            return False
        except Exception as e:
            print(f"❌ Error checking base comment for {self.bot_id}: {e}")
            return False
    
    def has_replied_to_comment(self, comment_id: int, all_comments: List[Dict]) -> bool:
        """Check if this bot has already replied to a specific comment"""
        for comment in all_comments:
            comment_author = comment.get('author', {}).get('username')
            parent_comment_id = comment.get('parent_comment')
            
            # Check if this is our comment replying to the target comment
            if (comment_author == self.bot_id
                    and parent_comment_id == comment_id):
                return True
        return False
    
    def get_pending_replies(self) -> List[Dict]:
        """Get comments that are replies to this bot's comments"""
        try:
            url = f"{self.base_url}/users/{self.bot_id}/pending_replies/"
            response = requests.get(url, headers=self.get_headers())
            
            if response.status_code == 200:
                data = response.json()
                return data.get('replies', [])
            return []
        except Exception as e:
            print(f"❌ Error getting pending replies for {self.bot_id}: {e}")
            return []

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
        """Decide what action to take based on personality and available content, with smart reply prioritization"""
        if not self.should_take_action():
            return None
            
        probabilities = self.personality.action_probabilities
        actions = []
        
        # First priority: Check for replies to our comments that need responding to
        pending_replies = self.get_pending_replies()
        current_post_replies = []  # Replies on the current post
        
        # If we have a current post, prioritize replies on that post
        if available_posts:
            current_post_id = available_posts[0]['id']
            
            # Find replies to our comments specifically on the current post
            for reply in pending_replies:
                reply_post_id = reply.get('post')
                if reply_post_id == current_post_id:
                    # Skip self-replies
                    reply_author = reply.get('author', {}).get('username')
                    if reply_author == self.bot_id:
                        continue
                    current_post_replies.append(reply)
        
        # ONLY respond to replies on the current post - ignore all old replies from other posts
        if current_post_replies:
            # HEAVILY prioritize responding to replies on the current active post
            actions.extend(['respond_to_current_reply'] * int(probabilities.reply_to_comment * 1000))  # 10x more likely
            print(f"🔥 {self.bot_id} found {len(current_post_replies)} replies on current post - HEAVILY prioritizing!")
        
        # No longer respond to old replies from other posts - bots focus ONLY on current discussion
        
        # Focus exclusively on the most recent post if available - this ensures all bot activity is concentrated
        if available_posts:
            latest_post = available_posts[0]  # Only work on the most recent post
            post_id = latest_post['id']
            
            # Check if we've already made a base-level comment on this specific post
            already_commented = self.has_base_comment_on_post(post_id)
            
            # Boost interaction probabilities for the current active post
            actions.extend(['vote_post'] * int(probabilities.vote_on_post * 150))  # 1.5x more likely
            
            # If there are comments on the latest post, prioritize replies over base comments
            if available_comments:
                # Filter out only our own comments - keep all other bots' comments as valid reply targets
                other_comments = []
                for comment in available_comments:
                    comment_author = comment.get('author', {}).get('username')
                    # Skip our own comments
                    if comment_author == self.bot_id:
                        continue
                    
                    other_comments.append(comment)
                
                if other_comments:
                    # ONLY allow base-level comments if we haven't already commented - NEVER if we have
                    if not already_commented:
                        # Prioritize base comment when haven't commented yet, but still allow replies
                        actions.extend(['comment_post'] * int(probabilities.comment_on_post * 600))  # High priority for first comment
                        actions.extend(['vote_comment'] * int(probabilities.vote_on_comment * 200))  # Lower priority for votes
                        actions.extend(['reply_comment'] * int(probabilities.reply_to_comment * 300))  # Lower priority for replies
                        print(f"🤖 {self.bot_id} prioritizing base comment (hasn't commented yet) over {len(other_comments)} replies")
                    else:
                        # If already commented, focus entirely on interacting with others
                        actions.extend(['vote_comment'] * int(probabilities.vote_on_comment * 400))  # 4x more likely
                        actions.extend(['reply_comment'] * int(probabilities.reply_to_comment * 800))  # 8x more likely
                        print(f"🚫 {self.bot_id} BLOCKED from base comment - already commented on post {post_id}, focusing on replies")
                else:
                    # No other comments exist, definitely make base comment if we haven't commented
                    if not already_commented:
                        actions.extend(['comment_post'] * int(probabilities.comment_on_post * 800))  # Very high priority - no other comments to interact with
                        print(f"🤖 {self.bot_id} will make first base comment (no other comments to reply to)")
                    else:
                        print(f"🚫 {self.bot_id} BLOCKED from base comment - already commented on post {post_id}")
            else:
                # No comments at all, definitely make base comment if we haven't commented
                if not already_commented:
                    actions.extend(['comment_post'] * int(probabilities.comment_on_post * 800))  # Very high priority - start the conversation
                    print(f"🤖 {self.bot_id} will make first base comment (no comments on post yet)")
                else:
                    print(f"🚫 {self.bot_id} BLOCKED from base comment - already commented on post {post_id}")
            
            # If we already commented but there are no other comments to reply to, just vote or do nothing
            if already_commented and not other_comments:
                print(f"🤖 {self.bot_id} already commented on post {post_id} with no other comments to reply to - limited actions")
            
            # Make post creation very rare when there's an active latest post - bots should focus on current discussion
            actions.extend(['create_post'] * int(probabilities.create_post * 10))  # Very rare - only 1% of normal probability
        else:
            # No recent post available, heavily favor creating new content
            actions.extend(['create_post'] * int(probabilities.create_post * 300))  # 3x more likely
        
        if not actions:
            print(f"⚠️ {self.bot_id} has no available actions - this shouldn't happen!")
            return None
            
        chosen_action = random.choice(actions)
        print(f"🎯 {self.bot_id} chose action: {chosen_action} from {len(actions)} options")
        
        # Handle the special case of responding to replies to our comments - ONLY on current post
        if chosen_action == 'respond_to_current_reply' and current_post_replies:
            # Filter out replies we've already responded to
            available_replies = []
            for reply in current_post_replies:
                if not self.has_replied_to_comment(reply['id'], available_comments):
                    available_replies.append(reply)
            
            if available_replies:
                reply_target = random.choice(available_replies)
                print(f"🔥 {self.bot_id} prioritizing current post reply from {reply_target.get('author', {}).get('username', 'unknown')}")
                return BotAction(
                    action_type='reply_comment',
                    target_id=reply_target['id']
                )
            else:
                print(f"🚫 {self.bot_id} no new replies to respond to - all already replied to")
        elif chosen_action == 'create_post':
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
            # Filter out our own comments and ensure only current post comments
            current_post_id = available_posts[0]['id'] if available_posts else None
            other_comments = []
            
            for comment in available_comments:
                comment_author = comment.get('author', {}).get('username')
                comment_post_id = comment.get('post')
                
                # Skip our own comments
                if comment_author == self.bot_id:
                    continue
                
                # Silently skip comments from wrong posts (safety check)
                if comment_post_id != current_post_id:
                    continue
                
                other_comments.append(comment)
            
            if other_comments:
                comment = random.choice(other_comments)
                current_post_id = available_posts[0]['id'] if available_posts else None
                print(f"🎯 {self.bot_id} voting on comment {comment.get('id')} on current post {current_post_id}")
                return BotAction(
                    action_type='vote_comment',
                    target_id=comment['id'],
                    vote_type=self._decide_vote_type()
                )
            else:
                current_post_id = available_posts[0]['id'] if available_posts else None
                print(f"⚠️ {self.bot_id} no valid comments to vote on in current post {current_post_id}")
        elif chosen_action == 'reply_comment' and available_comments:
            # Filter out our own comments, but allow replies to any other bot's comments
            other_comments = []
            current_post_id = available_posts[0]['id'] if available_posts else None
            
            for comment in available_comments:
                comment_author = comment.get('author', {}).get('username')
                comment_post_id = comment.get('post')
                
                # Skip our own comments
                if comment_author == self.bot_id:
                    continue
                
                # Silently skip comments from wrong posts (safety check)
                if comment_post_id != current_post_id:
                    continue
                
                # Skip comments we've already replied to
                if self.has_replied_to_comment(comment['id'], available_comments):
                    continue
                
                other_comments.append(comment)
            
            if other_comments:
                comment = random.choice(other_comments)
                current_post_id = available_posts[0]['id'] if available_posts else None
                print(f"🎯 {self.bot_id} replying to comment {comment.get('id')} on current post {current_post_id}")
                return BotAction(
                    action_type='reply_comment',
                    target_id=comment['id']
                )
            else:
                current_post_id = available_posts[0]['id'] if available_posts else None
                print(f"⚠️ {self.bot_id} no valid comments to reply to on current post {current_post_id}")
        
        return None
    
    def _choose_post(self, posts: List[Dict]) -> Dict:
        """Always return the most recent post (first in the list) to ensure bots only work on current content"""
        if not posts:
            return None
        
        # Always return the most recent post - no more choice, bots focus on current discussion
        latest_post = posts[0]
        
        # We always work on the most recent post regardless of community preferences
        # (since that's where the current conversation is happening)
        return latest_post
    
    def _choose_community(self) -> str:
        """Choose a community based on preferences"""
        if self.personality.preferred_communities:
            return random.choice(self.personality.preferred_communities)
        return "general"
    
    def _has_commented_on_post(self, post_id: int, available_comments: List[Dict]) -> bool:
        """Check if this bot has already made a level 0 comment on the given post"""
        for comment in available_comments:
            comment_author = comment.get('author', {})
            # Check if this is our comment, on the target post, and is level 0 (no parent)
            if (comment_author.get('username') == self.bot_id
                    and comment.get('post') == post_id
                    and comment.get('parent_comment') is None):
                return True
        return False
    
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
        """Generate post title and content with high temperature for diversity"""
        try:
            # Choose topic based on interests
            topic = random.choice(self.personality.topic_interests)
            
            # Build prompt based on personality
            prompt = self._build_post_prompt(topic)
            
            # Configure generation with higher temperature for more creativity
            generation_config = {
                'temperature': 1.2,  # High temperature for creativity
                'top_p': 0.95,      # Allow diverse token selection
                'top_k': 40,        # Consider more possible tokens
                'max_output_tokens': 500,
                'candidate_count': 1
            }
            
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt, generation_config=generation_config)
            
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
        """Generate comment content with high temperature for diversity"""
        try:
            prompt = self._build_comment_prompt(context)
            
            # Configure generation with higher temperature for more creativity
            generation_config = {
                'temperature': 1.3,  # Even higher temperature for comments
                'top_p': 0.9,       # Allow diverse responses
                'top_k': 50,        # Consider many possible tokens
                'max_output_tokens': 200,
                'candidate_count': 1
            }
            
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt, generation_config=generation_config)
            content = response.text.strip()
            return self._apply_personality_styling(content)
        except Exception as e:
            print(f"❌ Error generating comment: {e}")
            return self._get_fallback_content('comment')
    
    def _build_post_prompt(self, topic: str) -> str:
        """Build a prompt for post generation based on personality with variation"""
        style = self.personality.writing_style
        personality_desc = self.personality.description
        
        # Add randomness to prompt structure
        intro_variations = [
            f"Write a unique forum post about {topic}.",
            f"Create an original discussion about {topic}.", 
            f"Share your thoughts on {topic} in a forum post.",
            f"Write a compelling post discussing {topic}.",
            f"Compose a forum entry about {topic}."
        ]
        
        prompt = f"""{random.choice(intro_variations)}

Your personality: {personality_desc}

Be creative and express your unique perspective. Avoid generic responses.

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
        
        # Add personality-specific creative prompts
        creative_additions = [
            "- Include a personal anecdote or example",
            "- Ask thought-provoking questions",
            "- Share a contrarian viewpoint", 
            "- Reference current trends or events",
            "- Use metaphors or analogies",
            "- Include specific details or examples"
        ]
        
        if random.random() < 0.7:  # 70% chance to add creative element
            prompt += f"- {random.choice(creative_additions)}\n"
            
        prompt += "\nProvide a title on the first line, then the content. Be original and avoid clichés."
        
        return prompt
    
    def _build_comment_prompt(self, context: Dict) -> str:
        """Build a prompt for comment generation with creative variations"""
        # Check if this is a reply to a comment or a comment on a post
        if 'content' in context and 'author' in context and 'post' in context:
            # This is a comment we're replying to
            comment_content = context.get('content', '')[:300]  # Truncate for prompt
            comment_author = context.get('author', {}).get('username', 'Unknown')
            post_title = context.get('post', {}).get('title', 'Unknown Post')
            
            personality_desc = self.personality.description
            style = self.personality.writing_style
            
            reply_variations = [
                f"Write a thoughtful reply to this comment on '{post_title}':",
                f"Respond to {comment_author}'s comment with your unique perspective:",
                "Reply to this comment in your own voice:",
                "Share your thoughts in response to this comment:",
                "Craft a meaningful reply to this comment:"
            ]
            
            prompt = f"""{random.choice(reply_variations)}

Original Post: {post_title}
"""
            
            # Add conversation chain if available
            if 'conversation_chain' in context:
                chain = context['conversation_chain']
                prompt += "\nConversation so far:\n"
                for i, comment in enumerate(chain):
                    author = comment.get('author', {}).get('username', 'Unknown')
                    content = comment.get('content', '')[:200]  # Limit each comment length
                    prompt += f"{i+1}. {author}: {content}\n"
                prompt += f"\nYou are replying to comment {len(chain)} by {comment_author}.\n"
            else:
                prompt += f"\nComment by {comment_author}: {comment_content}...\n"

            prompt += f"""
Your personality: {personality_desc}

Be original and avoid generic responses. Express your unique viewpoint that builds on the conversation.

Style:
"""
        else:
            # This is a comment on a post
            post_title = context.get('title', 'Unknown Post')
            post_content = context.get('content', '')[:300]  # Truncate for prompt
            
            personality_desc = self.personality.description
            style = self.personality.writing_style
            
            comment_variations = [
                "Write an engaging comment on this forum post:",
                "Share your unique perspective on this post:",
                "Respond thoughtfully to this discussion:",
                "Add your voice to this conversation:",
                "Contribute meaningfully to this topic:"
            ]
            
            prompt = f"""{random.choice(comment_variations)}

Title: {post_title}
Content: {post_content}...

Your personality: {personality_desc}

Be creative and avoid clichés. Share specific thoughts or experiences.

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
        
        # Add creative elements randomly
        creative_comment_additions = [
            "- Share a personal experience or example",
            "- Ask a follow-up question",
            "- Offer a different perspective", 
            "- Reference something specific from the post",
            "- Use humor if appropriate",
            "- Build on or challenge a point made"
        ]
        
        if random.random() < 0.6:  # 60% chance to add creative element
            prompt += f"- {random.choice(creative_comment_additions)}\n"
            
        prompt += "\nAvoid generic phrases like 'interesting point' or 'thanks for sharing'."
            
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
    
    def _build_conversation_chain(self, comment_data: Dict, all_comments: List[Dict]) -> List[Dict]:
        """Build the full conversation chain for a comment to provide proper context"""
        chain = []
        current_comment = comment_data
        
        # Build the chain by following parent_comment links up to the root
        while current_comment:
            chain.insert(0, current_comment)  # Insert at beginning to maintain order
            
            parent_id = current_comment.get('parent_comment')
            if not parent_id:
                break
                
            # Find the parent comment
            parent_comment = None
            for comment in all_comments:
                if comment['id'] == parent_id:
                    parent_comment = comment
                    break
            
            current_comment = parent_comment
        
        return chain
    
    def _reply_to_comment(self, action: BotAction) -> bool:
        """Reply to a comment with full conversation context"""
        # First, get the comment details for context
        comment_url = f"{self.base_url}/comments/{action.target_id}/"
        comment_response = requests.get(comment_url, headers=self.get_headers())
        
        if comment_response.status_code != 200:
            print(f"❌ {self.bot_id} failed to get comment {action.target_id}: {comment_response.text}")
            return False
        
        comment_data = comment_response.json()
        
        # Get all comments for this post to build the conversation chain
        post_id = comment_data.get('post')
        if isinstance(post_id, int):
            # Fetch all comments for this post
            all_comments_url = f"{self.base_url}/comments/?post={post_id}"
            all_comments_response = requests.get(all_comments_url, headers=self.get_headers())
            
            all_comments = []
            if all_comments_response.status_code == 200:
                all_comments_data = all_comments_response.json()
                all_comments = all_comments_data.get('results', [])
            
            # Build the conversation chain
            conversation_chain = self._build_conversation_chain(comment_data, all_comments)
            
            # Get the full post data for context
            post_url = f"{self.base_url}/posts/{post_id}/"
            post_response = requests.get(post_url, headers=self.get_headers())
            
            if post_response.status_code == 200:
                post_data = post_response.json()
                # Add the full post data and conversation chain to context
                enhanced_context = {
                    **comment_data,
                    'post': post_data,
                    'conversation_chain': conversation_chain
                }
            else:
                enhanced_context = comment_data
        else:
            enhanced_context = comment_data
        
        reply_content = self.generate_content(action, enhanced_context)
        
        url = f"{self.base_url}/comments/{action.target_id}/reply/"
        data = {'content': reply_content}
        
        response = requests.post(url, headers=self.get_headers(), json=data)
        
        if response.status_code == 201:
            print(f"✅ {self.bot_id} replied to comment {action.target_id}")
            return True
        else:
            print(f"❌ {self.bot_id} failed to reply to comment: {response.text}")
            return False
