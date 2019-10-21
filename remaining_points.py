import os

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver


# TODO: Headless browser interactions?
# TODO: Download an example HTML file (and add to git) to demonstrate functionality without internet connection?
# TODO: Possible to modify the actual HTML displayed in the browser?
# TODO: Type hinting, docstrings


def login(user_id, password):
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


def get_picks_table_html():

    # TODO: Support other leagues? i.e. Don't hard-code my league's URL
    # TODO: Implement selecting the desired pick week

    # Navigate to picks page
    picks_url = 'http://football-guys.football.cbssports.com/office-pool/standings/live'
    driver.get(picks_url)

    # Find the picks table element, and then return its HTML to be scraped
    picks_table_elem = driver.find_element_by_id('nflpicks')  # <table id="nflpicks">
    table_html = picks_table_elem.get_attribute('outerHTML')  # Get raw HTML of the table element

    return table_html


def parse_picks_table_html(html):
    """
    Parse the raw HTML of the NFL weekly picks table and output it as a DataFrame.

    Args:
        html (str): Raw HTML string of the <table id="nflpicks"> element

    Return:
        (pd.DataFrame): DataFrame representing the NFL weekly picks table.
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
    for td in game_row.contents[1:-3]:

        # Each cell is a small table depicting the game matchup
        for table in td.contents:

            # Grab the table body
            tbody = table.contents[0]

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

            home_team = tbody.contents[0].contents[0].text
            away_team = tbody.contents[1].contents[0].text

            games.append(f"{home_team}|{away_team}")

    #
    # STEP 2: Extract each player's row from the main picks table
    #

    # Table format is:
    # | Player | game 1 pick | game 2 pick | ... | game n pick | MNF Points Tiebreaker | Weekly Points | YTD Points |

    # Container to hold each row of data from the table. Each row will stored as list, `row_data` will be list of lists.
    row_data = []

    # Get the Tag representing the pick rows (<tbody id="nflplayerRows">)
    player_rows = soup.find('tbody', {'id': 'nflplayerRows'})

    # Iterate over the rows in the table (the <tr> elements)
    for tr in player_rows.contents:
        row = []
        # If players have not made their picks for the week, they will have a single cell spanning all games.
        for td in tr.contents:
            if not td.attrs.get('colspan'):
                row.append(td.text)
            else:
                row.extend([None] * int(td.attrs['colspan']))
        row_data.append(row)

    columns = ['player'] + games + ['mnf_tiebreaker', 'weekly_points', 'ytd_points']

    return pd.DataFrame(row_data, columns=columns)


if __name__ == '__main__':

    # Instantiate a chrome webdriver for browser interactions
    driver = webdriver.Chrome()  # TODO: Pass the explicit path to the driver in the venv/bin/?

    try:
        # Login to cbssports.com
        login(user_id=os.environ.get('USERID'), password=os.environ.get('PASSWORD'))

        # Navigate the the weekly game picks table page and retrieve the table HTML
        picks_table_html = get_picks_table_html()

        # Parse the picks table HTML for relevant data, and read it into a DataFrame
        picks_df = parse_picks_table_html(picks_table_html)

        print(picks_df.to_string())

    finally:
        driver.quit()
