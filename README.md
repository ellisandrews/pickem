# pickem

A simple webscraping tool for my cbssports.com NFL weekly pickem league.

## Quickstart

### Setup
Install the required packages in your **_python3_** virtual environment.

```
pip3 install -r requirements.txt
```

Install a webdriver. [See below](#webdriver-installation) for details.

Set your cbssports.com User ID and password for login as environment variables

```
export USERID=<your_userid>
export PASSWORD=<your_password>
```

### Execution

```
python remaining_points.py
```

## Tips

### Webdriver Installation

This project uses the python package `selenium` to mimic web browser interactions such as logging in and navigating to
the page(s) we want to scrape. This requires downloading a webdriver and putting it in your PATH. I chose to download
the Chrome webdriver (for the Chrome version I currently have installed -- Version 76). I then put this executable in
my virtualenv's `bin/` directory. More information about webdrivers can be found in
[selenium's documentation](https://selenium-python.readthedocs.io/installation.html#drivers).

