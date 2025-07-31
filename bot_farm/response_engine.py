"""
Response Generation Engine

Handles LLM integration and bot response generation with quality control
"""

import asyncio
import google.generativeai as genai
import json
import time
import random
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from .models import Bot, BotInteraction, InteractionType
from .personalities import PersonalityPromptBuilder
from .memory_system import BotMemoryManager
from .config import get_config, LLMProvider


class LLMClient:
    """Unified interface for different LLM providers"""
    
    def __init__(self, provider: LLMProvider):
        self.provider = provider
        self.config = get_config()
        self.provider_config = self.config.llm_providers.get(provider, {})
        
        # Initialize Google Generative AI
        if provider == LLMProvider.GOOGLE:
            genai.configure(api_key=self.provider_config.get('api_key'))
            self.google_model = genai.GenerativeModel(
                self.provider_config.get('model', 'gemini-1.5-flash')
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}. Only Google is supported.")
    
    async def generate_response(self, system_prompt: str, user_prompt: str,
                              temperature: float = 0.8, max_tokens: int = 1000) -> str:
        """Generate response using the configured LLM provider"""
        
        try:
            if self.provider == LLMProvider.GOOGLE:
                return await self._google_generate(system_prompt, user_prompt, temperature, max_tokens)
            else:
                raise ValueError(f"Unsupported LLM provider: {self.provider}")
        
        except Exception as e:
            print(f"LLM generation error: {e}")
            return self._fallback_response()
    
    async def _google_generate(self, system_prompt: str, user_prompt: str,
                              temperature: float, max_tokens: int) -> str:
        """Generate response using Google Gemini API"""
        
        # Combine system and user prompts as Gemini doesn't have separate system prompt
        combined_prompt = f"{system_prompt}\n\nUser: {user_prompt}\n\nAssistant:"
        
        try:
            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )
            
            # Generate response
            response = self.google_model.generate_content(
                combined_prompt,
                generation_config=generation_config
            )
            
            return response.text.strip()
            
        except Exception as e:
            print(f"Google Gemini API error: {e}")
            raise
    
    def _fallback_response(self) -> str:
        """Fallback response when LLM fails"""
        fallback_responses = [
            "That's an interesting point. I'd like to think about that more.",
            "Thanks for sharing that perspective.",
            "I appreciate you bringing this up for discussion.",
            "That raises some good questions worth exploring.",
            "I find this topic quite thought-provoking."
        ]
        return random.choice(fallback_responses)


class ResponseQualityScorer:
    """Scores the quality of bot responses"""
    
    def __init__(self):
        self.config = get_config()
    
    def score_response(self, response: str, context: Dict[str, Any]) -> float:
        """Score response quality from 0.0 to 1.0"""
        
        score = 0.5  # Base score
        
        # Length appropriateness
        word_count = len(response.split())
        if 10 <= word_count <= 200:  # Reasonable length
            score += 0.1
        elif word_count < 5:  # Too short
            score -= 0.2
        elif word_count > 300:  # Too long
            score -= 0.1
        
        # Content quality indicators
        if self._has_substance(response):
            score += 0.2
        
        if self._is_relevant_to_context(response, context):
            score += 0.2
        
        if self._is_well_structured(response):
            score += 0.1
        
        # Negative indicators
        if self._is_repetitive(response):
            score -= 0.2
        
        if self._has_inappropriate_content(response):
            score -= 0.5
        
        return max(0.0, min(1.0, score))
    
    def _has_substance(self, response: str) -> bool:
        """Check if response has substantive content"""
        # Simple heuristics
        sentences = response.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
        
        return (
            avg_sentence_length > 5 and  # Not just short phrases
            len(sentences) > 1 and  # Multiple sentences
            not response.lower().startswith(('ok', 'yes', 'no', 'maybe'))  # Not just simple answers
        )
    
    def _is_relevant_to_context(self, response: str, context: Dict[str, Any]) -> bool:
        """Check if response is relevant to the context"""
        # Simplified relevance check
        if 'keywords' in context:
            response_lower = response.lower()
            return any(keyword.lower() in response_lower for keyword in context['keywords'])
        return True  # Default to True if no keywords provided
    
    def _is_well_structured(self, response: str) -> bool:
        """Check if response is well-structured"""
        # Basic structure checks
        has_punctuation = any(p in response for p in '.!?')
        proper_capitalization = response[0].isupper() if response else False
        
        return has_punctuation and proper_capitalization
    
    def _is_repetitive(self, response: str) -> bool:
        """Check if response is overly repetitive"""
        words = response.lower().split()
        unique_words = set(words)
        
        # If less than 60% unique words, consider repetitive
        if len(words) > 10:  # Only check for longer responses
            uniqueness_ratio = len(unique_words) / len(words)
            return uniqueness_ratio < 0.6
        
        return False
    
    def _has_inappropriate_content(self, response: str) -> bool:
        """Check for inappropriate content (simplified)"""
        # Basic filter - in production, use more sophisticated content filtering
        inappropriate_words = ['spam', 'offensive', 'inappropriate']  # Placeholder
        response_lower = response.lower()
        
        return any(word in response_lower for word in inappropriate_words)


class RepetitionPreventer:
    """Prevents bots from repeating themselves too much"""
    
    def __init__(self, memory_manager: BotMemoryManager):
        self.memory_manager = memory_manager
    
    def check_for_repetition(self, bot_id: str, new_response: str,
                           similarity_threshold: float = 0.8) -> Tuple[bool, float]:
        """Check if response is too similar to recent responses"""
        
        # Get recent interactions
        recent_interactions = self.memory_manager.storage.get_interactions(
            bot_id, limit=10
        )
        
        if not recent_interactions:
            return False, 0.0
        
        max_similarity = 0.0
        
        for interaction in recent_interactions:
            similarity = self._calculate_similarity(new_response, interaction.response_text)
            max_similarity = max(max_similarity, similarity)
        
        is_repetitive = max_similarity > similarity_threshold
        return is_repetitive, max_similarity
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts (simplified)"""
        
        # Simple word-based similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0


class ContextReader:
    """Reads and processes context for bot responses"""
    
    def __init__(self, api_client):
        self.api_client = api_client
        self.config = get_config()
    
    async def get_context_for_comment(self, comment_id: str) -> Dict[str, Any]:
        """Get full context for responding to a comment"""
        
        # Get the comment
        comment = await self.api_client.get(f'/comments/{comment_id}/')
        if not comment:
            return {}
        
        # Get the post
        post = await self.api_client.get(f'/posts/{comment["post"]}/')
        if not post:
            return {}
        
        # Get thread chain (parent comments)
        thread_chain = await self._get_thread_chain(comment)
        
        # Get sibling comments
        siblings = await self._get_sibling_comments(comment)
        
        # Optimize context for token limits
        context = {
            'post': {
                'title': post['title'],
                'content': post['content'],
                'author': post['author']['username'],
                'community': post['community_name'],
                'score': post['score']
            },
            'target_comment': {
                'content': comment['content'],
                'author': comment['author']['username'],
                'score': comment['score']
            },
            'thread_chain': thread_chain,
            'sibling_comments': siblings[:3],  # Limit siblings
            'community_context': await self._get_community_context(post['community_name'])
        }
        
        return self._optimize_context_for_tokens(context)
    
    async def get_context_for_post(self, post_id: str) -> Dict[str, Any]:
        """Get context for commenting on a post"""
        
        post = await self.api_client.get(f'/posts/{post_id}/')
        if not post:
            return {}
        
        # Get top comments for context
        comments = await self.api_client.get(f'/posts/{post_id}/comments/')
        top_comments = sorted(comments.get('results', []), 
                             key=lambda x: x['score'], reverse=True)[:5]
        
        context = {
            'post': {
                'title': post['title'],
                'content': post['content'],
                'author': post['author']['username'],
                'community': post['community_name'],
                'score': post['score']
            },
            'top_comments': [
                {
                    'content': c['content'][:200] + '...' if len(c['content']) > 200 else c['content'],
                    'author': c['author']['username'],
                    'score': c['score']
                }
                for c in top_comments
            ],
            'community_context': await self._get_community_context(post['community_name'])
        }
        
        return self._optimize_context_for_tokens(context)
    
    async def _get_thread_chain(self, comment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get the full conversation thread leading to this comment"""
        
        thread = []
        current = comment
        
        # Walk up the parent chain
        while current.get('parent_comment'):
            parent_id = current['parent_comment']
            parent = await self.api_client.get(f'/comments/{parent_id}/')
            if parent:
                thread.append({
                    'content': parent['content'],
                    'author': parent['author']['username'],
                    'score': parent['score']
                })
                current = parent
            else:
                break
        
        thread.reverse()  # Chronological order
        return thread
    
    async def _get_sibling_comments(self, comment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get other comments at the same level"""
        
        if comment.get('parent_comment'):
            # Get replies to the same parent
            parent_id = comment['parent_comment']
            siblings_response = await self.api_client.get(f'/comments/{parent_id}/replies/')
        else:
            # Get other top-level comments on the same post
            post_id = comment['post']
            siblings_response = await self.api_client.get(f'/posts/{post_id}/comments/')
        
        if not siblings_response:
            return []
        
        siblings = siblings_response.get('results', [])
        
        # Filter out the current comment and sort by score
        siblings = [s for s in siblings if s['id'] != comment['id']]
        siblings.sort(key=lambda x: x['score'], reverse=True)
        
        return siblings
    
    async def _get_community_context(self, community_name: str) -> Dict[str, Any]:
        """Get context about the community"""
        
        community = await self.api_client.get(f'/communities/{community_name}/')
        if not community:
            return {}
        
        return {
            'name': community['name'],
            'description': community['description'],
            'member_count': community['member_count'],
            'post_count': community['post_count']
        }
    
    def _optimize_context_for_tokens(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize context to fit within token limits"""
        
        # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
        def estimate_tokens(text: str) -> int:
            return len(text) // 4
        
        max_tokens = self.config.max_context_tokens
        current_tokens = estimate_tokens(json.dumps(context))
        
        if current_tokens <= max_tokens:
            return context
        
        # Start reducing context
        optimized = context.copy()
        
        # Reduce thread chain if too long
        if 'thread_chain' in optimized and len(optimized['thread_chain']) > 3:
            optimized['thread_chain'] = optimized['thread_chain'][-3:]  # Keep last 3
        
        # Reduce sibling comments
        if 'sibling_comments' in optimized and len(optimized['sibling_comments']) > 2:
            optimized['sibling_comments'] = optimized['sibling_comments'][:2]
        
        # Truncate long content
        if 'post' in optimized and 'content' in optimized['post']:
            content = optimized['post']['content']
            if len(content) > 500:
                optimized['post']['content'] = content[:500] + "..."
        
        return optimized


class ResponseEngine:
    """Main response generation engine"""
    
    def __init__(self):
        self.config = get_config()
        self.quality_scorer = ResponseQualityScorer()
        self.memory_manager = BotMemoryManager()
        self.repetition_preventer = RepetitionPreventer(self.memory_manager)
    
    async def generate_response(self, bot: Bot, context: Dict[str, Any],
                               interaction_type: InteractionType) -> Optional[str]:
        """Generate a high-quality response for the bot"""
        
        # Create LLM client
        llm_client = LLMClient(bot.llm_provider)
        
        # Build personality prompt
        prompt_builder = PersonalityPromptBuilder(bot.personality)
        system_prompt = prompt_builder.build_system_prompt(context)
        
        # Build user prompt based on interaction type
        user_prompt = self._build_user_prompt(context, interaction_type, bot)
        
        # Add memory context
        memory_context = self._get_memory_context(bot, context)
        if memory_context:
            user_prompt += f"\n\nYour relevant memories:\n{memory_context}"
        
        # Generate initial response
        response = await llm_client.generate_response(
            system_prompt, user_prompt,
            temperature=0.8,
            max_tokens=1000
        )
        
        if not response:
            return None
        
        # Quality control pipeline
        response = await self._quality_control_pipeline(bot, response, context)
        
        return response
    
    def _build_user_prompt(self, context: Dict[str, Any], 
                          interaction_type: InteractionType, bot: Bot) -> str:
        """Build the user prompt based on context and interaction type"""
        
        prompt = ""
        
        if interaction_type == InteractionType.COMMENT_CREATED:
            # Responding to a post
            post = context.get('post', {})
            prompt = f"""
SITUATION: You're reading a post in c/{post.get('community', 'unknown')}

POST TITLE: {post.get('title', '')}
POST CONTENT: {post.get('content', '')}
POST AUTHOR: {post.get('author', 'Unknown')} (Score: {post.get('score', 0)})

"""
            
            # Add top comments context
            if context.get('top_comments'):
                prompt += "CURRENT DISCUSSION:\n"
                for i, comment in enumerate(context['top_comments'][:3]):
                    prompt += f"{i+1}. {comment['author']}: {comment['content']}\n"
            
            prompt += f"\nAs {bot.name}, write a comment on this post:"
        
        elif interaction_type == InteractionType.REPLY_SENT:
            # Replying to a comment
            post = context.get('post', {})
            target = context.get('target_comment', {})
            
            prompt = f"""
SITUATION: You're in a discussion thread in c/{post.get('community', 'unknown')}

ORIGINAL POST: {post.get('title', '')}
{post.get('content', '')[:200]}...

CONVERSATION THREAD:
"""
            
            # Add thread chain
            for i, thread_comment in enumerate(context.get('thread_chain', [])):
                prompt += f"{i+1}. {thread_comment['author']}: {thread_comment['content']}\n"
            
            prompt += f"\nCOMMENT TO RESPOND TO:\n{target['author']}: {target['content']}\n"
            prompt += f"\nAs {bot.name}, write a thoughtful reply:"
        
        elif interaction_type == InteractionType.POST_CREATED:
            # Creating a new post
            community = context.get('community_context', {})
            prompt = f"""
SITUATION: You want to start a discussion in c/{community.get('name', 'unknown')}

COMMUNITY INFO: {community.get('description', '')}
Community size: {community.get('member_count', 0)} members

Create an engaging post that would generate good discussion in this community.
Your post should include both a title and content.

Format your response as:
TITLE: [your title here]
CONTENT: [your post content here]
"""
        
        return prompt
    
    def _get_memory_context(self, bot: Bot, context: Dict[str, Any]) -> str:
        """Get relevant memory context for the bot"""
        
        # Extract topic and community from context
        topic = self._extract_topic_from_context(context)
        community = context.get('post', {}).get('community') or context.get('community_context', {}).get('name')
        
        if not topic and not community:
            return ""
        
        # Get relevant memories
        memories = self.memory_manager.get_relevant_context(
            bot.id, topic or "general", community or "general", limit=3
        )
        
        if not memories:
            return ""
        
        memory_text = ""
        for memory in memories:
            memory_text += f"- {memory.interaction_summary}\n"
        
        return memory_text
    
    def _extract_topic_from_context(self, context: Dict[str, Any]) -> Optional[str]:
        """Extract main topic from context"""
        
        # Look in post title and content
        text_sources = []
        
        if context.get('post'):
            text_sources.extend([
                context['post'].get('title', ''),
                context['post'].get('content', '')
            ])
        
        if context.get('target_comment'):
            text_sources.append(context['target_comment'].get('content', ''))
        
        combined_text = ' '.join(text_sources).lower()
        
        # Simple topic extraction (could be enhanced with NLP)
        if any(word in combined_text for word in ['python', 'javascript', 'code', 'programming']):
            return 'technology'
        elif any(word in combined_text for word in ['philosophy', 'ethics', 'moral']):
            return 'philosophy'
        elif any(word in combined_text for word in ['politics', 'government', 'policy']):
            return 'politics'
        
        return None
    
    async def _quality_control_pipeline(self, bot: Bot, response: str, 
                                       context: Dict[str, Any]) -> str:
        """Run response through quality control pipeline"""
        
        # Stage 1: Quality scoring
        quality_score = self.quality_scorer.score_response(response, context)
        
        # Stage 2: Repetition check
        is_repetitive, similarity = self.repetition_preventer.check_for_repetition(
            bot.id, response
        )
        
        # Stage 3: If quality is too low or too repetitive, try to improve
        if quality_score < self.config.min_response_quality_score or is_repetitive:
            response = await self._improve_response(bot, response, context, quality_score, similarity)
        
        return response
    
    async def _improve_response(self, bot: Bot, original_response: str,
                               context: Dict[str, Any], quality_score: float,
                               similarity_score: float) -> str:
        """Attempt to improve a low-quality or repetitive response"""
        
        llm_client = LLMClient(bot.llm_provider)
        
        improvement_prompt = f"""
You are {bot.personality.name}. You wrote this response:
"{original_response}"

Issues identified:
"""
        
        if quality_score < self.config.min_response_quality_score:
            improvement_prompt += f"- Quality score too low: {quality_score:.2f}\n"
        
        if similarity_score > self.config.max_similarity_threshold:
            improvement_prompt += f"- Too similar to recent responses: {similarity_score:.2f}\n"
        
        improvement_prompt += f"""
Please rewrite this response to:
1. Be more substantive and engaging
2. Add unique perspective or examples  
3. Maintain your personality as {bot.personality.name}
4. Stay relevant to the context
5. Avoid repetition of your recent posts

Context: {context.get('post', {}).get('title', 'Discussion')}
"""
        
        try:
            improved_response = await llm_client.generate_response(
                f"You are {bot.personality.name} improving your response quality.",
                improvement_prompt,
                temperature=0.9,  # Slightly higher for more creativity
                max_tokens=800
            )
            
            # Check if improvement is actually better
            improved_quality = self.quality_scorer.score_response(improved_response, context)
            
            if improved_quality > quality_score:
                return improved_response
        
        except Exception as e:
            print(f"Response improvement failed: {e}")
        
        # Return original if improvement failed
        return original_response
