from collections import namedtuple
from typing import Optional, Tuple


# Custom object for holding player's pick for a particular game
Pick = namedtuple('Pick', ['team', 'points', 'correct'])


def parse_raw_pick(raw_pick: str) -> Tuple[Optional[str], Optional[int], Optional[str]]:
    """
    Parse a given player's pick for the team, number of points wagered, and pick status.

    Args:
        raw_pick: The player's raw pick. Comes in one of these formats:
                  1) 'TEAM(<pts>):-<status>' -- The player has made a selection ( e.g. 'KC(12):correct' )
                  2) None -- The player has not submitted ANY picks for the week
                  3) '-(<pts>):<status>' -- The player didn't pick this game (but has picked others in the week)
                  4) 'X:<status>'  -- The player has made a selection that is not yet visible to other players
                                      (e.g. 'X:unknown')
    Return:
        The team, number of points wagered, and status of the pick.
    """
    # Pick will be `None` if the player hasn't made any selections for the week yet.
    if raw_pick is None:
        return None, None, None

    pick, status = raw_pick.split(':')

    # Pick will be 'X:<status>' if other players cannot view it yet.
    if pick == 'X':
        return None, None, status

    team, wagered_pts = pick.strip(')').split('(')

    return team, int(wagered_pts), status


def cast_raw_pick(raw_pick: str) -> Pick:
    """
    Change a player's raw pick string to a Pick object (named tuple)

    Args:
        raw_pick: The player's raw pick.

    Return:
        The namedtuple representation of the raw pick.
    """
    team, wagered_pts, status = parse_raw_pick(raw_pick)
    return Pick(team, wagered_pts, status=='correct')
