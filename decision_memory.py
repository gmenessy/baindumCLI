import asyncio
import math
import random
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

class DecisionEpisode(BaseModel):
    episode_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_context: Dict[str, Any]
    strategy_used: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class OutcomeFeedback(BaseModel):
    episode_id: str
    success: bool
    efficiency_score: float = Field(ge=0.0, le=1.0, description="0.0 to 1.0, higher is better")
    user_feedback_score: Optional[float] = Field(None, ge=-1.0, le=1.0)
    error_logs: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def final_reward(self) -> float:
        # Calculate a final reward between -1.0 and 1.0
        base = 1.0 if self.success else -1.0
        efficiency_modifier = (self.efficiency_score - 0.5) * 0.5 # +/- 0.25

        reward = base + efficiency_modifier

        if self.user_feedback_score is not None:
            # User feedback has high weight
            reward = (reward * 0.5) + (self.user_feedback_score * 0.5)

        return max(-1.0, min(1.0, reward))

class StrategyMemory(BaseModel):
    strategy_id: str
    description: str
    usage_count: int = 0
    confidence_score: float = 0.5  # Starts neutral
    last_used: Optional[datetime] = None
    success_rate: float = 0.0
    successful_uses: int = 0

class DecisionMemoryService:
    def __init__(self):
        # In-memory mock for the VFS/DB
        self.episodes: Dict[str, DecisionEpisode] = {}
        self.strategies: Dict[str, StrategyMemory] = {}

    def register_strategy(self, strategy_id: str, description: str):
        if strategy_id not in self.strategies:
            self.strategies[strategy_id] = StrategyMemory(
                strategy_id=strategy_id,
                description=description
            )

    async def record_decision(self, task_context: Dict[str, Any], strategy_id: str) -> str:
        """Records a new decision episode."""
        if strategy_id not in self.strategies:
            self.register_strategy(strategy_id, "Auto-registered strategy")

        episode = DecisionEpisode(
            task_context=task_context,
            strategy_used=strategy_id
        )
        self.episodes[episode.episode_id] = episode

        # Update strategy usage
        strategy = self.strategies[strategy_id]
        strategy.usage_count += 1
        strategy.last_used = datetime.now(timezone.utc)

        return episode.episode_id

    async def record_outcome(self, feedback: OutcomeFeedback):
        """Records the outcome of an episode and updates the strategy's confidence."""
        if feedback.episode_id not in self.episodes:
            raise ValueError(f"Episode {feedback.episode_id} not found.")

        episode = self.episodes[feedback.episode_id]
        strategy_id = episode.strategy_used
        strategy = self.strategies[strategy_id]

        reward = feedback.final_reward

        # Update success rate
        if feedback.success:
            strategy.successful_uses += 1
        strategy.success_rate = strategy.successful_uses / max(1, strategy.usage_count)

        # Exponential moving average for confidence update
        # Learning rate alpha determines how quickly new information replaces old
        alpha = 0.2

        # Map reward (-1 to 1) to confidence (0 to 1) roughly
        target_confidence = (reward + 1.0) / 2.0

        strategy.confidence_score = (1 - alpha) * strategy.confidence_score + alpha * target_confidence

    async def recommend_strategy(self, task_context: Dict[str, Any]) -> str:
        """
        Recommends a strategy using an Epsilon-Greedy approach for Exploration vs. Exploitation.
        """
        if not self.strategies:
            raise ValueError("No strategies registered.")

        # Epsilon dictates exploration rate (e.g., 10% of the time, pick randomly)
        epsilon = 0.1

        if random.random() < epsilon:
            # Exploration: Pick a random strategy
            return random.choice(list(self.strategies.keys()))
        else:
            # Exploitation: Pick the highest confidence strategy
            # In a real system, we would filter by task_context relevance first
            best_strategy = max(self.strategies.values(), key=lambda s: s.confidence_score)
            return best_strategy.strategy_id

    async def export_for_deepdream(self, confidence_threshold: float = 0.8) -> List[Dict[str, Any]]:
        """
        Exports successful strategies to the Dream Engine (Deepdream) for DNA integration.
        Includes a randomized aspect to introduce controlled mutations or prevent local optima.
        """
        export_candidates = []

        for strategy in self.strategies.values():
            if strategy.confidence_score >= confidence_threshold:
                # Base export data
                export_data = {
                    "strategy_id": strategy.strategy_id,
                    "description": strategy.description,
                    "confidence": strategy.confidence_score,
                    "success_rate": strategy.success_rate,
                    "mutation_flag": False
                }

                # Randomized Aspect: 15% chance to flag for mutation in Deepdream
                # This signals the Dream Engine to try a variation of this rule.
                if random.random() < 0.15:
                    export_data["mutation_flag"] = True
                    export_data["mutation_reason"] = "Prevent local optima"

                export_candidates.append(export_data)

        return export_candidates
