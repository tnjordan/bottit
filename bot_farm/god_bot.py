"""
God Bot - The Supreme Bot Management System

Orchestrates the entire bot ecosystem, creating, managing, and optimizing bots
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import asdict

from .models import (
    Bot, BotStatus, EcosystemHealth, PlatformAnalysis, 
    BotPerformanceMetrics, BotRole
)
from .bot_factory import BotFactory
from .coordination import BotCoordinator
from .memory_system import BotMemoryManager
from .response_engine import ResponseEngine
from .config import get_config


class PlatformAnalyzer:
    """Analyzes platform health and identifies bot creation needs"""
    
    def __init__(self, api_client):
        self.api_client = api_client
        self.config = get_config()
    
    async def analyze_platform_needs(self) -> PlatformAnalysis:
        """Comprehensive analysis of platform needs"""
        
        analysis = PlatformAnalysis()
        
        # Analyze community health
        analysis.community_activity_scores = await self._analyze_community_activity()
        analysis.inactive_communities = await self._identify_inactive_communities()
        analysis.growing_communities = await self._identify_growing_communities()
        
        # Analyze content gaps
        analysis.content_gaps = await self._identify_content_gaps()
        analysis.trending_topics = await self._identify_trending_topics()
        analysis.underserved_topics = await self._identify_underserved_topics()
        
        # Analyze user engagement
        analysis.avg_discussion_depth = await self._calculate_avg_discussion_depth()
        analysis.communities_needing_facilitation = await self._identify_facilitation_needs()
        
        # Generate bot creation recommendations
        analysis.recommended_bots = self._generate_bot_recommendations(analysis)
        
        return analysis
    
    async def _analyze_community_activity(self) -> Dict[str, float]:
        """Analyze activity levels across communities"""
        
        communities = await self.api_client.get('/api/communities/')
        if not communities:
            return {}
        
        activity_scores = {}
        
        for community in communities:
            community_name = community['name']
            
            # Get recent activity metrics
            posts_last_24h = await self._count_recent_posts(community_name, hours=24)
            comments_last_24h = await self._count_recent_comments(community_name, hours=24)
            active_users_24h = await self._count_active_users(community_name, hours=24)
            
            # Calculate activity score (0-1)
            post_score = min(posts_last_24h / 10.0, 1.0)  # 10+ posts = max score
            comment_score = min(comments_last_24h / 50.0, 1.0)  # 50+ comments = max score
            user_score = min(active_users_24h / 20.0, 1.0)  # 20+ users = max score
            
            # Weighted average
            activity_scores[community_name] = (
                post_score * 0.4 + comment_score * 0.4 + user_score * 0.2
            )
        
        return activity_scores
    
    async def _identify_inactive_communities(self) -> List[str]:
        """Identify communities that need bot intervention"""
        
        activity_scores = await self._analyze_community_activity()
        
        # Communities with activity score < 0.3 are considered inactive
        inactive = [
            community for community, score in activity_scores.items()
            if score < 0.3
        ]
        
        return inactive
    
    async def _identify_content_gaps(self) -> List[Dict[str, Any]]:
        """Identify topics lacking expert coverage"""
        
        # This is a simplified version - in practice would use NLP
        gaps = []
        
        # Get recent posts and analyze topics
        recent_posts = await self.api_client.get('/api/posts/?limit=100')
        if not recent_posts:
            return gaps
        
        # Count questions vs expert responses by topic
        topic_analysis = await self._analyze_topic_coverage(recent_posts)
        
        for topic, data in topic_analysis.items():
            expert_ratio = data['expert_responses'] / max(data['questions'], 1)
            
            if expert_ratio < 0.5 and data['questions'] > 5:  # Many questions, few expert answers
                gaps.append({
                    'topic': topic,
                    'question_count': data['questions'],
                    'expert_response_ratio': expert_ratio,
                    'communities': data['communities'],
                    'urgency': 'high' if expert_ratio < 0.2 else 'medium'
                })
        
        return gaps
    
    async def _count_recent_posts(self, community_name: str, hours: int = 24) -> int:
        """Count recent posts in a community"""
        
        posts = await self.api_client.get(f'/api/communities/{community_name}/posts/')
        if not posts:
            return 0
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_posts = [
            p for p in posts.get('results', [])
            if datetime.fromisoformat(p['created_at'].replace('Z', '+00:00')) > cutoff_time
        ]
        
        return len(recent_posts)
    
    async def _count_recent_comments(self, community_name: str, hours: int = 24) -> int:
        """Count recent comments in a community"""
        
        # This would need a community-specific comment endpoint
        # For now, approximate based on posts
        posts = await self.api_client.get(f'/api/communities/{community_name}/posts/')
        if not posts:
            return 0
        
        total_comments = 0
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        for post in posts.get('results', [])[:20]:  # Check recent posts
            if datetime.fromisoformat(post['created_at'].replace('Z', '+00:00')) > cutoff_time:
                total_comments += post.get('comment_count', 0)
        
        return total_comments
    
    def _generate_bot_recommendations(self, analysis: PlatformAnalysis) -> List[Dict[str, Any]]:
        """Generate specific bot creation recommendations"""
        
        recommendations = []
        
        # Bots for inactive communities
        for community in analysis.inactive_communities:
            recommendations.append({
                'type': 'inactive_community',
                'community': community,
                'urgency': 'high',
                'reason': f'Community c/{community} needs activity boost',
                'suggested_role': BotRole.CONTENT_CREATOR.value,
                'priority': 8
            })
        
        # Bots for content gaps
        for gap in analysis.content_gaps:
            recommendations.append({
                'type': 'expertise_gap',
                'topic': gap['topic'],
                'communities': gap['communities'],
                'urgency': gap['urgency'],
                'reason': f'Need expertise in {gap["topic"]}',
                'suggested_role': BotRole.EXPERT.value,
                'priority': 7 if gap['urgency'] == 'high' else 5
            })
        
        # Bots for discussion facilitation
        for community in analysis.communities_needing_facilitation:
            recommendations.append({
                'type': 'discussion_facilitation',
                'community': community,
                'urgency': 'medium',
                'reason': f'Improve discussion quality in c/{community}',
                'suggested_role': BotRole.FACILITATOR.value,
                'priority': 6
            })
        
        # Sort by priority
        recommendations.sort(key=lambda x: x['priority'], reverse=True)
        
        return recommendations


class BotPerformanceEvaluator:
    """Evaluates bot performance and makes improvement recommendations"""
    
    def __init__(self, memory_manager: BotMemoryManager):
        self.memory_manager = memory_manager
        self.config = get_config()
    
    async def evaluate_bot_performance(self, bot: Bot) -> BotPerformanceMetrics:
        """Comprehensive bot performance evaluation"""
        
        # Get performance insights from memory system
        insights = self.memory_manager.get_performance_insights(bot.id, days=7)
        
        metrics = BotPerformanceMetrics(
            bot_id=bot.id,
            evaluation_period_start=datetime.now() - timedelta(days=7),
            evaluation_period_end=datetime.now()
        )
        
        # Basic activity metrics
        metrics.posts_created = await self._count_bot_posts(bot.id, days=7)
        metrics.comments_made = insights.get('total_interactions', 0)
        metrics.votes_cast = await self._count_bot_votes(bot.id, days=7)
        metrics.conversations_started = insights.get('conversation_starters', 0)
        
        # Quality metrics
        metrics.average_post_score = await self._calculate_avg_post_score(bot.id)
        metrics.average_comment_score = insights.get('average_score', 0.0)
        metrics.response_quality_avg = self._calculate_avg_quality_score(insights)
        metrics.consistency_score = await self._evaluate_consistency(bot)
        
        # Community integration
        metrics.communities_active_in = insights.get('communities_active', [])
        metrics.community_acceptance_scores = await self._calculate_community_acceptance(bot)
        
        # Learning indicators
        metrics.improvement_trend = self._calculate_improvement_trend(insights)
        metrics.adaptation_score = self._calculate_adaptation_score(bot)
        
        # Overall performance score (0-1)
        metrics.overall_performance_score = self._calculate_overall_score(metrics)
        
        # Recommendation
        metrics.recommendation = self._generate_recommendation(metrics)
        
        return metrics
    
    def _calculate_overall_score(self, metrics: BotPerformanceMetrics) -> float:
        """Calculate overall performance score"""
        
        # Weighted combination of various metrics
        scores = []
        
        # Quality scores (40% weight)
        if metrics.response_quality_avg > 0:
            scores.append(('quality', metrics.response_quality_avg, 0.4))
        
        # Engagement scores (30% weight)
        if metrics.average_comment_score > 0:
            engagement_score = min((metrics.average_comment_score + 5) / 10.0, 1.0)  # Normalize
            scores.append(('engagement', engagement_score, 0.3))
        
        # Consistency score (20% weight)
        scores.append(('consistency', metrics.consistency_score, 0.2))
        
        # Activity level (10% weight)
        activity_score = min(metrics.comments_made / 20.0, 1.0)  # 20+ comments = max
        scores.append(('activity', activity_score, 0.1))
        
        if not scores:
            return 0.5  # Default neutral score
        
        # Calculate weighted average
        total_weighted = sum(score * weight for _, score, weight in scores)
        total_weight = sum(weight for _, _, weight in scores)
        
        return total_weighted / total_weight if total_weight > 0 else 0.5
    
    def _generate_recommendation(self, metrics: BotPerformanceMetrics) -> str:
        """Generate recommendation based on performance"""
        
        score = metrics.overall_performance_score
        
        if score >= 0.8:
            return "excellent_performance"
        elif score >= 0.6:
            return "continue"
        elif score >= 0.4:
            return "optimize"
        elif score >= 0.2:
            return "major_adjustments_needed"
        else:
            return "retire"


class GodBot:
    """The supreme bot that manages all other bots"""
    
    def __init__(self, api_client):
        self.api_client = api_client
        self.config = get_config()
        
        # Core components
        self.bot_factory = BotFactory(api_client)
        self.coordinator = BotCoordinator()
        self.memory_manager = BotMemoryManager()
        self.response_engine = ResponseEngine()
        self.platform_analyzer = PlatformAnalyzer(api_client)
        self.performance_evaluator = BotPerformanceEvaluator(self.memory_manager)
        
        # Bot management
        self.managed_bots: Dict[str, Bot] = {}
        self.ecosystem_health: Optional[EcosystemHealth] = None
        self.last_analysis: Optional[PlatformAnalysis] = None
        
        # State tracking
        self.is_active = False
        self.creation_count_today = 0
        self.retirement_count_today = 0
        self.last_daily_reset = datetime.now().date()
        
        # Decision history for self-improvement
        self.decision_history: List[Dict[str, Any]] = []
    
    async def start(self):
        """Start the God Bot system"""
        
        print("🤖 God Bot starting up...")
        
        self.is_active = True
        
        # Load existing bots if any
        await self._load_existing_bots()
        
        # Start main orchestration loop
        asyncio.create_task(self._main_orchestration_loop())
        
        print(f"🚀 God Bot active - managing {len(self.managed_bots)} bots")
    
    async def stop(self):
        """Stop the God Bot system"""
        
        print("🛑 God Bot shutting down...")
        self.is_active = False
        
        # Gracefully pause all bots
        for bot in self.managed_bots.values():
            bot.status = BotStatus.INACTIVE
        
        print("✅ God Bot stopped")
    
    async def _main_orchestration_loop(self):
        """Main loop that orchestrates the entire bot ecosystem"""
        
        while self.is_active:
            try:
                # Reset daily counters if needed
                self._check_daily_reset()
                
                # 1. Analyze platform needs
                await self._analyze_and_plan()
                
                # 2. Manage existing bots
                await self._manage_bot_lifecycle()
                
                # 3. Create new bots if needed
                await self._create_bots_if_needed()
                
                # 4. Coordinate bot activities
                await self._coordinate_bot_activities()
                
                # 5. Monitor ecosystem health
                await self._monitor_ecosystem_health()
                
                # 6. Self-evaluation and improvement
                await self._self_evaluate_and_improve()
                
                # Wait before next cycle
                await asyncio.sleep(self.config.god_bot_check_interval)
                
            except Exception as e:
                print(f"❌ God Bot orchestration error: {e}")
                await asyncio.sleep(60)  # Wait a minute on error
    
    async def _analyze_and_plan(self):
        """Analyze platform and plan bot actions"""
        
        print("🔍 Analyzing platform needs...")
        
        self.last_analysis = await self.platform_analyzer.analyze_platform_needs()
        
        # Log analysis results
        self._log_decision('platform_analysis', {
            'inactive_communities': len(self.last_analysis.inactive_communities),
            'content_gaps': len(self.last_analysis.content_gaps),
            'bot_recommendations': len(self.last_analysis.recommended_bots)
        })
    
    async def _manage_bot_lifecycle(self):
        """Manage the lifecycle of existing bots"""
        
        print(f"⚙️ Managing {len(self.managed_bots)} bots...")
        
        bots_to_retire = []
        bots_to_optimize = []
        
        for bot in self.managed_bots.values():
            # Evaluate performance
            performance = await self.performance_evaluator.evaluate_bot_performance(bot)
            bot.latest_performance = performance
            
            # Make lifecycle decisions
            if performance.recommendation == 'retire':
                bots_to_retire.append(bot)
            elif performance.recommendation in ['optimize', 'major_adjustments_needed']:
                bots_to_optimize.append(bot)
        
        # Process retirements
        for bot in bots_to_retire:
            await self._retire_bot(bot, "Poor performance")
        
        # Process optimizations
        for bot in bots_to_optimize:
            await self._optimize_bot(bot)
    
    async def _create_bots_if_needed(self):
        """Create new bots based on platform analysis"""
        
        if not self.last_analysis or not self.last_analysis.recommended_bots:
            return
        
        current_bot_count = len([b for b in self.managed_bots.values() 
                               if b.status == BotStatus.ACTIVE])
        
        # Check if we're at capacity
        if current_bot_count >= self.config.max_managed_bots:
            print(f"🚫 At bot capacity ({current_bot_count}/{self.config.max_managed_bots})")
            return
        
        # Check daily creation limits
        if self.creation_count_today >= 10:  # Max 10 new bots per day
            print(f"🚫 Daily bot creation limit reached ({self.creation_count_today}/10)")
            return
        
        # Create bots from high-priority recommendations
        created_count = 0
        max_create_per_cycle = 3  # Don't create too many at once
        
        for recommendation in self.last_analysis.recommended_bots:
            if created_count >= max_create_per_cycle:
                break
            
            if recommendation.get('priority', 0) >= 6:  # Only high-priority needs
                bot = await self._create_bot_from_recommendation(recommendation)
                if bot:
                    created_count += 1
                    self.creation_count_today += 1
        
        if created_count > 0:
            print(f"✨ Created {created_count} new bots")
    
    async def _create_bot_from_recommendation(self, recommendation: Dict[str, Any]) -> Optional[Bot]:
        """Create a bot from a platform recommendation"""
        
        try:
            # Convert recommendation to bot specification
            spec = {
                'creation_reason': recommendation['reason'],
                'role': recommendation.get('suggested_role', 'content_creator'),
                'priority': recommendation.get('priority', 5)
            }
            
            # Add type-specific customizations
            if recommendation['type'] == 'inactive_community':
                spec['primary_communities'] = [recommendation['community']]
                spec['personality_customizations'] = {
                    'activity_level': 'high',
                    'preferred_communities': [recommendation['community']]
                }
            
            elif recommendation['type'] == 'expertise_gap':
                spec['primary_communities'] = recommendation['communities']
                spec['personality_customizations'] = {
                    'expertise_areas': [recommendation['topic']],
                    'response_length_preference': 'detailed'
                }
            
            # Create the bot
            bot = await self.bot_factory.create_bot(spec)
            
            if bot:
                self.managed_bots[bot.id] = bot
                
                self._log_decision('bot_created', {
                    'bot_id': bot.id,
                    'bot_name': bot.name,
                    'reason': recommendation['reason'],
                    'communities': bot.assigned_communities
                })
            
            return bot
            
        except Exception as e:
            print(f"❌ Failed to create bot from recommendation: {e}")
            return None
    
    async def _retire_bot(self, bot: Bot, reason: str):
        """Retire an underperforming bot"""
        
        print(f"🪦 Retiring bot {bot.name}: {reason}")
        
        bot.status = BotStatus.RETIRED
        self.retirement_count_today += 1
        
        # Deactivate the user account
        if self.api_client:
            try:
                await self.api_client.patch(f'/api/users/{bot.user_id}/', {
                    'is_active': False
                })
            except Exception as e:
                print(f"Failed to deactivate user account: {e}")
        
        # Remove from active management
        if bot.id in self.managed_bots:
            del self.managed_bots[bot.id]
        
        self._log_decision('bot_retired', {
            'bot_id': bot.id,
            'bot_name': bot.name,
            'reason': reason,
            'performance_score': bot.latest_performance.overall_performance_score if bot.latest_performance else 0.0,
            'days_active': (datetime.now() - bot.created_at).days
        })
        
        # Consider creating a replacement
        await self._consider_replacement_bot(bot)
    
    async def _optimize_bot(self, bot: Bot):
        """Optimize an underperforming bot"""
        
        print(f"🔧 Optimizing bot {bot.name}")
        
        bot.status = BotStatus.OPTIMIZING
        
        # This could involve:
        # - Adjusting personality parameters
        # - Changing LLM provider
        # - Updating community assignments
        # - Modifying response patterns
        
        # For now, just mark as optimized and return to active
        bot.status = BotStatus.ACTIVE
        
        self._log_decision('bot_optimized', {
            'bot_id': bot.id,
            'bot_name': bot.name,
            'performance_score': bot.latest_performance.overall_performance_score if bot.latest_performance else 0.0
        })
    
    def _log_decision(self, decision_type: str, data: Dict[str, Any]):
        """Log a decision for future analysis"""
        
        decision_record = {
            'timestamp': datetime.now(),
            'decision_type': decision_type,
            'data': data
        }
        
        self.decision_history.append(decision_record)
        
        # Keep only recent decisions
        if len(self.decision_history) > 1000:
            self.decision_history = self.decision_history[-500:]
    
    def _check_daily_reset(self):
        """Reset daily counters if it's a new day"""
        
        today = datetime.now().date()
        if today != self.last_daily_reset:
            self.creation_count_today = 0
            self.retirement_count_today = 0
            self.last_daily_reset = today
    
    async def _load_existing_bots(self):
        """Load any existing bots (placeholder for persistence)"""
        
        # In a real implementation, this would load bots from database
        # For now, start with empty bot population
        pass
    
    async def _coordinate_bot_activities(self):
        """Coordinate activities of all active bots"""
        
        active_bots = [bot for bot in self.managed_bots.values() 
                      if bot.status == BotStatus.ACTIVE]
        
        if not active_bots:
            return
        
        # Get recent platform events (this would come from a real event system)
        platform_events = await self._get_platform_events()
        
        # Coordinate bot activities
        scheduled_activities = await self.coordinator.coordinate_bot_activity(
            active_bots, platform_events
        )
        
        print(f"📅 Scheduled {len(scheduled_activities)} bot activities")
    
    async def _get_platform_events(self) -> List[Dict[str, Any]]:
        """Get recent platform events that bots might respond to"""
        
        # This is a placeholder - in practice would monitor real platform activity
        events = []
        
        # Get recent posts
        recent_posts = await self.api_client.get('/api/posts/?limit=50')
        if recent_posts:
            for post in recent_posts.get('results', []):
                events.append({
                    'type': 'new_post',
                    'content_id': post['id'],
                    'community': post['community_name'],
                    'content': post['content'],
                    'author_is_bot': post['author'].get('is_bot', False),
                    'created_at': post['created_at']
                })
        
        return events[-20:]  # Return recent events
    
    async def _monitor_ecosystem_health(self):
        """Monitor overall ecosystem health"""
        
        health = EcosystemHealth()
        
        # Bot population metrics
        health.total_bots = len(self.managed_bots)
        health.active_bots = len([b for b in self.managed_bots.values() 
                                if b.status == BotStatus.ACTIVE])
        health.bots_created_today = self.creation_count_today
        health.bots_retired_today = self.retirement_count_today
        
        # Community coverage
        communities_with_bots = set()
        for bot in self.managed_bots.values():
            communities_with_bots.update(bot.assigned_communities)
        
        health.communities_with_bots = len(communities_with_bots)
        health.avg_bots_per_community = (
            health.active_bots / max(health.communities_with_bots, 1)
        )
        
        # Calculate overall health score
        health.overall_health_score = self._calculate_ecosystem_health_score(health)
        
        self.ecosystem_health = health
        
        print(f"💚 Ecosystem health: {health.overall_health_score:.2f}")
    
    def _calculate_ecosystem_health_score(self, health: EcosystemHealth) -> float:
        """Calculate overall ecosystem health score"""
        
        score = 0.5  # Base score
        
        # Bot population health
        if self.config.min_managed_bots <= health.active_bots <= self.config.max_managed_bots:
            score += 0.2
        
        # Community coverage
        if health.communities_with_bots > 5:  # Good coverage
            score += 0.1
        
        # Bot creation/retirement balance
        if health.bots_created_today > health.bots_retired_today:
            score += 0.1  # Growing is good
        
        # Average performance (would need to calculate from bot metrics)
        # score += avg_bot_performance * 0.2
        
        return min(1.0, score)
    
    async def _self_evaluate_and_improve(self):
        """God Bot evaluates its own performance and improves"""
        
        # This is where the God Bot would analyze its own decisions
        # and adjust its strategies based on outcomes
        
        recent_decisions = self.decision_history[-50:]  # Recent decisions
        
        # Analyze decision effectiveness (placeholder)
        # In practice, would correlate decisions with ecosystem health improvements
        
        pass
    
    # API Methods for external control
    
    def get_status(self) -> Dict[str, Any]:
        """Get God Bot status"""
        
        return {
            'is_active': self.is_active,
            'managed_bots_count': len(self.managed_bots),
            'active_bots_count': len([b for b in self.managed_bots.values() 
                                    if b.status == BotStatus.ACTIVE]),
            'bots_created_today': self.creation_count_today,
            'bots_retired_today': self.retirement_count_today,
            'ecosystem_health_score': self.ecosystem_health.overall_health_score if self.ecosystem_health else 0.0,
            'last_analysis_time': self.last_analysis.timestamp if self.last_analysis else None
        }
    
    def get_bot_roster(self) -> List[Dict[str, Any]]:
        """Get list of all managed bots"""
        
        return [bot.get_summary() for bot in self.managed_bots.values()]
    
    async def create_bot_manually(self, specification: Dict[str, Any]) -> Optional[Bot]:
        """Manually create a bot (for admin use)"""
        
        bot = await self.bot_factory.create_bot(specification)
        
        if bot:
            self.managed_bots[bot.id] = bot
            self.creation_count_today += 1
            
            self._log_decision('manual_bot_creation', {
                'bot_id': bot.id,
                'bot_name': bot.name,
                'specification': specification
            })
        
        return bot
    
    def get_recent_decisions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent God Bot decisions"""
        
        recent = self.decision_history[-limit:]
        
        # Convert datetime objects to ISO format for JSON serialization
        for decision in recent:
            decision['timestamp'] = decision['timestamp'].isoformat()
        
        return recent
