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


# # TODO: Do we still need this function given the one below it?
# def pick_to_int(pick: Optional[str]) -> int:
#     """
#     Parse a game pick string for the number of points wagered on the game. If the game has not been picked by the user
#     or the pick is not yet visible, return 0 as the number of points wagered.
#
#     Args:
#         pick: One of:   1) String representing the player's pick like 'KC(11)'.
#                         2) 'X' -- The player has picked the game but their selection is not yet visible.
#                         3) '-' -- The player has not picked this game, but has picked other games this week.
#                         4) None -- The player has not picked any games this week.
#     Return:
#         The number of points the player wagered on the pick.
#     """
#     # We're only interested in the points wagered (if any) on each matchup
#     _, pts, _ = parse_raw_pick(pick)
#
#     if pts is None or pts == 'X':
#         return 0
#     else:
#         return int(pts)


def cast_raw_pick(raw_pick):
    team, wagered_pts, status = parse_raw_pick(raw_pick)
    return Pick(team, wagered_pts, status=='correct')
