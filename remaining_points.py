import os
from argparse import ArgumentParser

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver

from utils import cast_raw_pick

# TODO: DELETE THIS IMPORT
from pprint import pprint


# TODO: Headless browser interactions?
# TODO: Download an example HTML file (and add to git) to demonstrate functionality without internet connection?
# TODO: Possible to modify the actual HTML displayed in the browser?
# TODO: Type hinting, docstrings


def login(user_id: str, password: str) -> None:
    """
    Navigate to the cbssports.com login page and submit login credentials.

    Args:
        user_id:   cbssports.com user_id
        password:  cbssports.com password
    """
    # Navigate to the login page
    login_url = 'https://www.cbssports.com/login'
    driver.get(login_url)

    # Find the login form elements
    userid_elem = driver.find_element_by_id('userid')      # <input id="userid"> login form element
    password_elem = driver.find_element_by_id('password')  # <input id="password"> login form element
    submit_elem = driver.find_element_by_name('_submit')   # <input name="_submit"> login form element

    # Fill the username field
    userid_elem.clear()
    userid_elem.send_keys(user_id)

    # Fill the password field
    password_elem.clear()
    password_elem.send_keys(password)

    # Click the submit button
    submit_elem.click()


def get_picks_table_html() -> str:
    """
    Navigate to the cbssports.com NFL pickem league weekly picks page, and retrieve the HTML for the weekly picks table.
    """
    # TODO: Support other leagues? i.e. Don't hard-code my league's URL
    # TODO: Implement selecting the desired pick week?

    # Navigate to picks page
    picks_url = 'http://football-guys.football.cbssports.com/office-pool/standings/live'
    driver.get(picks_url)

    # Find the picks table element, and then return its HTML to be scraped
    picks_table_elem = driver.find_element_by_id('nflpicks')  # <table id="nflpicks">
    table_html = picks_table_elem.get_attribute('outerHTML')  # Get raw HTML of the table element

    return table_html


def parse_picks_table_html(html: str) -> pd.DataFrame:
    """
    Parse the raw HTML of the NFL weekly picks table and output it as a DataFrame.

    Args:
        html: Raw HTML string of the <table id="nflpicks"> element

    Return:
        DataFrame representing the NFL weekly picks table.
    """
    # Parse the picks table HTML with BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')

    #
    # STEP 1: Get the slate of games being played on the given week
    #

    # Get the table header row that specifies which NFL games are being played
    game_row = soup.find('tr', {'id': 'nflheader'})

    # List to hold the games being played this week (list items will be strings of the format: "home_team|away_team")
    games = []

    # Iterate over the games in the header row (exclude the non-game columns)
    for td in game_row.find_all('td')[1:-3]:

        # Each cell is a small table depicting the game matchup
        for table in td.find_all('table'):

            # Grab the table body
            tbody = table.find('tbody')

            # Grab the two teams playing. HTML looks like:
            #  <tbody>
            #    <tr>
            #      <td>home_team</td>
            #      <td>home_score</td>
            #    </tr>
            #    <tr>
            #      <td>away_team</td>
            #      <td>away_score</td>
            #    </tr>
            #  </tbody>


            home_row, away_row = tbody.find_all('tr')

            home_team = home_row.find('td').text
            away_team = away_row.find('td').text

            games.append(f"{home_team}|{away_team}")

    #
    # STEP 2: Extract each player's row from the main picks table
    #

    # Table format is:
    # | Player | game 1 pick | game 2 pick | ... | game n pick | MNF Points Tiebreaker | Weekly Points | YTD Points |

    # Container to hold each row of data from the table. Each row will be stored as list.
    row_data = []

    # Get the Tag representing the pick rows (<tbody id="nflplayerRows">)
    player_rows = soup.find('tbody', {'id': 'nflplayerRows'})

    # Iterate over the rows in the table (the <tr> elements)
    for tr in player_rows.find_all('tr'):

        row = []

        # Handle table cells for game week picks and MNF tiebreaker
        for td in tr.find_all('td')[:-2]:

            # If players have not made their picks for the week, they will have a single cell spanning all games.
            if td.attrs.get('colspan'):
                row.extend([None] * int(td.attrs['colspan']))
            else:
                pick = td.text  # Get the pick the user made (e.g. 'KC(11)' )

                # Get the class attribute of the td element (e.g. <td class="correct">... )
                class_ = td.attrs.get('class')

                if class_:
                    if 'correct' in class_:
                        status = 'correct'
                    elif 'incorrect' in class_:
                        status = 'incorrect'
                    elif 'unlocked' in class_:
                        status = 'hidden'
                    else:
                        status = 'unknown'
                else:
                    status = 'unknown'

                row.append(f"{pick}:{status}")

        row_data.append(row)

        # Handle table cells for weekly and yearly totals
        for td in tr.find_all('td')[-2:]:
            row.append(int(td.text))

    # DataFrame column headers
    columns = ['player'] + games + ['mnf_tiebreaker', 'weekly_pts', 'ytd_pts']

    # Dump data into DF
    df = pd.DataFrame(row_data, columns=columns)

    return df


def calculate_remaining_pts(df: pd.DataFrame) -> pd.DataFrame:

    # Calculate:
    #    1) How many total remaining points each player has left to wager
    #    2) Which specific point values each user has left to wager
    #    3) The maximum possible score the user could achieve on the week (correct points + total left to wager)

    # 1) Remaining points = Total weekly points possible - SUM(wagered_points)

    # Deep copy the DataFrame. We'll be adding/modifying columns and do not want to modify the original DF in case we
    # want to use it elsewhere, given that it's an unadulterated representation of the scraped HTML table.
    df = df.copy()

    num_games = len(df.columns) - 4  # Number of games in the given week
    weekly_values = sorted(range(1, num_games+1))  # Point values eligible to be wagered given number of games
    max_pts = sum(weekly_values)  # Max number of points possible given number of games

    # Extract the point value wagered by each player on each of the games, and make this the new column value
    for column in df.columns[1:num_games+1]:
        df[column] = df[column].apply(lambda raw_pick: cast_raw_pick(raw_pick).points)

    # Add a column that is the number of (visible) points each player has wagered thus far, and how many they have left
    #  to wager
    df['wagered_pts'] = df.iloc[:, 1:num_games+1].sum(axis=1)
    df['remaining_pts'] = max_pts - df['wagered_pts']

    df['max_possible_pts'] = df['weekly_pts'] + df['remaining_pts']

    return df


def format_picks_df(df: pd.DataFrame) -> pd.DataFrame:

    # Deep copy the DataFrame. We'll be adding/modifying columns and do not want to modify the original DF in case we
    # want to use it elsewhere, given that it's an unadulterated representation of the scraped HTML table.
    df = df.copy()

    num_games = len(df.columns) - 4  # Number of games in the given week
    weekly_values = sorted(range(1, num_games + 1))  # Point values eligible to be wagered given the number of games
    max_pts = sum(weekly_values)  # Max number of points possible given number of games

    # Extract the point value wagered by each player on each of the games, and make this the new column value
    for column in df.columns[1:num_games + 1]:
        df[column] = df[column].apply(cast_raw_pick)

    return df


if __name__ == '__main__':

    a = ArgumentParser()

    a.add_argument('--test_data', '-t', action='store_true',
                   help='Run the script using saved example HTML, skipping login and other browser interactions.')

    a.add_argument('--player_name', '-p', type=str, default='Ellis Andrews',
                   help='Your own player name on CBS.')

    args = a.parse_args()

    # Read the sample data if desired (for testing, running without internet, etc.)
    if args.test_data:
        with open('test_data/picks_table_week_7.html', 'r') as f:  # TODO: Absolute path
            picks_table_html = f.read()

    # Otherwise, retrieve the picks table data from the internet
    else:
        # Instantiate a chrome webdriver for browser interactions
        driver = webdriver.Chrome()

        try:
            # Login to cbssports.com
            login(os.environ.get('USERID'), os.environ.get('PASSWORD'))

            # Navigate the the weekly game picks table page and retrieve the table HTML
            picks_table_html = get_picks_table_html()

        finally:
            driver.quit()

    # TODO: Save (pickle? cache somehow?) the picks_table_html so don't have to wait for browser if running again.

    # Parse the picks table HTML for relevant data, and read it into a DataFrame
    picks_df = parse_picks_table_html(picks_table_html)

    print(picks_df.to_string())
    print()

    # sandbox_df = format_picks_df(picks_df)

    # print(sandbox_df.to_string())

    # # TODO: Allow user to check "What if x game flipped?" scenario. Or even "What if x, y, z games flipped?"
    # # TODO: Instead of the above, let a user input a list of winners of each game and then see what would happen

    # Calculate how many total points each player has left to wager on the given week
    remaining_pts_df = calculate_remaining_pts(picks_df)

    print(remaining_pts_df.to_string())
    print()
