#!/usr/bin/env python3
"""
Facebook Group Tool — Terminal CLI
Usage: python cli.py
"""

import asyncio
import json
import os
import random
import sys
from playwright.async_api import async_playwright

# ─── Config ───────────────────────────────────────────────────────────────────
SESSION_FILE    = "facebook_session.json"
GROUPS_FILE     = "groups.json"
JOINED_FILE     = "joined_groups.json"
MAX_SCROLLS     = 8
SCROLL_PAUSE    = 2.5
MAX_GROUPS      = 50
DELAY_BETWEEN   = (10, 30)   # seconds between actions

# ─── Colors ───────────────────────────────────────────────────────────────────
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    GREEN  = "\033[92m"
    RED    = "\033[91m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    BLUE   = "\033[94m"
    DIM    = "\033[2m"

def ok(msg):    print(f"{C.GREEN}✅ {msg}{C.RESET}")
def err(msg):   print(f"{C.RED}❌ {msg}{C.RESET}")
def warn(msg):  print(f"{C.YELLOW}⚠️  {msg}{C.RESET}")
def info(msg):  print(f"{C.CYAN}ℹ️  {msg}{C.RESET}")
def step(msg):  print(f"{C.BLUE}➤  {msg}{C.RESET}")
def dim(msg):   print(f"{C.DIM}{msg}{C.RESET}")

def banner():
    print(f"""
{C.BOLD}{C.CYAN}╔══════════════════════════════════════╗
║     Facebook Group Tool  v1.0        ║
╚══════════════════════════════════════╝{C.RESET}
""")

def menu():
    session_status = f"{C.GREEN}Logged in{C.RESET}" if os.path.exists(SESSION_FILE) else f"{C.RED}Not logged in{C.RESET}"
    groups_count = 0
    if os.path.exists(GROUPS_FILE):
        try:
            groups_count = len(json.load(open(GROUPS_FILE)))
        except: pass
    joined_count = 0
    if os.path.exists(JOINED_FILE):
        try:
            joined_count = len(json.load(open(JOINED_FILE)))
        except: pass

    print(f"\n{C.BOLD}Status:{C.RESET} {session_status}  |  "
          f"Groups saved: {C.CYAN}{groups_count}{C.RESET}  |  "
          f"Joined: {C.CYAN}{joined_count}{C.RESET}\n")
    print(f"{C.BOLD}  [1]{C.RESET} Login to Facebook")
    print(f"{C.BOLD}  [2]{C.RESET} Load session from file")
    print(f"{C.BOLD}  [3]{C.RESET} Search groups")
    print(f"{C.BOLD}  [4]{C.RESET} Join groups")
    print(f"{C.BOLD}  [5]{C.RESET} Post to groups")
    print(f"{C.BOLD}  [6]{C.RESET} Leave joined groups")
    print(f"{C.BOLD}  [7]{C.RESET} View saved groups")
    print(f"{C.BOLD}  [0]{C.RESET} Exit")
    print()

# ─── Browser helpers ──────────────────────────────────────────────────────────

async def make_context(playwright, use_session=True):
    browser = await playwright.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox',
              '--disable-blink-features=AutomationControlled']
    )
    opts = {
        "user_agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "locale": "en-US",
        "viewport": {"width": 1280, "height": 800},
    }
    if use_session and os.path.exists(SESSION_FILE):
        opts["storage_state"] = SESSION_FILE
    ctx = await browser.new_context(**opts)
    return browser, ctx

async def dismiss_cookies(page):
    for sel in [
        '[data-testid="cookie-policy-manage-dialog-accept-button"]',
        'button:has-text("Allow all cookies")',
        'button:has-text("Accept All")',
        'button:has-text("Allow Essential and Optional Cookies")',
        '[data-cookiebanner="accept_button"]',
    ]:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=2000):
                await btn.click()
                await page.wait_for_timeout(1500)
                return
        except:
            continue

# ─── 1. Login ─────────────────────────────────────────────────────────────────

async def do_login():
    print()
    email    = input(f"{C.CYAN}  Facebook email/phone: {C.RESET}").strip()
    password = input(f"{C.CYAN}  Password:             {C.RESET}").strip()

    step("Launching browser and logging in...")

    try:
        async with async_playwright() as p:
            browser, ctx = await make_context(p, use_session=False)
            page = await ctx.new_page()

            await page.goto("https://www.facebook.com", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)
            await dismiss_cookies(page)

            await page.wait_for_selector('input[name="email"]', timeout=20000)
            await page.type('input[name="email"]', email, delay=50)
            await page.wait_for_timeout(400)
            await page.type('input[name="pass"]', password, delay=50)
            await page.wait_for_timeout(600)

            # Click login — 4 fallbacks
            clicked = False
            for sel in ['button[name="login"]', 'input[type="submit"]',
                        'button:has-text("Log in")', 'button:has-text("Log In")']:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=3000):
                        await btn.click()
                        clicked = True
                        break
                except: continue
            if not clicked:
                await page.press('input[name="pass"]', "Enter")

            await page.wait_for_timeout(10000)

            # 2FA
            if await page.locator('input[name="approvals_code"]').count() > 0:
                code = input(f"{C.YELLOW}  2FA code required: {C.RESET}").strip()
                await page.fill('input[name="approvals_code"]', code)
                await page.press('input[name="approvals_code"]', "Enter")
                await page.wait_for_timeout(5000)

            url = page.url
            logged_in = "facebook.com" in url and "login" not in url and "checkpoint" not in url
            if not logged_in:
                try:
                    await page.wait_for_selector(
                        '[aria-label="Your profile"], [data-testid="nav-small-profile-pic"]',
                        timeout=5000
                    )
                    logged_in = True
                except: pass

            if logged_in:
                await ctx.storage_state(path=SESSION_FILE)
                await browser.close()
                ok("Login successful! Session saved.")
            else:
                await browser.close()
                err("Login failed. Check your credentials and try again.")

    except Exception as e:
        err(f"Login error: {e}")

# ─── 2. Load session from file ────────────────────────────────────────────────

def do_load_session():
    print()
    path = input(f"{C.CYAN}  Path to session JSON file: {C.RESET}").strip().strip('"').strip("'")
    if not os.path.exists(path):
        err(f"File not found: {path}")
        return

    try:
        with open(path, encoding='utf-8') as f:
            content = f.read()
        data = json.loads(content)
    except Exception as e:
        err(f"Couldn't read file: {e}")
        return

    # Validate
    if "cookies" not in data or not isinstance(data["cookies"], list) or not data["cookies"]:
        err("Invalid session file — missing or empty 'cookies' list.")
        return

    fb_cookies = [c for c in data["cookies"] if "facebook.com" in c.get("domain", "")]
    if not fb_cookies:
        err("No facebook.com cookies found. Is this a Facebook session file?")
        return

    auth_cookies = [c for c in fb_cookies if c.get("name") in ("c_user", "xs", "fr")]
    if len(auth_cookies) < 2:
        warn(f"Session may be incomplete — only {len(auth_cookies)} auth cookie(s) found (need c_user + xs).")
        confirm = input("  Save anyway? (yes/no): ").strip().lower()
        if confirm != "yes":
            info("Cancelled.")
            return

    with open(SESSION_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    ok(f"Session loaded! ({len(fb_cookies)} Facebook cookies found)")

# ─── 3. Search groups ─────────────────────────────────────────────────────────

async def do_search():
    if not os.path.exists(SESSION_FILE):
        err("Not logged in. Use option 1 or 2 first.")
        return

    print()
    keyword = input(f"{C.CYAN}  Search keyword: {C.RESET}").strip()
    if not keyword:
        warn("No keyword entered.")
        return

    step(f"Searching Facebook groups for: '{keyword}'...")

    try:
        async with async_playwright() as p:
            browser, ctx = await make_context(p)
            page = await ctx.new_page()

            url = f"https://www.facebook.com/groups/search/?q={keyword.replace(' ', '%20')}"
            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_timeout(5000)

            groups = []
            for i in range(MAX_SCROLLS):
                print(f"  Scrolling... ({i+1}/{MAX_SCROLLS})  found {len(groups)} so far", end='\r')
                links = await page.evaluate("""() => {
                    return Array.from(document.querySelectorAll('a[href*="facebook.com/groups/"]'))
                        .map(a => a.href.split('?')[0])
                        .filter(h =>
                            h.includes('/groups/') &&
                            !h.includes('/search') &&
                            !h.includes('/members') &&
                            !h.includes('/about') &&
                            !h.endsWith('/groups/')
                        )
                }""")
                for link in links:
                    if link not in groups:
                        groups.append(link)
                await page.evaluate("window.scrollBy(0, 1000)")
                await asyncio.sleep(SCROLL_PAUSE)

            groups = list(set(groups))[:MAX_GROUPS]
            print()
            with open(GROUPS_FILE, 'w') as f:
                json.dump(groups, f, indent=2)
            await browser.close()

        if groups:
            ok(f"Found {len(groups)} groups for '{keyword}' — saved to {GROUPS_FILE}")
        else:
            warn("No groups found. Try a different keyword.")

    except Exception as e:
        err(f"Search error: {e}")

# ─── 4. Join groups ───────────────────────────────────────────────────────────

async def do_join():
    if not os.path.exists(SESSION_FILE):
        err("Not logged in. Use option 1 or 2 first.")
        return
    if not os.path.exists(GROUPS_FILE):
        err("No groups found. Run Search first (option 3).")
        return

    with open(GROUPS_FILE) as f:
        groups = json.load(f)
    if not groups:
        err("Groups list is empty.")
        return

    print()
    info(f"{len(groups)} groups available.")
    try:
        count_input = input(f"{C.CYAN}  How many to join? (Enter for all {len(groups)}): {C.RESET}").strip()
        count = int(count_input) if count_input else len(groups)
        count = min(count, len(groups))
    except ValueError:
        err("Invalid number.")
        return

    step(f"Joining {count} groups... (press Ctrl+C to stop early)")
    print()

    joined_urls = _load_json(JOINED_FILE)

    try:
        async with async_playwright() as p:
            browser, ctx = await make_context(p)
            page = await ctx.new_page()

            joined = 0
            for i, url in enumerate(groups[:count]):
                print(f"  [{i+1}/{count}] ", end='')
                try:
                    await page.goto(url, timeout=60000, wait_until="domcontentloaded")
                    await page.wait_for_timeout(random.randint(3000, 6000))

                    join_button = None
                    for sel in [
                        '[aria-label="Join group"]', 'div[aria-label="Join group"]',
                        'button:has-text("Join Group")', 'button:has-text("Join")',
                        'a:has-text("Join Group")',
                    ]:
                        try:
                            btn = page.locator(sel).first
                            if await btn.count() > 0:
                                join_button = btn
                                break
                        except: continue

                    if join_button:
                        await join_button.click()
                        joined += 1
                        if url not in joined_urls:
                            joined_urls.append(url)
                        ok(f"Joined: {url}")
                    else:
                        warn(f"Already member or closed: {url}")

                    delay = random.randint(*DELAY_BETWEEN)
                    print(f"  {C.DIM}Waiting {delay}s...{C.RESET}")
                    await asyncio.sleep(delay)

                except KeyboardInterrupt:
                    print()
                    warn("Stopped by user.")
                    break
                except Exception as e:
                    err(f"Error: {str(e)[:100]}")

            _save_json(JOINED_FILE, joined_urls)
            await ctx.storage_state(path=SESSION_FILE)
            await browser.close()
            print()
            ok(f"Done! Joined {joined}/{count} groups.")

    except KeyboardInterrupt:
        warn("Stopped.")
    except Exception as e:
        err(f"Join error: {e}")

# ─── 5. Post to groups ────────────────────────────────────────────────────────

async def do_post():
    if not os.path.exists(SESSION_FILE):
        err("Not logged in. Use option 1 or 2 first.")
        return
    if not os.path.exists(GROUPS_FILE):
        err("No groups found. Run Search first (option 3).")
        return

    with open(GROUPS_FILE) as f:
        groups = json.load(f)
    if not groups:
        err("Groups list is empty.")
        return

    print()
    info(f"{len(groups)} groups available.")
    try:
        count_input = input(f"{C.CYAN}  How many groups to post to? (Enter for all {len(groups)}): {C.RESET}").strip()
        count = int(count_input) if count_input else len(groups)
        count = min(count, len(groups))
    except ValueError:
        err("Invalid number.")
        return

    print()
    print(f"{C.CYAN}  Post text (type your message, press Enter twice when done):{C.RESET}")
    lines = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    post_text = "\n".join(lines).strip()

    if not post_text:
        err("Post text is empty.")
        return

    print()
    image_path = input(f"{C.CYAN}  Image path (optional, press Enter to skip): {C.RESET}").strip().strip('"').strip("'")
    if image_path and not os.path.exists(image_path):
        warn(f"Image not found at '{image_path}' — posting without image.")
        image_path = None

    step(f"Posting to {count} groups... (press Ctrl+C to stop early)")
    print()

    try:
        async with async_playwright() as p:
            browser, ctx = await make_context(p)
            page = await ctx.new_page()

            posted = 0
            failed = 0
            for i, url in enumerate(groups[:count]):
                print(f"  [{i+1}/{count}] ", end='', flush=True)
                try:
                    await page.goto(url, timeout=60000, wait_until="domcontentloaded")
                    await page.wait_for_timeout(random.randint(3000, 6000))

                    # Open composer
                    composer_opened = False
                    for sel in [
                        '//span[contains(text(), "Write something...")]',
                        '//span[contains(text(), "What\'s on your mind")]',
                        '[aria-label="Write something..."]',
                        '[aria-label="Create a public post…"]',
                    ]:
                        try:
                            el = page.locator(sel).first
                            if await el.is_visible(timeout=4000):
                                await el.click()
                                composer_opened = True
                                break
                        except: continue

                    if not composer_opened:
                        warn(f"Can't open composer: {url}")
                        failed += 1
                        continue

                    await page.wait_for_timeout(2000)

                    # Find text area
                    text_area = None
                    for sel in [
                        "//div[@role='dialog']//div[@contenteditable='true']",
                        "div[contenteditable='true'][role='textbox']",
                        "div[contenteditable='true']",
                    ]:
                        try:
                            el = page.locator(sel).first
                            if await el.is_visible(timeout=3000):
                                text_area = el
                                break
                        except: continue

                    if not text_area:
                        warn(f"Can't find text box: {url}")
                        failed += 1
                        continue

                    await text_area.click()
                    await text_area.fill(post_text)
                    await page.wait_for_timeout(1500)

                    # Attach image
                    if image_path:
                        try:
                            for photo_sel in ['[aria-label="Photo/video"]', 'button:has-text("Photo")']:
                                try:
                                    btn = page.locator(photo_sel).first
                                    if await btn.is_visible(timeout=3000):
                                        await btn.click()
                                        await page.wait_for_timeout(1500)
                                        break
                                except: continue
                            async with page.expect_file_chooser() as fc_info:
                                await page.locator('input[type="file"]').first.click()
                            fc = await fc_info.value
                            await fc.set_files(image_path)
                            await page.wait_for_timeout(4000)
                        except Exception as img_e:
                            warn(f"Couldn't attach image: {img_e}")

                    # Click Post
                    post_clicked = False
                    for sel in [
                        "//div[@role='dialog']//div[@aria-label='Post']",
                        "//div[@role='dialog']//div[@aria-label='Share']",
                        'button:has-text("Post")', '[aria-label="Post"]',
                    ]:
                        try:
                            btn = page.locator(sel).first
                            if await btn.is_visible(timeout=4000):
                                await btn.click()
                                post_clicked = True
                                break
                        except: continue

                    if not post_clicked:
                        warn(f"Couldn't click Post: {url}")
                        failed += 1
                        continue

                    await page.wait_for_timeout(5000)
                    posted += 1
                    ok(f"Posted: {url}")

                    delay = random.randint(*DELAY_BETWEEN)
                    print(f"  {C.DIM}Waiting {delay}s...{C.RESET}")
                    await asyncio.sleep(delay)

                except KeyboardInterrupt:
                    print()
                    warn("Stopped by user.")
                    break
                except Exception as e:
                    failed += 1
                    err(f"Failed: {url} — {str(e)[:100]}")

            await ctx.storage_state(path=SESSION_FILE)
            await browser.close()
            print()
            ok(f"Posting complete! Posted: {posted}  Failed: {failed}")

    except KeyboardInterrupt:
        warn("Stopped.")
    except Exception as e:
        err(f"Post error: {e}")

# ─── 6. Leave joined groups ───────────────────────────────────────────────────

async def do_leave():
    if not os.path.exists(SESSION_FILE):
        err("Not logged in. Use option 1 or 2 first.")
        return

    joined = _load_json(JOINED_FILE)
    if not joined:
        err(f"No joined groups on record ({JOINED_FILE} is empty or missing).")
        return

    print()
    info(f"{len(joined)} joined groups on record.")
    confirm = input(f"{C.YELLOW}  Leave all {len(joined)} groups? (yes/no): {C.RESET}").strip().lower()
    if confirm != "yes":
        info("Cancelled.")
        return

    step(f"Leaving {len(joined)} groups... (press Ctrl+C to stop early)")
    print()

    remaining = list(joined)

    try:
        async with async_playwright() as p:
            browser, ctx = await make_context(p)
            page = await ctx.new_page()

            left = 0
            failed = 0
            for i, url in enumerate(joined):
                print(f"  [{i+1}/{len(joined)}] ", end='', flush=True)
                try:
                    await page.goto(url, timeout=60000, wait_until="domcontentloaded")
                    await page.wait_for_timeout(random.randint(3000, 5000))

                    leave_clicked = False
                    for sel in [
                        '[aria-label="Joined"]', 'div[aria-label="Joined"]',
                        'button:has-text("Joined")', '[aria-label="Member"]',
                        'button:has-text("Member")',
                    ]:
                        try:
                            btn = page.locator(sel).first
                            if await btn.is_visible(timeout=4000):
                                await btn.click()
                                await page.wait_for_timeout(1500)
                                leave_clicked = True
                                break
                        except: continue

                    if not leave_clicked:
                        warn(f"Not a member or button not found: {url}")
                        failed += 1
                        continue

                    for sel in [
                        'span:has-text("Leave group")',
                        '[aria-label="Leave group"]',
                        'div[role="menuitem"]:has-text("Leave")',
                    ]:
                        try:
                            btn = page.locator(sel).first
                            if await btn.is_visible(timeout=3000):
                                await btn.click()
                                await page.wait_for_timeout(1500)
                                break
                        except: continue

                    # Confirm dialog
                    for sel in [
                        'div[aria-label="Leave Group"]',
                        'button:has-text("Leave Group")',
                        'div[role="dialog"] button:has-text("Leave")',
                    ]:
                        try:
                            btn = page.locator(sel).first
                            if await btn.is_visible(timeout=3000):
                                await btn.click()
                                break
                        except: continue

                    await page.wait_for_timeout(2000)
                    left += 1
                    remaining.remove(url)
                    ok(f"Left: {url}")

                    delay = random.randint(5, 15)
                    print(f"  {C.DIM}Waiting {delay}s...{C.RESET}")
                    await asyncio.sleep(delay)

                except KeyboardInterrupt:
                    print()
                    warn("Stopped by user.")
                    break
                except Exception as e:
                    failed += 1
                    err(f"Error leaving {url}: {str(e)[:100]}")

            _save_json(JOINED_FILE, remaining)
            await ctx.storage_state(path=SESSION_FILE)
            await browser.close()
            print()
            ok(f"Done! Left: {left}  Failed: {failed}  Remaining in log: {len(remaining)}")

    except KeyboardInterrupt:
        warn("Stopped.")
    except Exception as e:
        err(f"Leave error: {e}")

# ─── 7. View saved groups ─────────────────────────────────────────────────────

def do_view_groups():
    print()
    if not os.path.exists(GROUPS_FILE):
        warn("No groups file found. Run Search first.")
        return
    groups = _load_json(GROUPS_FILE)
    joined = _load_json(JOINED_FILE)
    if not groups:
        warn("Groups list is empty.")
        return
    print(f"{C.BOLD}  Saved groups ({len(groups)}):{C.RESET}")
    for i, url in enumerate(groups, 1):
        tag = f" {C.GREEN}[joined]{C.RESET}" if url in joined else ""
        print(f"  {C.DIM}{i:>3}.{C.RESET} {url}{tag}")

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _load_json(path):
    if not os.path.exists(path):
        return []
    try:
        return json.load(open(path))
    except:
        return []

def _save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

# ─── Main loop ────────────────────────────────────────────────────────────────

async def main():
    banner()
    while True:
        try:
            menu()
            choice = input(f"{C.BOLD}  Choose an option: {C.RESET}").strip()
            print()

            if   choice == "1": await do_login()
            elif choice == "2": do_load_session()
            elif choice == "3": await do_search()
            elif choice == "4": await do_join()
            elif choice == "5": await do_post()
            elif choice == "6": await do_leave()
            elif choice == "7": do_view_groups()
            elif choice == "0":
                print(f"{C.CYAN}  Bye!{C.RESET}\n")
                break
            else:
                warn("Invalid option. Enter a number 0–7.")

        except KeyboardInterrupt:
            print(f"\n{C.YELLOW}  Use option 0 to exit.{C.RESET}")

if __name__ == "__main__":
    asyncio.run(main())
