from __future__ import annotations

from dataclasses import dataclass

from clawai.agents.specialist_agent import (
    planner_agent,
    research_agent,
    coder_agent,
    reviewer_agent,
    tester_agent,
)


@dataclass
class TeamResult:

    planning: str

    research: str

    implementation: str

    review: str

    tests: str


class TeamLeader:

    def execute(
        self,
        objective: str,
    ) -> TeamResult:

        planning = planner_agent.execute(
            objective
        )

        research = research_agent.execute(
            planning.response
        )

        implementation = coder_agent.execute(
            f"""
Planejamento:

{planning.response}

Pesquisa:

{research.response}
"""
        )

        review = reviewer_agent.execute(
            implementation.response
        )

        tests = tester_agent.execute(
            implementation.response
        )

        return TeamResult(

            planning=planning.response,

            research=research.response,

            implementation=implementation.response,

            review=review.response,

            tests=tests.response,

        )


team_leader = TeamLeader()
