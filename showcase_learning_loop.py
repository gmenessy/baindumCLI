import asyncio
from brain_vfs import BrainVFS, SQLiteBackend, VFSNode
from retriever import BrainRetriever
from policy_engine import PolicyEngine
from tool_router import ToolRouter
from decision_memory import DecisionMemoryService
from dream_engine import DreamEngine
from agent_runtime import AgentRuntime
from datetime import datetime, timezone, timedelta

async def run_learning_loop():
    print("🚀 Initializing BrainDump Sprint 2 Learning Loop...\n")

    # 1. Initialize Subsystems
    storage = SQLiteBackend("metadata_sprint2.db")
    vfs = BrainVFS(storage)
    retriever = BrainRetriever(vfs)
    policy_engine = PolicyEngine(vfs, retriever)
    decision_memory = DecisionMemoryService()
    dream_engine = DreamEngine(vfs, retriever)
    tool_router = ToolRouter()

    runtime = AgentRuntime(
        retriever=retriever,
        policy_engine=policy_engine,
        decision_memory=decision_memory,
        dream_engine=dream_engine,
        vfs=vfs,
        tool_router=tool_router
    )

    # 2. Pre-Seed Database to Simulate Time Passing
    print("⏳ Pre-seeding VFS with old and active memories...\n")

    # Old wiki entry that should be archived (Forgetting Curve)
    vfs.write(VFSNode(
        path="vfs://wiki/old_project/setup_notes",
        layer="wiki",
        content="This is an old project setup.",
        metadata={"memory_score": 0.2},
        updated_at=datetime.now(timezone.utc) - timedelta(days=40)
    ))

    # Highly confident, frequently used pattern that should become DNA
    vfs.write(VFSNode(
        path="vfs://wiki/coding_standards/python_rules",
        layer="wiki",
        content="Always use type hints.",
        metadata={"usage_count": 10, "confidence": 0.95},
        updated_at=datetime.now(timezone.utc) - timedelta(days=5)
    ))

    # Pre-register a successful strategy to simulate Meta-Learning later
    decision_memory.register_strategy("strat_test_driven", "Write tests before code.")
    strat = decision_memory.strategies["strat_test_driven"]
    strat.confidence_score = 0.92
    strat.usage_count = 15
    strat.success_rate = 0.90

    # 3. Agent Task Execution (triggers Dump + Daydream)
    print("\n=======================================================")
    print("🔄 Executing a task to trigger Daydream...")
    await runtime.run_task("Write a simple script for me.")
    print("=======================================================\n")

    # 4. Trigger Nightdream (Archive & DNA)
    print("\n=======================================================")
    print("🌙 Manually triggering Nightdream...")
    night_result = dream_engine.run_nightdream()
    print(f"✅ Archived: {night_result.archived}")
    print(f"✅ DNA Updates: {night_result.dna_updates}")
    print("=======================================================\n")

    # 5. Trigger Deepdream (Policy Meta-Learning)
    print("\n=======================================================")
    print("🌌 Manually triggering Deepdream...")
    deep_result = await dream_engine.run_deepdream(decision_memory_service=decision_memory)
    print(f"✅ New Policies Learned: {deep_result.policy_updates}")
    print("=======================================================\n")

    # 6. Verify Final State
    print("🔍 Inspecting Final VFS State...")
    print(f"  Dumps: {[n.path for n in vfs.list_namespace('vfs://dumps/')]}")
    print(f"  Wiki: {[n.path for n in vfs.list_namespace('vfs://wiki/')]}")
    print(f"  Archive: {[n.path for n in vfs.list_namespace('vfs://archive/')]}")
    print(f"  DNA: {[n.path for n in vfs.list_namespace('vfs://core/dna/')]}")
    print(f"  Policies: {[n.path for n in vfs.list_namespace('vfs://core/policies/')]}")

if __name__ == "__main__":
    asyncio.run(run_learning_loop())
