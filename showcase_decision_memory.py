import asyncio
from decision_memory import DecisionMemoryService, OutcomeFeedback

async def run_showcase():
    print("🧠 Starting BrainDump Decision Memory Showcase...\n")

    # 1. Initialize Service
    dms = DecisionMemoryService()

    # Pre-register some initial strategies for a hypothetical "Data Extraction" task
    dms.register_strategy("strat_regex", "Use RegEx to find entities.")
    dms.register_strategy("strat_llm_zero_shot", "Ask LLM directly without examples.")
    dms.register_strategy("strat_llm_few_shot", "Ask LLM with 3 examples.")

    print("Initial Strategies Registered:")
    for sid, s in dms.strategies.items():
        print(f" - {sid} (Confidence: {s.confidence_score:.2f})")
    print("\n")

    task_context = {"task_type": "entity_extraction", "complexity": "high"}

    print("🔄 Running 20 Task Cycles (Simulation)...\n")
    for i in range(20):
        # 2. Recommend Strategy (Exploration vs Exploitation inside)
        chosen_strategy = await dms.recommend_strategy(task_context)

        # 3. Record Decision
        episode_id = await dms.record_decision(task_context, chosen_strategy)

        # Simulate Outcome (Mock Environment Logic)
        success = False
        efficiency = 0.5

        if chosen_strategy == "strat_regex":
            # Fast but fails often on high complexity
            success = i % 4 == 0  # 25% success
            efficiency = 0.9
        elif chosen_strategy == "strat_llm_zero_shot":
            # Medium success, medium speed
            success = i % 2 == 0  # 50% success
            efficiency = 0.6
        elif chosen_strategy == "strat_llm_few_shot":
            # High success, slow speed
            success = i % 10 != 0 # 90% success
            efficiency = 0.3

        # 4. Record Outcome
        feedback = OutcomeFeedback(
            episode_id=episode_id,
            success=success,
            efficiency_score=efficiency
        )

        await dms.record_outcome(feedback)

    print("📊 Final Strategy Standings:")
    for sid, s in dms.strategies.items():
        print(f" - {sid}: Used {s.usage_count} times, Success: {s.success_rate*100:.0f}%, Confidence: {s.confidence_score:.3f}")
    print("\n")

    # 5. Export to Deepdream
    print("🌌 Deepdream Cycle Initiated...")
    export_data = await dms.export_for_deepdream(confidence_threshold=0.6)

    if not export_data:
        print(" -> No strategies reached the confidence threshold for DNA integration.")
    else:
        for data in export_data:
            print(f" -> Exporting '{data['strategy_id']}' to DNA.")
            if data['mutation_flag']:
                print(f"    ⚠️ MUTATION TRIGGERED: {data['mutation_reason']} - Sending to Dream Engine for variation.")

if __name__ == "__main__":
    asyncio.run(run_showcase())
