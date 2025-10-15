# Ajul AI Research Agent

**Autonomous AI system for scientific research and automated discovery.**

## Features
- 15 Core modules for autonomous research
- Multi-agent collaboration
- Self-evaluation & improvement
- Human-in-the-loop feedback
- Multimodal integration

## Installation
```bash
pip install -r requirements.txt
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
```

## Quick Start
```python
from ajul import AjulResearchAgent
from ajul.orchestrator import AjulConfig

config = AjulConfig(anthropic_api_key="your_key")
agent = AjulResearchAgent(config)
```

## Status
✅ 15/15 Core modules complete
🚧 Integration testing in progress
