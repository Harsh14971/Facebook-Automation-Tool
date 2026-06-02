# Facebook Group Tool CLI

A terminal-based Facebook group management tool built with Python and Playwright.

## Features

- Login with Facebook credentials
- Import an existing Facebook session JSON file
- Save and reuse login sessions
- Search Facebook groups by keyword
- Save discovered groups locally
- Join groups from saved search results
- Post content to saved groups
- Leave previously joined groups
- View saved groups from the terminal

## Requirements

- Python 3.10+
- Playwright
- Chromium browser

## Installation

Install Playwright:

pip install playwright

Install Chromium:

playwright install chromium

## Run

python cli.py

## Files

- cli.py — Main application
- groups.json — Stores discovered groups
- facebook_session.json — Created automatically after login/session import
- joined_groups.json — Created automatically when joining groups

## Menu

1. Login to Facebook
2. Load session from file
3. Search groups
4. Join groups
5. Post to groups
6. Leave joined groups
7. View saved groups
0. Exit

## Disclaimer

This project is provided for educational and research purposes only.

Users are responsible for complying with applicable laws, platform policies, and terms of service. The author is not responsible for misuse of this software.

## License

MIT License
