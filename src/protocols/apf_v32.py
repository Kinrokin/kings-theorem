from enum import Enum


class APFLogicValue(Enum):
    TRUE = 1
    FALSE = 0
    BOTH = 2
    NEITHER = 3


def fuse_paradox(state_a: bool, state_b: bool) -> APFLogicValue:
    if state_a and state_b:
        return APFLogicValue.TRUE
    if not state_a and not state_b:
        return APFLogicValue.FALSE
    if state_a != state_b:
        return APFLogicValue.BOTH
    return APFLogicValue.NEITHER
