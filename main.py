"""
Main entry point for Ajul AI Research Agent
"""

import asyncio
from loguru import logger

from ajul.config import Config
from ajul.orchestrator import AjulResearchAgent, AjulConfig


async def main():
    """Main entry point"""

    logger.info("Starting Ajul AI Research Agent")

    # Load configuration
    config = Config.from_env()

    # Create agent config
    agent_config = AjulConfig(
        anthropic_api_key=config.anthropic_api_key,
        model=config.model,
        enable_multimodal=config.enable_multimodal,
        enable_expert_feedback=config.enable_expert_feedback,
        enable_self_evaluation=config.enable_self_evaluation,
        memory_backend=config.memory_backend,
        max_research_cycles=config.max_research_cycles
    )

    # Initialize agent
    agent = AjulResearchAgent(agent_config)

    # Example research question
    research_question = "How can transformer architectures be optimized for scientific reasoning?"

    # Conduct research
    results = await agent.conduct_research(
        research_question=research_question,
        domain="machine_learning"
    )

    # Display results
    logger.info("Research Results:")
    logger.info(f"Question: {results['question']}")
    logger.info(f"Cycles completed: {len(results['cycles'])}")
    logger.info(f"Final insights: {results['final_insights']}")

    logger.success("Ajul completed successfully")


if __name__ == "__main__":
    asyncio.run(main())
