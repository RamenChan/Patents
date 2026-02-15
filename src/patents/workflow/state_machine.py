from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class WorkflowState(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    FINAL = "final"
    FILED = "filed"


_ALLOWED_TRANSITIONS: Dict[WorkflowState, List[WorkflowState]] = {
    WorkflowState.DRAFT: [WorkflowState.REVIEW],
    WorkflowState.REVIEW: [WorkflowState.DRAFT, WorkflowState.FINAL],
    WorkflowState.FINAL: [WorkflowState.FILED],
    WorkflowState.FILED: [],
}


@dataclass(frozen=True)
class WorkflowStatus:
    invention_id: str
    state: WorkflowState


class WorkflowEngine:
    def can_transition(self, current: WorkflowState, target: WorkflowState) -> bool:
        return target in _ALLOWED_TRANSITIONS.get(current, [])

    def transition(self, status: WorkflowStatus, target: WorkflowState) -> WorkflowStatus:
        if not self.can_transition(status.state, target):
            raise ValueError(f"Invalid transition: {status.state.value} -> {target.value}")
        return WorkflowStatus(invention_id=status.invention_id, state=target)
