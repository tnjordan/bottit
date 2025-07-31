"""
Bot Memory System

Handles bot memory storage, retrieval, and learning from interactions
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import sqlite3
import os
from dataclasses import asdict

from .models import BotMemoryEntry, BotInteraction, Bot
from .config import get_config


class BotMemoryStorage:
    """Handles persistent storage of bot memories"""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.path.join(os.getcwd(), 'bot_farm_memory.db')
        
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the memory database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Bot memories table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bot_memories (
                    id TEXT PRIMARY KEY,
                    bot_id TEXT NOT NULL,
                    topic TEXT,
                    community TEXT,
                    interaction_summary TEXT,
                    learned_preferences TEXT,  -- JSON
                    success_indicators TEXT,   -- JSON
                    importance_score REAL,
                    timestamp TEXT
                )
            ''')
            
            # Create indexes for bot_memories
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_bot_memories_bot_id ON bot_memories(bot_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_bot_memories_topic ON bot_memories(topic)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_bot_memories_community ON bot_memories(community)')
            
            # Bot interactions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bot_interactions (
                    id TEXT PRIMARY KEY,
                    bot_id TEXT NOT NULL,
                    interaction_type TEXT,
                    content_id TEXT,
                    community_name TEXT,
                    content_text TEXT,
                    response_text TEXT,
                    context_used TEXT,  -- JSON
                    quality_score REAL,
                    vote_score INTEGER,
                    replies_generated INTEGER,
                    success_metrics TEXT,  -- JSON
                    timestamp TEXT
                )
            ''')
            
            # Create indexes for bot_interactions
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_bot_interactions_bot_id ON bot_interactions(bot_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_bot_interactions_community ON bot_interactions(community_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_bot_interactions_timestamp ON bot_interactions(timestamp)')
            
            conn.commit()
    
    def store_memory(self, memory: BotMemoryEntry):
        """Store a memory entry"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO bot_memories 
                (id, bot_id, topic, community, interaction_summary, 
                 learned_preferences, success_indicators, importance_score, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                memory.id, memory.bot_id, memory.topic, memory.community,
                memory.interaction_summary, json.dumps(memory.learned_preferences),
                json.dumps(memory.success_indicators), memory.importance_score,
                memory.timestamp.isoformat()
            ))
            conn.commit()
    
    def get_memories(self, bot_id: str, limit: int = 50, 
                     topic: Optional[str] = None, 
                     community: Optional[str] = None) -> List[BotMemoryEntry]:
        """Retrieve memories for a bot"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = 'SELECT * FROM bot_memories WHERE bot_id = ?'
            params = [bot_id]
            
            if topic:
                query += ' AND topic = ?'
                params.append(topic)
            
            if community:
                query += ' AND community = ?'
                params.append(community)
            
            query += ' ORDER BY importance_score DESC, timestamp DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            memories = []
            for row in rows:
                memories.append(BotMemoryEntry(
                    id=row[0], bot_id=row[1], topic=row[2], community=row[3],
                    interaction_summary=row[4],
                    learned_preferences=json.loads(row[5]),
                    success_indicators=json.loads(row[6]),
                    importance_score=row[7],
                    timestamp=datetime.fromisoformat(row[8])
                ))
            
            return memories
    
    def store_interaction(self, interaction: BotInteraction):
        """Store an interaction record"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO bot_interactions 
                (id, bot_id, interaction_type, content_id, community_name,
                 content_text, response_text, context_used, quality_score,
                 vote_score, replies_generated, success_metrics, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                interaction.id, interaction.bot_id, interaction.interaction_type.value,
                interaction.content_id, interaction.community_name,
                interaction.content_text, interaction.response_text,
                json.dumps(interaction.context_used), interaction.quality_score,
                interaction.vote_score, interaction.replies_generated,
                json.dumps(interaction.success_metrics), interaction.timestamp.isoformat()
            ))
            conn.commit()
    
    def get_interactions(self, bot_id: str, limit: int = 100,
                        community: Optional[str] = None,
                        since: Optional[datetime] = None) -> List[BotInteraction]:
        """Retrieve interaction history for a bot"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = 'SELECT * FROM bot_interactions WHERE bot_id = ?'
            params = [bot_id]
            
            if community:
                query += ' AND community_name = ?'
                params.append(community)
            
            if since:
                query += ' AND timestamp > ?'
                params.append(since.isoformat())
            
            query += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            from .models import InteractionType
            
            interactions = []
            for row in rows:
                interactions.append(BotInteraction(
                    id=row[0], bot_id=row[1],
                    interaction_type=InteractionType(row[2]),
                    content_id=row[3], community_name=row[4],
                    content_text=row[5], response_text=row[6],
                    context_used=json.loads(row[7]), quality_score=row[8],
                    vote_score=row[9], replies_generated=row[10],
                    success_metrics=json.loads(row[11]),
                    timestamp=datetime.fromisoformat(row[12])
                ))
            
            return interactions
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Remove old memory and interaction data"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Keep high-importance memories longer
            cursor.execute('''
                DELETE FROM bot_memories 
                WHERE timestamp < ? AND importance_score < 0.7
            ''', (cutoff_date.isoformat(),))
            
            # Clean up old interactions
            cursor.execute('''
                DELETE FROM bot_interactions 
                WHERE timestamp < ?
            ''', (cutoff_date.isoformat(),))
            
            conn.commit()


class BotMemoryManager:
    """High-level memory management for bots"""
    
    def __init__(self, storage: Optional[BotMemoryStorage] = None):
        self.storage = storage or BotMemoryStorage()
        self.config = get_config()
    
    def learn_from_interaction(self, bot: Bot, interaction: BotInteraction, 
                             outcome_metrics: Dict[str, Any]):
        """Learn from a bot interaction and update memory"""
        
        # Store the interaction
        interaction.success_metrics = outcome_metrics
        self.storage.store_interaction(interaction)
        
        # Extract learning insights
        insights = self._extract_learning_insights(interaction, outcome_metrics)
        
        if insights:
            # Create or update memory entry
            memory = self._create_memory_entry(bot.id, interaction, insights)
            self.storage.store_memory(memory)
            
            # Update bot's in-memory cache
            bot.memory_entries.append(memory)
            if len(bot.memory_entries) > self.config.max_conversation_history:
                bot.memory_entries = bot.memory_entries[-self.config.max_conversation_history:]
    
    def _extract_learning_insights(self, interaction: BotInteraction, 
                                 outcome_metrics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract learning insights from an interaction"""
        
        # Determine if this was a successful interaction
        success_indicators = {}
        
        # Vote-based success
        if interaction.vote_score > 2:
            success_indicators['positive_reception'] = True
            success_indicators['vote_quality'] = min(interaction.vote_score / 10.0, 1.0)
        elif interaction.vote_score < -1:
            success_indicators['negative_reception'] = True
            success_indicators['vote_quality'] = max(interaction.vote_score / 10.0, -1.0)
        
        # Reply-based success
        if interaction.replies_generated > 1:
            success_indicators['conversation_starter'] = True
            success_indicators['engagement_level'] = min(interaction.replies_generated / 5.0, 1.0)
        
        # Quality-based success
        if interaction.quality_score and interaction.quality_score > 0.8:
            success_indicators['high_quality'] = True
        elif interaction.quality_score and interaction.quality_score < 0.4:
            success_indicators['low_quality'] = True
        
        # Only create memory if there's something significant to learn
        if success_indicators:
            return {
                'topic_performance': self._analyze_topic_performance(interaction),
                'community_fit': self._analyze_community_fit(interaction),
                'communication_effectiveness': self._analyze_communication_style(interaction),
                'success_indicators': success_indicators
            }
        
        return None
    
    def _create_memory_entry(self, bot_id: str, interaction: BotInteraction,
                           insights: Dict[str, Any]) -> BotMemoryEntry:
        """Create a memory entry from interaction and insights"""
        
        # Determine topic from content
        topic = self._extract_topic(interaction.content_text + " " + interaction.response_text)
        
        # Create summary
        summary = f"Discussed {topic} in c/{interaction.community_name}"
        if insights['success_indicators'].get('positive_reception'):
            summary += " - well received"
        elif insights['success_indicators'].get('conversation_starter'):
            summary += " - sparked discussion"
        
        # Calculate importance score
        importance = self._calculate_importance_score(insights)
        
        return BotMemoryEntry(
            bot_id=bot_id,
            topic=topic,
            community=interaction.community_name,
            interaction_summary=summary,
            learned_preferences=insights,
            success_indicators=insights['success_indicators'],
            importance_score=importance
        )
    
    def _analyze_topic_performance(self, interaction: BotInteraction) -> Dict[str, Any]:
        """Analyze how well the bot performed on this topic"""
        return {
            'topic_keywords': self._extract_keywords(interaction.content_text),
            'response_relevance': interaction.quality_score or 0.5,
            'audience_engagement': interaction.replies_generated
        }
    
    def _analyze_community_fit(self, interaction: BotInteraction) -> Dict[str, Any]:
        """Analyze how well the bot fits in this community"""
        return {
            'community': interaction.community_name,
            'reception_score': interaction.vote_score,
            'discussion_generation': interaction.replies_generated > 0
        }
    
    def _analyze_communication_style(self, interaction: BotInteraction) -> Dict[str, Any]:
        """Analyze the effectiveness of the communication style used"""
        return {
            'response_length': len(interaction.response_text.split()),
            'engagement_achieved': interaction.replies_generated,
            'quality_perceived': interaction.quality_score or 0.5
        }
    
    def _extract_topic(self, text: str) -> str:
        """Extract main topic from text (simplified)"""
        # This is a simplified version - in production you'd use NLP
        words = text.lower().split()
        
        # Common technical terms
        tech_terms = ['python', 'javascript', 'programming', 'code', 'software', 'web', 'api']
        if any(term in words for term in tech_terms):
            return 'technology'
        
        # Philosophy terms
        phil_terms = ['philosophy', 'ethics', 'moral', 'meaning', 'existence', 'truth']
        if any(term in words for term in phil_terms):
            return 'philosophy'
        
        # Default to general
        return 'general_discussion'
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text (simplified)"""
        # Simplified keyword extraction
        words = text.lower().split()
        # Filter out common words
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
        keywords = [word for word in words if len(word) > 3 and word not in common_words]
        return keywords[:10]  # Top 10 keywords
    
    def _calculate_importance_score(self, insights: Dict[str, Any]) -> float:
        """Calculate how important this memory is to retain"""
        score = 0.5  # Base score
        
        success_indicators = insights.get('success_indicators', {})
        
        # Positive interactions are more important
        if success_indicators.get('positive_reception'):
            score += 0.3
        
        # Conversation starters are valuable
        if success_indicators.get('conversation_starter'):
            score += 0.2
        
        # High quality responses are important
        if success_indicators.get('high_quality'):
            score += 0.2
        
        # Negative interactions are also important to learn from
        if success_indicators.get('negative_reception'):
            score += 0.1
        
        return min(score, 1.0)
    
    def get_relevant_context(self, bot_id: str, current_topic: str, 
                           community: str, limit: int = 5) -> List[BotMemoryEntry]:
        """Get relevant memories for current context"""
        
        # Get memories for this topic and community
        topic_memories = self.storage.get_memories(bot_id, limit=limit, topic=current_topic)
        community_memories = self.storage.get_memories(bot_id, limit=limit, community=community)
        
        # Combine and deduplicate
        all_memories = topic_memories + community_memories
        seen_ids = set()
        unique_memories = []
        
        for memory in all_memories:
            if memory.id not in seen_ids:
                unique_memories.append(memory)
                seen_ids.add(memory.id)
        
        # Sort by importance and recency
        unique_memories.sort(key=lambda m: (m.importance_score, m.timestamp), reverse=True)
        
        return unique_memories[:limit]
    
    def get_performance_insights(self, bot_id: str, days: int = 7) -> Dict[str, Any]:
        """Get performance insights for a bot"""
        since = datetime.now() - timedelta(days=days)
        interactions = self.storage.get_interactions(bot_id, since=since)
        
        if not interactions:
            return {'total_interactions': 0}
        
        # Calculate metrics
        total_score = sum(i.vote_score for i in interactions)
        avg_score = total_score / len(interactions)
        
        positive_interactions = [i for i in interactions if i.vote_score > 0]
        negative_interactions = [i for i in interactions if i.vote_score < 0]
        
        communities = list(set(i.community_name for i in interactions))
        
        return {
            'total_interactions': len(interactions),
            'average_score': avg_score,
            'positive_ratio': len(positive_interactions) / len(interactions),
            'negative_ratio': len(negative_interactions) / len(interactions),
            'communities_active': communities,
            'conversation_starters': sum(1 for i in interactions if i.replies_generated > 1),
            'quality_scores': [i.quality_score for i in interactions if i.quality_score is not None]
        }
