from typing import Dict, Any

class ToolRouter:
    """Safe execution environment for Agent plans."""

    def __init__(self):
        self.registered_tools = {
            "default_llm": self._mock_llm_tool,
            "repo_scan": self._mock_repo_scan
        }

    def execute(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches tools based on the execution plan."""
        print(f"🔧 ToolRouter received plan: {plan}")

        results = {}
        for step in plan.get("steps", []):
            if step in self.registered_tools:
                print(f"  -> Executing: {step}")
                results[step] = self.registered_tools[step](plan.get("query"))
            else:
                print(f"  -> ⚠️ Tool {step} not found!")
                results[step] = {"error": "Tool not found"}

        return {
            "status": "success",
            "tool_outputs": results,
            "constraints_applied": plan.get("constraints", [])
        }

    def _mock_llm_tool(self, query: str) -> str:
        return f"LLM thought process for: {query}"

    def _mock_repo_scan(self, query: str) -> str:
        return "Found 3 files matching query."
