from __future__ import annotations

from typing import Any

from .planning_strategy import PlanningStrategy, RuleBasedPlanningStrategy


class PlannerFactory:
    _strategies: dict[str, type[PlanningStrategy]] = {
        "rule_based": RuleBasedPlanningStrategy,
    }

    @classmethod
    def register(cls, name: str, strategy_cls: type[PlanningStrategy]) -> None:
        cls._strategies[name] = strategy_cls

    @classmethod
    def create(cls, strategy_name: str = "rule_based", **kwargs: Any) -> PlanningStrategy:
        if strategy_name not in cls._strategies:
            raise ValueError(
                f"Unknown strategy: {strategy_name!r}. "
                f"Available: {list(cls._strategies.keys())}"
            )
        strategy_cls = cls._strategies[strategy_name]
        if strategy_cls is RuleBasedPlanningStrategy and "decomposer" not in kwargs:
            from .goal_decomposer import GoalDecomposer
            kwargs["decomposer"] = GoalDecomposer()
        return strategy_cls(**kwargs)
