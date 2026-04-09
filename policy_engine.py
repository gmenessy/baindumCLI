from dataclasses import dataclass, field
from typing import Dict, Any, List
from retriever import BrainRetriever
from brain_vfs import BrainVFS

@dataclass
class PolicyRule:
    policy_id: str
    condition: Dict[str, Any]
    action: Dict[str, Any]
    priority: float = 0.5
    confidence: float = 0.8
    source: str = "dream"

class PolicyEngine:
    """The active rule and governance system for BrainDump."""
    def __init__(self, vfs: BrainVFS, retriever: BrainRetriever):
        self.vfs = vfs
        self.retriever = retriever

    def evaluate(self, task_context: Dict[str, Any]) -> List[PolicyRule]:
        """Evaluates policies against the current task context."""
        return self._match_rules(task_context)

    def apply(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        """Applies rules and composes an execution plan."""
        rules = self.evaluate(task_context)
        return self._compose_execution_plan(task_context, rules)

    def _match_rules(self, task_context: Dict[str, Any]) -> List[PolicyRule]:
        # Mock policy matching logic
        # In a real system, this would evaluate 'condition' fields of retrieved policies.
        matched = []

        # Check if context has retrieved policies
        if "context" in task_context and hasattr(task_context["context"], "policies"):
            for p in task_context["context"].policies:
                matched.append(PolicyRule(
                    policy_id=p.get("id", "unknown"),
                    condition={"type": "always"},
                    action={"type": "enforce", "value": p.get("content")},
                    priority=0.9
                ))

        # Inject a default policy rule
        matched.append(PolicyRule(
            policy_id="default_fallback",
            condition={"type": "always"},
            action={"type": "execute_tool", "tool": "default_llm"},
            priority=0.1
        ))

        # Sort by priority
        return sorted(matched, key=lambda x: x.priority, reverse=True)

    def _compose_execution_plan(self, task_context: Dict[str, Any], rules: List[PolicyRule]) -> Dict[str, Any]:
        """Creates an agent-ready plan based on policies."""
        plan = {
            "query": task_context.get("query"),
            "steps": [],
            "constraints": []
        }

        for rule in rules:
            if rule.action.get("type") == "enforce":
                plan["constraints"].append(rule.action.get("value"))
            elif rule.action.get("type") == "execute_tool":
                plan["steps"].append(rule.action.get("tool"))

        return plan
