"""
Multi-Agent Collaboration Framework

Enables multiple AI agents to:
- Generate hypotheses collaboratively
- Review and critique each other's work
- Refine predictions through discussion
- Reach consensus on research directions

Implements specialized agent roles and coordination protocols.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid

from anthropic import AsyncAnthropic
from loguru import logger


class AgentRole(str, Enum):
    """Specialized agent roles in research process"""
    GENERATOR = "generator"  # Generate hypotheses
    CRITIC = "critic"  # Review and critique
    VALIDATOR = "validator"  # Validate methodology
    SYNTHESIZER = "synthesizer"  # Integrate findings
    EXPERIMENTER = "experimenter"  # Design experiments
    ANALYST = "analyst"  # Analyze results


@dataclass
class Message:
    """Communication message between agents"""
    id: str
    sender_id: str
    sender_role: AgentRole
    recipient_id: Optional[str]  # None = broadcast
    content: str
    message_type: str  # proposal, critique, question, answer, consensus
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    references: List[str] = field(default_factory=list)  # Referenced message IDs


@dataclass
class AgentState:
    """Internal state of an agent"""
    agent_id: str
    role: AgentRole
    beliefs: Dict[str, Any]  # Current beliefs/knowledge
    goals: List[str]  # Current objectives
    memory: List[Message]  # Recent message history
    confidence: float = 0.5  # Confidence in current position
    active: bool = True


class ResearchAgent:
    """
    Single autonomous agent with specialized role.

    Can generate, critique, or validate research hypotheses
    based on its assigned role and expertise.
    """

    def __init__(
        self,
        agent_id: str,
        role: AgentRole,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        expertise_domain: Optional[str] = None
    ):
        self.agent_id = agent_id
        self.role = role
        self.expertise_domain = expertise_domain

        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

        self.state = AgentState(
            agent_id=agent_id,
            role=role,
            beliefs={},
            goals=[],
            memory=[]
        )

    async def process_message(
        self,
        message: Message,
        context: Optional[Dict] = None
    ) -> Message:
        """
        Process incoming message and generate response.

        Args:
            message: Message to process
            context: Additional context

        Returns:
            Response message
        """
        logger.info(f"[{self.role}] Processing message from {message.sender_role}")

        # Add to memory
        self.state.memory.append(message)

        # Generate response based on role
        if self.role == AgentRole.GENERATOR:
            response = await self._generate_hypothesis(message, context)
        elif self.role == AgentRole.CRITIC:
            response = await self._critique_proposal(message, context)
        elif self.role == AgentRole.VALIDATOR:
            response = await self._validate_methodology(message, context)
        elif self.role == AgentRole.SYNTHESIZER:
            response = await self._synthesize_discussion(message, context)
        elif self.role == AgentRole.EXPERIMENTER:
            response = await self._design_experiment(message, context)
        elif self.role == AgentRole.ANALYST:
            response = await self._analyze_results(message, context)
        else:
            response = await self._generic_response(message, context)

        return response

    async def _generate_hypothesis(
        self,
        message: Message,
        context: Optional[Dict]
    ) -> Message:
        """Generate hypothesis based on prompt"""

        prompt = f"""You are a hypothesis generator agent specialized in {self.expertise_domain or 'general science'}.

Context: {message.content}

Generate a novel, testable hypothesis that:
1. Addresses the research question
2. Is falsifiable
3. Makes specific predictions
4. Is feasible to test

Format:
**Hypothesis**: [title]
**Description**: [detailed explanation]
**Predictions**: [specific testable predictions]
**Novelty**: [what makes this unique]
"""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.content[0].text

        return Message(
            id=str(uuid.uuid4()),
            sender_id=self.agent_id,
            sender_role=self.role,
            recipient_id=message.sender_id,
            content=content,
            message_type="proposal",
            metadata={"confidence": 0.7}
        )

    async def _critique_proposal(
        self,
        message: Message,
        context: Optional[Dict]
    ) -> Message:
        """Critique a hypothesis or proposal"""

        prompt = f"""You are a critical reviewer agent specialized in {self.expertise_domain or 'scientific methodology'}.

Review the following proposal:

{message.content}

Provide constructive critique addressing:
1. **Strengths**: What is good about this proposal?
2. **Weaknesses**: What are the flaws or gaps?
3. **Testability**: Can this be tested? How?
4. **Feasibility**: Is this realistic?
5. **Improvements**: How can this be improved?

Be objective and evidence-based.
"""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            temperature=0.4,
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.content[0].text

        return Message(
            id=str(uuid.uuid4()),
            sender_id=self.agent_id,
            sender_role=self.role,
            recipient_id=message.sender_id,
            content=content,
            message_type="critique",
            metadata={"critique_severity": "moderate"}
        )

    async def _validate_methodology(
        self,
        message: Message,
        context: Optional[Dict]
    ) -> Message:
        """Validate experimental methodology"""

        prompt = f"""You are a methodology validator specializing in {self.expertise_domain or 'experimental design'}.

Validate the following methodology:

{message.content}

Assess:
1. **Rigor**: Is the methodology scientifically rigorous?
2. **Controls**: Are proper controls in place?
3. **Variables**: Are variables well-defined?
4. **Reproducibility**: Can others reproduce this?
5. **Ethics**: Any ethical concerns?

Provide validation score (0-1) and recommendations.
"""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.content[0].text

        return Message(
            id=str(uuid.uuid4()),
            sender_id=self.agent_id,
            sender_role=self.role,
            recipient_id=message.sender_id,
            content=content,
            message_type="validation",
            metadata={"validation_score": 0.8}
        )

    async def _synthesize_discussion(
        self,
        message: Message,
        context: Optional[Dict]
    ) -> Message:
        """Synthesize multiple viewpoints"""

        # Gather recent discussion
        recent_messages = self.state.memory[-10:]
        discussion = "\n\n".join([
            f"[{msg.sender_role}]: {msg.content[:200]}..."
            for msg in recent_messages
        ])

        prompt = f"""You are a synthesizer agent that integrates multiple perspectives.

Discussion so far:
{discussion}

Current message:
{message.content}

Synthesize the discussion by:
1. Identifying consensus points
2. Highlighting disagreements
3. Proposing integrated solution
4. Suggesting next steps

Create coherent synthesis.
"""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            temperature=0.5,
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.content[0].text

        return Message(
            id=str(uuid.uuid4()),
            sender_id=self.agent_id,
            sender_role=self.role,
            recipient_id=None,  # Broadcast
            content=content,
            message_type="consensus",
            metadata={"synthesis_type": "integration"}
        )

    async def _design_experiment(
        self,
        message: Message,
        context: Optional[Dict]
    ) -> Message:
        """Design experiment for hypothesis"""

        prompt = f"""You are an experimental design specialist in {self.expertise_domain or 'scientific research'}.

Design an experiment for:

{message.content}

Include:
1. **Objective**: Clear goal
2. **Methods**: Step-by-step procedure
3. **Materials**: What's needed
4. **Measurements**: What to measure
5. **Analysis**: How to analyze data
6. **Timeline**: Estimated duration
"""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            temperature=0.5,
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.content[0].text

        return Message(
            id=str(uuid.uuid4()),
            sender_id=self.agent_id,
            sender_role=self.role,
            recipient_id=message.sender_id,
            content=content,
            message_type="proposal",
            metadata={"experiment_complexity": "moderate"}
        )

    async def _analyze_results(
        self,
        message: Message,
        context: Optional[Dict]
    ) -> Message:
        """Analyze experimental results"""

        prompt = f"""You are a data analyst specialized in {self.expertise_domain or 'scientific data'}.

Analyze the following results:

{message.content}

Provide:
1. **Summary**: Key findings
2. **Statistical Analysis**: Significance
3. **Interpretation**: What does it mean?
4. **Limitations**: What are the caveats?
5. **Conclusions**: Support or reject hypothesis?
"""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            temperature=0.4,
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.content[0].text

        return Message(
            id=str(uuid.uuid4()),
            sender_id=self.agent_id,
            sender_role=self.role,
            recipient_id=message.sender_id,
            content=content,
            message_type="answer",
            metadata={"analysis_confidence": 0.8}
        )

    async def _generic_response(
        self,
        message: Message,
        context: Optional[Dict]
    ) -> Message:
        """Generic response for undefined roles"""

        return Message(
            id=str(uuid.uuid4()),
            sender_id=self.agent_id,
            sender_role=self.role,
            recipient_id=message.sender_id,
            content="Acknowledged.",
            message_type="answer"
        )


class MultiAgentOrchestrator:
    """
    Orchestrates collaboration between multiple research agents.

    Manages:
    - Agent creation and lifecycle
    - Message routing
    - Consensus building
    - Workflow coordination
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.agents: Dict[str, ResearchAgent] = {}
        self.message_queue: List[Message] = []
        self.conversation_history: List[Message] = []

    def create_agent(
        self,
        role: AgentRole,
        expertise_domain: Optional[str] = None
    ) -> str:
        """
        Create new agent with specified role.

        Args:
            role: Agent role
            expertise_domain: Optional domain expertise

        Returns:
            Agent ID
        """
        agent_id = f"{role.value}_{len(self.agents)}"

        agent = ResearchAgent(
            agent_id=agent_id,
            role=role,
            api_key=self.api_key,
            expertise_domain=expertise_domain
        )

        self.agents[agent_id] = agent
        logger.info(f"Created agent: {agent_id} ({role})")

        return agent_id

    async def route_message(self, message: Message):
        """Route message to appropriate agent(s)"""

        if message.recipient_id:
            # Direct message
            if message.recipient_id in self.agents:
                self.message_queue.append(message)
        else:
            # Broadcast to all agents
            for agent_id in self.agents.keys():
                broadcast_msg = Message(
                    id=str(uuid.uuid4()),
                    sender_id=message.sender_id,
                    sender_role=message.sender_role,
                    recipient_id=agent_id,
                    content=message.content,
                    message_type=message.message_type,
                    metadata=message.metadata
                )
                self.message_queue.append(broadcast_msg)

        self.conversation_history.append(message)

    async def process_queue(self) -> List[Message]:
        """Process all messages in queue"""

        responses = []

        while self.message_queue:
            message = self.message_queue.pop(0)

            if message.recipient_id in self.agents:
                agent = self.agents[message.recipient_id]
                response = await agent.process_message(message)
                responses.append(response)
                self.conversation_history.append(response)

        return responses

    async def collaborative_hypothesis_generation(
        self,
        research_question: str,
        domain: str
    ) -> Dict[str, Any]:
        """
        Run collaborative hypothesis generation workflow.

        Steps:
        1. Generator proposes hypotheses
        2. Critic reviews proposals
        3. Validator checks methodology
        4. Synthesizer integrates feedback
        5. Final refined hypothesis

        Args:
            research_question: Question to address
            domain: Research domain

        Returns:
            Final consensus hypothesis with discussion
        """
        logger.info("Starting collaborative hypothesis generation...")

        # Create specialized agents
        generator_id = self.create_agent(AgentRole.GENERATOR, domain)
        critic_id = self.create_agent(AgentRole.CRITIC, domain)
        validator_id = self.create_agent(AgentRole.VALIDATOR, domain)
        synthesizer_id = self.create_agent(AgentRole.SYNTHESIZER, domain)

        # Step 1: Generator proposes
        initial_msg = Message(
            id=str(uuid.uuid4()),
            sender_id="orchestrator",
            sender_role=AgentRole.GENERATOR,
            recipient_id=generator_id,
            content=f"Research Question: {research_question}\nDomain: {domain}",
            message_type="proposal"
        )

        await self.route_message(initial_msg)
        responses = await self.process_queue()

        # Step 2: Critic reviews
        if responses:
            critique_msg = Message(
                id=str(uuid.uuid4()),
                sender_id="orchestrator",
                sender_role=AgentRole.CRITIC,
                recipient_id=critic_id,
                content=responses[0].content,
                message_type="critique"
            )
            await self.route_message(critique_msg)
            await self.process_queue()

        # Step 3: Validator checks
        validation_msg = Message(
            id=str(uuid.uuid4()),
            sender_id="orchestrator",
            sender_role=AgentRole.VALIDATOR,
            recipient_id=validator_id,
            content=responses[0].content if responses else "",
            message_type="validation"
        )
        await self.route_message(validation_msg)
        await self.process_queue()

        # Step 4: Synthesizer integrates
        synthesis_msg = Message(
            id=str(uuid.uuid4()),
            sender_id="orchestrator",
            sender_role=AgentRole.SYNTHESIZER,
            recipient_id=synthesizer_id,
            content="Synthesize all feedback into final hypothesis",
            message_type="consensus"
        )
        await self.route_message(synthesis_msg)
        final_responses = await self.process_queue()

        # Return results
        return {
            "research_question": research_question,
            "domain": domain,
            "conversation_history": [
                {
                    "role": msg.sender_role.value,
                    "content": msg.content[:200] + "...",
                    "type": msg.message_type
                }
                for msg in self.conversation_history
            ],
            "final_hypothesis": final_responses[-1].content if final_responses else "",
            "agent_count": len(self.agents),
            "message_count": len(self.conversation_history)
        }

    async def collaborative_experiment_review(
        self,
        experiment_description: str,
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Collaborative review of experiment results.

        Multiple agents analyze, critique, and synthesize findings.

        Args:
            experiment_description: Experiment details
            results: Experimental results

        Returns:
            Consensus analysis
        """
        logger.info("Starting collaborative experiment review...")

        # Create review team
        analyst_id = self.create_agent(AgentRole.ANALYST)
        critic_id = self.create_agent(AgentRole.CRITIC)
        synthesizer_id = self.create_agent(AgentRole.SYNTHESIZER)

        # Analyst reviews
        content = f"Experiment: {experiment_description}\n\nResults: {results}"

        analysis_msg = Message(
            id=str(uuid.uuid4()),
            sender_id="orchestrator",
            sender_role=AgentRole.ANALYST,
            recipient_id=analyst_id,
            content=content,
            message_type="question"
        )

        await self.route_message(analysis_msg)
        await self.process_queue()

        # Critic evaluates
        await self.route_message(Message(
            id=str(uuid.uuid4()),
            sender_id="orchestrator",
            sender_role=AgentRole.CRITIC,
            recipient_id=critic_id,
            content=content,
            message_type="critique"
        ))
        await self.process_queue()

        # Synthesizer integrates
        await self.route_message(Message(
            id=str(uuid.uuid4()),
            sender_id="orchestrator",
            sender_role=AgentRole.SYNTHESIZER,
            recipient_id=synthesizer_id,
            content="Integrate analysis and critique into consensus",
            message_type="consensus"
        ))
        final = await self.process_queue()

        return {
            "experiment": experiment_description,
            "consensus": final[-1].content if final else "",
            "agents_involved": len(self.agents)
        }

    def get_agent_states(self) -> Dict[str, Dict]:
        """Get current state of all agents"""
        return {
            agent_id: {
                "role": agent.role.value,
                "expertise": agent.expertise_domain,
                "memory_size": len(agent.state.memory),
                "confidence": agent.state.confidence,
                "active": agent.state.active
            }
            for agent_id, agent in self.agents.items()
        }
