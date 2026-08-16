"""Independent current/next futures state warming and promotion."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Generic, TypeVar


T = TypeVar("T")


@dataclass(slots=True)
class FuturesStateBook(Generic[T]):
    factory: Callable[[], T]
    states: dict[str, T] = field(default_factory=dict)
    current_contract: str | None = None
    next_contract: str | None = None

    def state(self, contract: str) -> T:
        if contract not in self.states:
            self.states[contract] = self.factory()
        return self.states[contract]

    def set_contracts(self, current: str, next_contract: str | None) -> None:
        self.current_contract = current
        self.next_contract = next_contract
        self.state(current)
        if next_contract is not None:
            self.state(next_contract)

    def promote(self, new_next_contract: str | None = None) -> T:
        if self.next_contract is None:
            raise ValueError("next contract has not been warmed")
        self.current_contract = self.next_contract
        self.next_contract = new_next_contract
        current_state = self.state(self.current_contract)
        if new_next_contract is not None:
            self.state(new_next_contract)
        return current_state
