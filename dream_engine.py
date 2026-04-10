from dataclasses import dataclass, field
from typing import List, Any, Dict
from datetime import datetime, timezone, timedelta
from brain_vfs import BrainVFS, VFSNode
from retriever import BrainRetriever

@dataclass
class DreamResult:
    promoted: List[str] = field(default_factory=list)
    archived: List[str] = field(default_factory=list)
    dna_updates: List[str] = field(default_factory=list)
    policy_updates: List[str] = field(default_factory=list)

class DreamEngine:
    """The consolidation and learning core of BrainDump."""
    def __init__(self, vfs: BrainVFS, retriever: BrainRetriever, entity_resolver=None):
        self.vfs = vfs
        self.retriever = retriever
        self.entity_resolver = entity_resolver

    def run_daydream(self) -> DreamResult:
        """Micro Consolidation: Runs frequently to process raw dumps into structured knowledge."""
        print("☁️ [Daydream] Starting micro-consolidation...")
        result = DreamResult()

        # 1. Scan for recent dumps
        # Simplistic assumption for mockup: all dumps are under vfs://dumps/
        dumps = self.vfs.list_namespace("vfs://dumps/")

        for dump in dumps:
            if not dump.metadata.get("daydream_processed", False):
                # Mock: Fact Extraction & Promotion
                # If a dump contains useful knowledge, promote it to user wiki or skills
                target_path = f"vfs://wiki/projects/auto-extract/{dump.path.split('/')[-1]}"

                print(f"  -> Extracting facts from {dump.path}")
                self.vfs.promote(dump.path, target_path)
                result.promoted.append(target_path)

                # Mark as processed
                dump.metadata["daydream_processed"] = True
                self.vfs.write(dump)

        return result

    def run_nightdream(self) -> DreamResult:
        """Deep Consolidation: Runs daily to merge redundancy, forget (cool down), and promote to DNA."""
        print("🌙 [Nightdream] Starting deep consolidation...")
        result = DreamResult()

        # 1. Forgetting Curve (Active -> Archive)
        now = datetime.now(timezone.utc)
        wikis = self.vfs.list_namespace("vfs://wiki/")
        for wiki in wikis:
            age = (now - wiki.updated_at).days
            score = wiki.metadata.get("memory_score", 1.0)

            if age > 30 and score < 0.5:
                # Move to archive
                archive_path = f"vfs://archive/wiki/{wiki.path.split('/')[-1]}"
                print(f"  -> Cooling down and archiving: {wiki.path}")
                self.vfs.promote(wiki.path, archive_path)
                self.vfs.delete(wiki.path)
                result.archived.append(archive_path)

        # 2. DNA Candidate Extraction
        # Look for repeated, highly confident patterns in the wiki
        for wiki in wikis:
            usage_count = wiki.metadata.get("usage_count", 0)
            confidence = wiki.metadata.get("confidence", 0.0)

            # Heuristic for DNA
            if usage_count > 5 and confidence > 0.8:
                dna_path = f"vfs://core/dna/{wiki.path.split('/')[-1]}"
                print(f"  -> 🧬 Promoting stable pattern to DNA: {dna_path}")
                self.vfs.promote(wiki.path, dna_path)
                result.dna_updates.append(dna_path)

        return result

    async def run_deepdream(self, decision_memory_service=None) -> DreamResult:
        """Meta Learning: Runs weekly to abstract policies from decision outcomes."""
        print("🌌 [Deepdream] Starting meta-learning and policy extraction...")
        result = DreamResult()

        if decision_memory_service:
            export_candidates = await decision_memory_service.export_for_deepdream(confidence_threshold=0.8)

            for candidate in export_candidates:
                policy_path = f"vfs://core/policies/learned_from_{candidate['strategy_id']}"
                print(f"  -> 📜 Extracting new policy from decision memory: {policy_path}")

                # Construct a new policy node based on the successful strategy
                policy_node = VFSNode(
                    path=policy_path,
                    layer="policies",
                    content={"action": "enforce_learned_strategy", "strategy": candidate["strategy_id"]},
                    metadata={"source": "deepdream", "confidence": candidate["confidence"]}
                )
                self.vfs.write(policy_node)
                result.policy_updates.append(policy_path)

        return result
