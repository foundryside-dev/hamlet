"""Integration tests for Expression → VFS → Effects flow.

Tests the expression evaluation pipeline:
  Expression String → Parse → Type Check → Evaluate → VFS → Effects
"""

import pytest
import torch

from townlet.effects.context import ExecutionContext as EffectsExecutionContext
from townlet.effects.executor import CommandExecutor
from townlet.effects.schema import CommandNode, CommandType
from townlet.vfs.registry import VariableRegistry
from townlet.vfs.schema import VariableDef, VariableScope
from townlet.world.expression.context import ExecutionContext
from townlet.world.expression.evaluator import Evaluator
from townlet.world.expression.parser import ExpressionParser


@pytest.fixture
def expression_parser():
    """Expression parser instance."""
    return ExpressionParser()


@pytest.fixture
def vfs_registry():
    """VFS registry with test variables."""
    # Define variables list
    variables = [
        VariableDef(
            id="computed_value",
            scope=VariableScope.AGENT,
            type="scalar",
            lifetime="episode",
            readable_by=["agent", "engine"],
            writable_by=["engine"],
            default=0.0,
        )
    ]

    # Create registry with variables
    registry = VariableRegistry(variables=variables, num_agents=2, device=torch.device("cpu"))

    return registry


class TestExpressionVFSEffectsFlow:
    """Test data flow through expression → VFS → Effects."""

    def test_expression_parses_and_evaluates(self, expression_parser):
        """Expression string parses to AST and evaluates."""
        # Parse expression
        expr_str = "0.5 + 0.3"
        ast = expression_parser.parse(expr_str)

        # Evaluate with context
        context = ExecutionContext(bars={}, vfs={}, affordances={}, temporal={}, device=torch.device("cpu"))
        evaluator = Evaluator(context)
        result = evaluator.evaluate(ast)

        # Verify result
        assert isinstance(result, torch.Tensor)
        assert result.item() == pytest.approx(0.8)

    def test_expression_reads_from_bars(self, expression_parser):
        """Expression can read from bars dict."""
        # Parse expression referencing bar
        expr_str = "bar.energy + 0.2"
        ast = expression_parser.parse(expr_str)

        # Setup context with bars
        bars = {"energy": torch.tensor([0.5, 0.6])}
        context = ExecutionContext(bars=bars, vfs={}, affordances={}, temporal={}, device=torch.device("cpu"))

        # Evaluate (context indexes into the batch for us)
        evaluator = Evaluator(context)
        result = evaluator.evaluate(ast)

        # Verify: Returns full tensor [0.7, 0.8]
        assert result[0].item() == pytest.approx(0.7)
        assert result[1].item() == pytest.approx(0.8)

    def test_expression_reads_from_vfs(self, expression_parser, vfs_registry):
        """Expression can read from VFS registry."""
        # Set VFS value
        vfs_registry.set("computed_value", torch.tensor([1.0, 2.0]), writer="engine")

        # Parse expression referencing VFS
        expr_str = "vfs.computed_value * 2.0"
        ast = expression_parser.parse(expr_str)

        # Setup context with vfs dict
        vfs_dict = {"computed_value": torch.tensor([1.0, 2.0])}
        context = ExecutionContext(bars={}, vfs=vfs_dict, affordances={}, temporal={}, device=torch.device("cpu"))

        # Evaluate
        evaluator = Evaluator(context)
        result = evaluator.evaluate(ast)

        # Verify: [1.0, 2.0] * 2.0 = [2.0, 4.0]
        assert result[0].item() == pytest.approx(2.0)
        assert result[1].item() == pytest.approx(4.0)

    def test_effects_execute_with_expressions(self, expression_parser, vfs_registry):
        """Effects can execute commands with expression values."""
        # Setup execution context for effects system
        bars = {"energy": torch.tensor([0.5, 0.6])}
        context = EffectsExecutionContext(bars=bars, vfs_registry=vfs_registry, self_index=None, target_index=0)

        # Create command executor
        executor = CommandExecutor()

        # Parse expression to get AST
        expr_str = "target.bar.energy + 0.3"
        ast = expression_parser.parse(expr_str)

        # Create command with pre-compiled AST
        command = CommandNode(
            type=CommandType.MODIFY,
            path="target.bar.energy",
            value_expr=expr_str,
            value_ast=ast,
        )

        # Execute command
        executor.execute(command, context)

        # Verify: energy[0] updated from 0.5 to 0.8
        assert bars["energy"][0].item() == pytest.approx(0.8)
