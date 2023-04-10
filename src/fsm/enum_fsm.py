from enum import Enum
from typing import Callable, Optional


#### #### #### ####
#### class
#### #### #### ####
class EnumFsm:
    def __init__(
        self,
        start_state: Enum,
        exit_state: Enum,
        on_state_changed: Optional[Callable] = None,
    ):
        self._on_state_changed = on_state_changed
        self._current_state = start_state
        self._exit_state = exit_state
        self._is_ready = False
        self._states = set()
        self._state_enter_callbacks = {}
        self._state_stay_callbacks = {}
        self._state_exit_callbacks = {}

    @property
    def current_state(self) -> Enum:
        return self._current_state

    def add_state(
        self,
        state: Enum,
        stay_callback: Callable,
        enter_callback: Optional[Callable] = None,
        exit_callback: Optional[Callable] = None,
    ):
        assert self._is_ready is False, "Cannot add state after FSM is ready"
        self._states.add(state)
        self._state_stay_callbacks[state] = stay_callback
        self._state_enter_callbacks[state] = enter_callback
        self._state_exit_callbacks[state] = exit_callback

    def start(self):
        assert self._current_state in self._states
        self._is_ready = True

    def update(self) -> bool:
        """Advance the FSM by one step.

        Returns:
            bool: True if the FSM is exited, False otherwise.
        """
        assert self._is_ready is True, "FSM is not ready"
        next_state = self._state_stay_callbacks[self._current_state]()
        assert (
            next_state in self._states
        ), "Invalid next state from state \"{}\"".format(self._current_state)
        if next_state == self._current_state:
            return self._current_state == self._exit_state
        exit_function = self._state_exit_callbacks[self._current_state]
        if exit_function is not None:
            exit_function()
        if self._on_state_changed is not None:
            self._on_state_changed(
                current_state=self._current_state, next_state=next_state
            )
        self._current_state = next_state
        enter_function = self._state_enter_callbacks[self._current_state]
        if enter_function is not None:
            enter_function()
        return self._current_state == self._exit_state
