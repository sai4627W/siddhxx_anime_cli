import os
import time
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-secret")

# Global storage
search_results = []
episode_list = []
current_anime_url = ""


def setup_selenium():
    """Setup Selenium with headless Chrome using webdriver-manager."""
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--mute-audio")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        )

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        print(f"Selenium setup error: {e}")
        return None


def search_anime(anime_name):
    """Search for anime on animegg.org."""
    try:
        query = anime_name.replace(" ", "+")
        resp = requests.get(f"https://www.animegg.org/search/?q={query}", timeout=10)
        soup = BeautifulSoup(resp.content, "html.parser")
        links = soup.find_all("a", class_="mse")
        results = []
        for a in links:
            href = a.get("href")
            if href:
                title = href.rsplit("/", 1)[-1].replace("-", " ").title()
                results.append({
                    "title": title,
                    "href": href,
                    "url": f"https://www.animegg.org{href}"
                })
        return results
    except Exception as e:
        print(f"Search error: {e}")
        return []


def get_episodes(anime_url):
    """Get list of episodes for the selected anime."""
    try:
        resp = requests.get(anime_url, timeout=10)
        soup = BeautifulSoup(resp.content, "html.parser")
        links = soup.find_all("a", class_="anm_det_pop")
        episodes = []
        for a in links:
            href = a.get("href")
            if href:
                ep_title = href.rsplit("/", 1)[-1].replace("-", " ").title()
                episodes.append({
                    "title": ep_title,
                    "href": href,
                    "url": f"https://www.animegg.org{href}"
                })
        return episodes
    except Exception as e:
        print(f"Episodes error: {e}")
        return []


def extract_streaming_links(episode_url, language):
    """Use Selenium to extract streaming iframe links."""
    try:
        url = episode_url + ("#subbed" if language == "sub" else "#dubbed")
        driver = setup_selenium()
        if not driver:
            return []
        driver.get(url)
        time.sleep(3)
        iframes = driver.find_elements("tag name", "iframe")
        links = [iframe.get_attribute("src") for iframe in iframes if iframe.get_attribute("src")]
        driver.quit()
        # Exclude last if redundant
        return links[:-1] if len(links) > 1 else links
    except Exception as e:
        print(f"Extraction error: {e}")
        return []


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/search", methods=["POST"])
def do_search():
    global search_results
    name = request.form.get("anime_name", "").strip()
    if not name:
        flash("Please enter an anime name!", "error")
        return redirect(url_for("home"))
    search_results = search_anime(name)
    if not search_results:
        flash("No anime found. Try another search.", "error")
        return redirect(url_for("home"))
    return render_template("search_results.html", results=search_results, anime_name=name)


@app.route("/episodes/<int:anime_index>")
def episodes(anime_index):
    global episode_list, current_anime_url
    if 0 <= anime_index < len(search_results):
        selected = search_results[anime_index]
        current_anime_url = selected["url"]
        episode_list = get_episodes(current_anime_url)
        if not episode_list:
            flash("No episodes found for this anime.", "error")
            return redirect(url_for("home"))
        return render_template("episodes.html", episodes=episode_list, anime_title=selected["title"])
    flash("Invalid selection!", "error")
    return redirect(url_for("home"))


@app.route("/watch/<int:episode_index>")
def watch(episode_index):
    lang = request.args.get("lang", "sub")
    if 0 <= episode_index < len(episode_list):
        ep = episode_list[episode_index]
        links = extract_streaming_links(ep["url"], lang)
        if not links:
            flash("Could not extract streaming links. Try another episode.", "error")
            return redirect(url_for("home"))
        return render_template("watch.html", streaming_links=links, episode_title=ep["title"], language=lang)
    flash("Invalid episode selection!", "error")
    return redirect(url_for("home"))


@app.route("/api/extract/<int:episode_index>")
def api_extract(episode_index):
    lang = request.args.get("lang", "sub")
    if 0 <= episode_index < len(episode_list):
        ep = episode_list[episode_index]
        links = extract_streaming_links(ep["url"], lang)
        return jsonify({
            "success": bool(links),
            "links": links,
            "episode_title": ep["title"]
        })
    return jsonify({"success": False, "error": "Invalid episode index"}), 400


if __name__ == "__main__":
    # Use host and port from environment or defaults
    host = os.getenv("FLASK_RUN_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_RUN_PORT", "5000"))
    app.run(host=host, port=port, debug=True)
