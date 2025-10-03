
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import os
import threading
import time

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-this'

# Global variables to store data
search_results = []
episode_list = []
current_anime_url = ""

def setup_selenium():
    """Setup Selenium with headless Chrome"""
    try:
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.add_argument("--mute-audio")
        options.add_argument("--log-level=3")
        options.add_argument("--disable-dev-shm-usage")
        
        service = Service(log_path=os.devnull)
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        print(f"Selenium setup error: {e}")
        return None

def search_anime(anime_name):
    """Search for anime on animegg.org"""
    try:
        search_query = anime_name.replace(" ", "+")
        web = requests.get(f"https://www.animegg.org/search/?q={search_query}")
        soup = BeautifulSoup(web.content, "html.parser")
        
        anime_links = soup.find_all("a", class_="mse")
        anime_list = []
        
        for link in anime_links:
            href = link.get("href")
            if href:
                title = href.split('/')[-1].replace('-', ' ').title()
                anime_list.append({
                    'href': href,
                    'title': title,
                    'url': f"https://www.animegg.org{href}"
                })
        
        return anime_list
    except Exception as e:
        print(f"Search error: {e}")
        return []

def get_episodes(anime_url):
    """Get episodes for selected anime"""
    try:
        web2 = requests.get(anime_url)
        soup2 = BeautifulSoup(web2.content, "html.parser")
        
        anime_links1 = soup2.find_all("a", class_="anm_det_pop")
        episode_list = []
        
        for link in anime_links1:
            href = link.get("href")
            if href:
                episode_name = href.split('/')[-1].replace('-', ' ').title()
                episode_list.append({
                    'href': href,
                    'title': episode_name,
                    'url': f"https://www.animegg.org{href}"
                })
        
        return episode_list
    except Exception as e:
        print(f"Episodes error: {e}")
        return []

def extract_streaming_links(episode_url, language):
    """Extract streaming links using Selenium"""
    try:
        final_url = episode_url + ("#subbed" if language == "sub" else "#dubbed")
        
        driver = setup_selenium()
        if not driver:
            return []
        
        driver.get(final_url)
        time.sleep(3)  # Wait for page to load
        
        iframe_elements = driver.find_elements("tag name", "iframe")
        embed_links = []
        
        for iframe in iframe_elements:
            src = iframe.get_attribute("src")
            if src:
                embed_links.append(src)
        
        driver.quit()
        
        # Remove last link as per original logic
        if len(embed_links) > 1:
            embed_links = embed_links[:-1]
        
        return embed_links
    except Exception as e:
        print(f"Extraction error: {e}")
        return []

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    global search_results
    anime_name = request.form.get('anime_name', '').strip()
    
    if not anime_name:
        flash('Please enter an anime name!', 'error')
        return redirect(url_for('home'))
    
    search_results = search_anime(anime_name)
    
    if not search_results:
        flash('No anime found with that name. Please try a different search term.', 'error')
        return redirect(url_for('home'))
    
    return render_template('search_results.html', results=search_results, anime_name=anime_name)

@app.route('/episodes/<int:anime_index>')
def episodes(anime_index):
    global episode_list, current_anime_url
    
    if 0 <= anime_index < len(search_results):
        selected_anime = search_results[anime_index]
        current_anime_url = selected_anime['url']
        episode_list = get_episodes(current_anime_url)
        
        if not episode_list:
            flash('No episodes found for this anime.', 'error')
            return redirect(url_for('home'))
        
        return render_template('episodes.html', 
                             episodes=episode_list, 
                             anime_title=selected_anime['title'])
    else:
        flash('Invalid anime selection!', 'error')
        return redirect(url_for('home'))

@app.route('/watch/<int:episode_index>')
def watch(episode_index):
    language = request.args.get('lang', 'sub')
    
    if 0 <= episode_index < len(episode_list):
        selected_episode = episode_list[episode_index]
        episode_url = selected_episode['url']
        
        # Extract streaming links in background
        streaming_links = extract_streaming_links(episode_url, language)
        
        if not streaming_links:
            flash('Could not find streaming links for this episode. Please try a different episode.', 'error')
            return redirect(url_for('home'))
        
        return render_template('watch.html', 
                             streaming_links=streaming_links,
                             episode_title=selected_episode['title'],
                             language=language)
    else:
        flash('Invalid episode selection!', 'error')
        return redirect(url_for('home'))

@app.route('/api/extract/<int:episode_index>')
def api_extract(episode_index):
    """API endpoint for extracting links asynchronously"""
    language = request.args.get('lang', 'sub')
    
    if 0 <= episode_index < len(episode_list):
        selected_episode = episode_list[episode_index]
        episode_url = selected_episode['url']
        
        streaming_links = extract_streaming_links(episode_url, language)
        
        return jsonify({
            'success': len(streaming_links) > 0,
            'links': streaming_links,
            'episode_title': selected_episode['title']
        })
    
    return jsonify({'success': False, 'error': 'Invalid episode selection'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
