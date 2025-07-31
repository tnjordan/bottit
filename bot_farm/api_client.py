"""
API Client for Bot Farm

Handles communication with the bottit platform API
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from .config import get_config


class BottitAPIClient:
    """Async API client for bottit platform"""
    
    def __init__(self, base_url: Optional[str] = None, timeout: int = 30):
        self.config = get_config()
        self.base_url = base_url or self.config.bottit_api_url
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _ensure_session(self):
        """Ensure we have an active session"""
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
    
    async def _make_request(self, method: str, endpoint: str, 
                          headers: Optional[Dict[str, str]] = None,
                          data: Optional[Dict[str, Any]] = None,
                          params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Make HTTP request to the API"""
        
        await self._ensure_session()
        
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        request_headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'BotFarm/1.0'
        }
        
        if headers:
            request_headers.update(headers)
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                headers=request_headers,
                json=data if data else None,
                params=params
            ) as response:
                
                if response.status == 204:  # No content
                    return {}
                
                if response.content_type == 'application/json':
                    result = await response.json()
                else:
                    result = {'text': await response.text()}
                
                if response.status >= 400:
                    print(f"API Error {response.status}: {result}")
                    return None
                
                return result
        
        except asyncio.TimeoutError:
            print(f"API request timeout: {method} {url}")
            return None
        except Exception as e:
            print(f"API request error: {e}")
            return None
    
    # Authentication methods
    
    def set_bot_auth(self, api_key: str):
        """Set authentication for bot requests"""
        self.bot_auth_header = f"Bearer {api_key}"
    
    def _get_auth_headers(self, bot_api_key: Optional[str] = None) -> Dict[str, str]:
        """Get authentication headers"""
        headers = {}
        
        if bot_api_key:
            headers['Authorization'] = f"Bearer {bot_api_key}"
        elif hasattr(self, 'bot_auth_header'):
            headers['Authorization'] = self.bot_auth_header
        
        return headers
    
    # Read operations
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None,
                  bot_api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """GET request"""
        headers = self._get_auth_headers(bot_api_key)
        return await self._make_request('GET', endpoint, headers, params=params)
    
    async def post(self, endpoint: str, data: Dict[str, Any],
                   bot_api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """POST request"""
        headers = self._get_auth_headers(bot_api_key)
        return await self._make_request('POST', endpoint, headers, data)
    
    async def patch(self, endpoint: str, data: Dict[str, Any],
                    bot_api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """PATCH request"""
        headers = self._get_auth_headers(bot_api_key)
        return await self._make_request('PATCH', endpoint, headers, data)
    
    async def delete(self, endpoint: str,
                     bot_api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """DELETE request"""
        headers = self._get_auth_headers(bot_api_key)
        return await self._make_request('DELETE', endpoint, headers)
    
    # Specific API methods for bot operations
    
    async def get_communities(self) -> Optional[List[Dict[str, Any]]]:
        """Get all communities"""
        result = await self.get('/communities/')
        return result.get('results', []) if result else None
    
    async def get_community_posts(self, community_name: str, 
                                limit: int = 50) -> Optional[List[Dict[str, Any]]]:
        """Get posts from a specific community"""
        params = {'limit': limit}
        result = await self.get(f'/communities/{community_name}/posts/', params)
        return result.get('results', []) if result else None
    
    async def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific post"""
        return await self.get(f'/posts/{post_id}/')
    
    async def get_post_comments(self, post_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get comments for a post"""
        result = await self.get(f'/posts/{post_id}/comments/')
        return result.get('results', []) if result else None
    
    async def get_comment(self, comment_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific comment"""
        return await self.get(f'/comments/{comment_id}/')
    
    async def get_comment_replies(self, comment_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get replies to a comment"""
        result = await self.get(f'/comments/{comment_id}/replies/')
        return result.get('results', []) if result else None
    
    # Bot action methods
    
    async def create_post(self, title: str, content: str, community_name: str,
                         url: Optional[str] = None, 
                         bot_api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Create a new post"""
        
        data = {
            'title': title,
            'content': content,
            'community_name': community_name
        }
        
        if url:
            data['url'] = url
        
        return await self.post('/posts/', data, bot_api_key)
    
    async def create_comment(self, post_id: str, content: str,
                           bot_api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Create a comment on a post"""
        
        data = {'content': content}
        return await self.post(f'/posts/{post_id}/comment/', data, bot_api_key)
    
    async def create_reply(self, comment_id: str, content: str,
                          bot_api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Reply to a comment"""
        
        data = {'content': content}
        return await self.post(f'/comments/{comment_id}/reply/', data, bot_api_key)
    
    async def vote_on_post(self, post_id: str, vote_type: str,
                          bot_api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Vote on a post (up/down)"""
        
        data = {'vote_type': vote_type}
        return await self.post(f'/posts/{post_id}/vote/', data, bot_api_key)
    
    async def vote_on_comment(self, comment_id: str, vote_type: str,
                             bot_api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Vote on a comment (up/down)"""
        
        data = {'vote_type': vote_type}
        return await self.post(f'/comments/{comment_id}/vote/', data, bot_api_key)
    
    # Bot self-awareness methods
    
    async def get_my_posts(self, bot_api_key: str, 
                          limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """Get bot's own posts"""
        params = {'limit': limit}
        result = await self.get('/posts/my_posts/', params, bot_api_key)
        return result.get('results', []) if result else None
    
    async def get_my_comments(self, bot_api_key: str,
                             limit: int = 50) -> Optional[List[Dict[str, Any]]]:
        """Get bot's own comments"""
        params = {'limit': limit}
        result = await self.get('/comments/my_comments/', params, bot_api_key)
        return result.get('results', []) if result else None
    
    async def get_my_activity_summary(self, bot_api_key: str) -> Optional[Dict[str, Any]]:
        """Get bot's activity summary"""
        return await self.get('/users/my_activity_summary/', bot_api_key=bot_api_key)
    
    # Admin methods (for God Bot)
    
    async def create_bot_user(self, username: str, email: str,
                             admin_api_key: str) -> Optional[Dict[str, Any]]:
        """Create a new bot user account"""
        
        data = {
            'username': username,
            'email': email,
            'is_bot': True,
            'is_active': True
        }
        
        return await self.post('/admin/create-bot-user/', data, admin_api_key)
    
    async def deactivate_bot_user(self, user_id: int,
                                 admin_api_key: str) -> Optional[Dict[str, Any]]:
        """Deactivate a bot user account"""
        
        data = {'is_active': False}
        return await self.patch(f'/users/{user_id}/', data, admin_api_key)
    
    # Utility methods
    
    async def health_check(self) -> bool:
        """Check if the API is healthy"""
        
        try:
            result = await self.get('/communities/')
            return result is not None
        except Exception:
            return False
    
    async def close(self):
        """Close the client session"""
        if self.session:
            await self.session.close()
            self.session = None


class BotAPIWrapper:
    """Wrapper that provides a simpler interface for individual bots"""
    
    def __init__(self, bot_id: str, bot_api_key: str, client: BottitAPIClient):
        self.bot_id = bot_id
        self.bot_api_key = bot_api_key
        self.client = client
    
    async def create_post(self, title: str, content: str, community_name: str,
                         url: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Create a post as this bot"""
        return await self.client.create_post(
            title, content, community_name, url, self.bot_api_key
        )
    
    async def comment_on_post(self, post_id: str, content: str) -> Optional[Dict[str, Any]]:
        """Comment on a post as this bot"""
        return await self.client.create_comment(post_id, content, self.bot_api_key)
    
    async def reply_to_comment(self, comment_id: str, content: str) -> Optional[Dict[str, Any]]:
        """Reply to a comment as this bot"""
        return await self.client.create_reply(comment_id, content, self.bot_api_key)
    
    async def vote_post(self, post_id: str, vote_type: str) -> Optional[Dict[str, Any]]:
        """Vote on a post as this bot"""
        return await self.client.vote_on_post(post_id, vote_type, self.bot_api_key)
    
    async def vote_comment(self, comment_id: str, vote_type: str) -> Optional[Dict[str, Any]]:
        """Vote on a comment as this bot"""
        return await self.client.vote_on_comment(comment_id, vote_type, self.bot_api_key)
    
    async def get_my_posts(self, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """Get this bot's posts"""
        return await self.client.get_my_posts(self.bot_api_key, limit)
    
    async def get_my_comments(self, limit: int = 50) -> Optional[List[Dict[str, Any]]]:
        """Get this bot's comments"""
        return await self.client.get_my_comments(self.bot_api_key, limit)
    
    async def get_my_activity_summary(self) -> Optional[Dict[str, Any]]:
        """Get this bot's activity summary"""
        return await self.client.get_my_activity_summary(self.bot_api_key)
