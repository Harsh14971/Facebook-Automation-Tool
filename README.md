GroupFlow CLI

A terminal-based Python application for learning browser automation, session management, and Playwright automation.

Features

- Login using Facebook credentials
- Import existing Facebook session files
- Save and reuse login sessions
- Search groups by keyword
- Save discovered groups locally
- Join groups
- Leave joined groups
- Post content to groups
- View saved groups
- Chromium browser automation using Playwright

Requirements

- Python 3.10+
- Playwright
- Chromium Browser

Installation

Install Playwright:

pip install playwright

Install Chromium:

playwright install chromium

Run

python cli.py

Files

- "cli.py" — Main application
- "groups.json" — Stores discovered groups
- "facebook_session.json" — Created automatically after login or session import
- "joined_groups.json" — Created automatically when joining groups

Educational Purpose

This project was created for educational and research purposes related to:

- Python Programming
- Browser Automation
- Session Management
- Playwright Automation
- Command Line Applications
- JSON Data Handling

Security Notes

- Never share session files publicly.
- Never upload session files to GitHub.
- Never commit credentials or tokens.
- Use a ".gitignore" file to exclude sensitive data.

Example ".gitignore":

facebook_session.json
*_session.json
joined_groups.json
.env
pycache/
*.pyc
*.log

Disclaimer

This software is provided for educational and research purposes only.

Users are responsible for ensuring that their use of this software complies with applicable laws, regulations, and platform policies.

The author assumes no responsibility for misuse of this software or any consequences arising from its use.

License

Licensed under the MIT License.
See the LICENSE file for details.