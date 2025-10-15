"""Tests for orchestrator"""
import pytest
from ajul.orchestrator import AjulConfig, AjulResearchAgent

def test_config_creation():
    config = AjulConfig(anthropic_api_key="test_key")
    assert config.anthropic_api_key == "test_key"
    assert config.model == "claude-sonnet-4-20250514"

def test_agent_initialization():
    config = AjulConfig(anthropic_api_key="test_key")
    agent = AjulResearchAgent(config)
    assert agent.config == config
