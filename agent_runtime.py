import hashlib
from datetime import datetime, timezone
from typing import Dict, Any

from brain_vfs import BrainVFS, VFSNode
from retriever import BrainRetriever
from policy_engine import PolicyEngine
from tool_router import ToolRouter
from decision_memory import DecisionMemoryService, DecisionEpisode, OutcomeFeedback

class MockDreamEngine:
    """Mock for the asynchronous learning service."""
    def run_daydream(self):
        print("☁️ [Daydream] Extracted fragments and promoted wikis.")

class AgentRuntime:
    """The central Execution Kernel of BrainDump."""

    def __init__(
        self,
        retriever: BrainRetriever,
        policy_engine: PolicyEngine,
        decision_memory: DecisionMemoryService,
        dream_engine: MockDreamEngine,
        vfs: BrainVFS,
        tool_router: ToolRouter,
    ):
        self.retriever = retriever
        self.policy_engine = policy_engine
        self.decision_memory = decision_memory
        self.dream_engine = dream_engine
        self.vfs = vfs
        self.tool_router = tool_router

    async def run_task(self, task_input: str) -> Dict[str, Any]:
        """Executes the complete Cognitive Agent Loop."""
        print(f"\n🧠 [AgentRuntime] Starting Task: '{task_input}'")

        # 1. Input -> Retrieve
        print("🔍 Retrieving context (fRAG)...")
        context = self.retriever.retrieve(task_input)

        # 2. Retrieve -> Policy -> Execution Plan
        print("📜 Evaluating policies...")
        task_context = {"query": task_input, "context": context}
        execution_plan = self.policy_engine.apply(task_context)

        # 3. Execution Plan -> Tool Dispatch
        result = self.tool_router.execute(execution_plan)

        # 4. Result -> Post Processing (Decision, Reward, Dump, Dream)
        await self._post_process(task_input, context, execution_plan, result)

        return result

    async def _post_process(self, task_input: str, context: Any, execution_plan: Dict[str, Any], result: Dict[str, Any]):

        # A. Decision Recording
        print("⚖️ Recording decision and generating reward...")

        # We need a strategy ID for the decision memory; we'll hash the execution plan steps
        strategy_id = "strat_" + hashlib.md5(str(execution_plan.get("steps")).encode()).hexdigest()[:8]

        episode_id = await self.decision_memory.record_decision(
            task_context={"query": task_input},
            strategy_id=strategy_id
        )

        # Calculate mock reward (simulating user/system feedback)
        success = result.get("status") == "success"
        feedback = OutcomeFeedback(
            episode_id=episode_id,
            success=success,
            efficiency_score=0.8
        )
        await self.decision_memory.record_outcome(feedback)

        # B. Dump Writing
        print("💾 Writing raw dump to VFS...")
        dump_path = f"vfs://dumps/session/{datetime.now(timezone.utc).strftime('%Y-%m-%d')}/task-{episode_id[:4]}"

        dump_content = {
            "input": task_input,
            "plan": execution_plan,
            "result": result
        }

        self.vfs.write(VFSNode(
            path=dump_path,
            layer="dumps",
            content=dump_content
        ))

        # C. Daydream Trigger
        self.dream_engine.run_daydream()
