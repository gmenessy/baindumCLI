import asyncio
from brain_vfs import BrainVFS, SQLiteBackend, VFSNode
from retriever import BrainRetriever
from policy_engine import PolicyEngine
from tool_router import ToolRouter
from decision_memory import DecisionMemoryService
from dream_engine import DreamEngine
from agent_runtime import AgentRuntime

async def run_vertical_slice():
    print("🚀 Initializing BrainDump Core Services...\n")

    # 1. Initialize DB Backend & VFS
    storage = SQLiteBackend("metadata.db")
    vfs = BrainVFS(storage)

    # Seed some mock data in VFS to make it interesting
    vfs.write(VFSNode(
        path="vfs://core/policies/rule_db",
        layer="policies",
        content={"id": "policy_db", "action": "always snapshot before migration"}
    ))

    # 2. Initialize Subsystems
    retriever = BrainRetriever(vfs)
    policy_engine = PolicyEngine(vfs, retriever)
    decision_memory = DecisionMemoryService()
    dream_engine = DreamEngine(vfs, retriever)
    tool_router = ToolRouter()

    # 3. Create Runtime Kernel
    runtime = AgentRuntime(
        retriever=retriever,
        policy_engine=policy_engine,
        decision_memory=decision_memory,
        dream_engine=dream_engine,
        vfs=vfs,
        tool_router=tool_router
    )

    # 4. Execute a Task
    print("\n=======================================================")
    task_query = "Please scan the repository for security vulnerabilities."
    result = await runtime.run_task(task_query)
    print(f"\n✅ Final Task Result: {result}")
    print("=======================================================\n")

    # 5. Verify VFS Dump
    print("🔍 Inspecting VFS for the generated Dump...")
    import sqlite3
    with sqlite3.connect("metadata.db") as conn:
        cursor = conn.execute("SELECT path, layer FROM vfs_nodes WHERE layer = 'dumps'")
        rows = cursor.fetchall()
        for path, layer in rows:
            print(f"   Found Dump: {path}")

if __name__ == "__main__":
    asyncio.run(run_vertical_slice())
