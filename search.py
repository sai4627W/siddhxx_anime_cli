import requests
import os
import time
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import webbrowser
from colorama import init, Fore, Back, Style


# Initialize colorama for cross-platform colored terminal text
init(autoreset=True)


def print_banner():
    """Print an attractive banner"""
    banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║  {Fore.YELLOW}█████╗ ███╗   ██╗██╗███╗   ███╗███████╗    ███████╗████████╗██████╗ ███████╗ {Fore.CYAN}║
║  {Fore.YELLOW}██╔══██╗████╗  ██║██║████╗ ████║██╔════╝    ██╔════╝╚══██╔══╝██╔══██╗██╔════╝ {Fore.CYAN}║
║  {Fore.YELLOW}███████║██╔██╗ ██║██║██╔████╔██║█████╗      ███████╗   ██║   ██████╔╝█████╗   {Fore.CYAN}║
║  {Fore.YELLOW}██╔══██║██║╚██╗██║██║██║╚██╔╝██║██╔══╝      ╚════██║   ██║   ██╔══██╗██╔══╝   {Fore.CYAN}║
║  {Fore.YELLOW}██║  ██║██║ ╚████║██║██║ ╚═╝ ██║███████╗    ███████║   ██║   ██║  ██║███████╗ {Fore.CYAN}║
║  {Fore.YELLOW}╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚═╝     ╚═╝╚══════╝    ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝ {Fore.CYAN}║
║                                                                              ║
║            {Fore.MAGENTA}🌟 Siddhxx CLI - Your Ultimate Anime Streaming Experience 🌟{Fore.CYAN}           ║
║               {Fore.GREEN}✨ Watch Any Anime, Anytime, Anywhere ✨{Fore.CYAN}                ║
╚══════════════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
    """
    print(banner)


def loading_animation(text, duration=2):
    """Create a loading animation"""
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    end_time = time.time() + duration
    
    while time.time() < end_time:
        for frame in frames:
            print(f"\r{Fore.YELLOW}{frame} {text}{Style.RESET_ALL}", end="", flush=True)
            time.sleep(0.1)
    print(f"\r{Fore.GREEN}✓ {text} - Complete!{Style.RESET_ALL}")


def print_divider(char="═", length=80, color=Fore.CYAN):
    """Print a decorative divider"""
    print(f"{color}{char * length}{Style.RESET_ALL}")


def get_anime_input():
    """Get anime name input with style"""
    print(f"\n{Fore.MAGENTA}🔍 ANIME SEARCH{Style.RESET_ALL}")
    print_divider("─", 50, Fore.MAGENTA)
    
    while True:
        anime_name = input(f"{Fore.CYAN}🎌 Enter the anime name you want to search: {Fore.WHITE}").strip()
        if anime_name:
            return anime_name
        print(f"{Fore.RED}❌ Please enter a valid anime name!{Style.RESET_ALL}")


def display_search_results(anime_list):
    """Display search results in an attractive format"""
    print(f"\n{Fore.GREEN}🎯 SEARCH RESULTS FOUND!{Style.RESET_ALL}")
    print_divider("─", 60, Fore.GREEN)
    
    for idx, href in enumerate(anime_list, start=1):
        # Extract anime title from href
        title = href.split('/')[-1].replace('-', ' ').title()
        print(f"{Fore.YELLOW}[{idx:2d}] {Fore.WHITE}🎬 {title}{Style.RESET_ALL}")
    
    print_divider("─", 60, Fore.GREEN)


def get_user_choice(options_list, prompt_text):
    """Get user choice with error handling"""
    while True:
        try:
            choice = int(input(f"{Fore.CYAN}👉 {prompt_text}: {Fore.WHITE}"))
            if 1 <= choice <= len(options_list):
                return choice
            else:
                print(f"{Fore.RED}❌ Invalid choice! Please enter a number between 1 and {len(options_list)}{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}❌ Invalid input! Please enter a number{Style.RESET_ALL}")


def display_episodes(anime_list2):
    """Display episodes in an attractive format"""
    print(f"\n{Fore.BLUE}📺 AVAILABLE EPISODES{Style.RESET_ALL}")
    print_divider("─", 60, Fore.BLUE)
    
    for idx, href in enumerate(anime_list2, start=1):
        episode_name = href.split('/')[-1].replace('-', ' ').title()
        print(f"{Fore.YELLOW}[{idx:2d}] {Fore.WHITE}🎥 {episode_name}{Style.RESET_ALL}")
    
    print_divider("─", 60, Fore.BLUE)


def get_language_choice():
    """Get language preference with style"""
    print(f"\n{Fore.MAGENTA}🌐 LANGUAGE SELECTION{Style.RESET_ALL}")
    print_divider("─", 40, Fore.MAGENTA)
    print(f"{Fore.YELLOW}[1] {Fore.WHITE}🇯🇵 Subbed (Japanese with subtitles)")
    print(f"{Fore.YELLOW}[2] {Fore.WHITE}🇺🇸 Dubbed (English voice-over)")
    print_divider("─", 40, Fore.MAGENTA)
    
    while True:
        try:
            lang = int(input(f"{Fore.CYAN}👉 Choose your preference: {Fore.WHITE}"))
            if lang in [1, 2]:
                return lang
            else:
                print(f"{Fore.RED}❌ Please enter 1 for Subbed or 2 for Dubbed{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}❌ Invalid input! Please enter 1 or 2{Style.RESET_ALL}")


def extract_with_progress():
    """Show extraction progress"""
    print(f"\n{Fore.YELLOW}🔧 EXTRACTING STREAMING LINK{Style.RESET_ALL}")
    print_divider("─", 50, Fore.YELLOW)
    
    steps = [
        "Initializing Chrome driver",
        "Loading episode page", 
        "Parsing video sources",
        "Extracting embed links",
        "Finalizing extraction"
    ]
    
    for step in steps:
        loading_animation(step, 1)
        time.sleep(0.3)


def success_message(embed_link):
    """Display success message"""
    print(f"\n{Fore.GREEN}🎉 SUCCESS! STREAMING LINK EXTRACTED{Style.RESET_ALL}")
    print_divider("═", 70, Fore.GREEN)
    print(f"{Fore.CYAN}📺 Stream URL: {Fore.WHITE}{embed_link}")
    print_divider("═", 70, Fore.GREEN)
    print(f"{Fore.YELLOW}🚀 Opening in your default browser...{Style.RESET_ALL}")
    
    # Countdown animation
    for i in range(3, 0, -1):
        print(f"\r{Fore.YELLOW}⏱️  Starting in {i}...{Style.RESET_ALL}", end="", flush=True)
        time.sleep(1)
    print(f"\r{Fore.GREEN}🎬 Enjoy your anime! ✨{Style.RESET_ALL}")


def error_message(message):
    """Display error message"""
    print(f"\n{Fore.RED}💥 ERROR OCCURRED{Style.RESET_ALL}")
    print_divider("─", 40, Fore.RED)
    print(f"{Fore.RED}❌ {message}{Style.RESET_ALL}")
    print_divider("─", 40, Fore.RED)


# ═══════════════════════════════════════════════════════════════════════════════
#                              MAIN PROGRAM
# ═══════════════════════════════════════════════════════════════════════════════


try:
    # Clear screen and show banner
    os.system('cls' if os.name == 'nt' else 'clear')
    print_banner()

    # Step 0: Get anime name input
    anime_name = get_anime_input()
    search_query = anime_name.replace(" ", "+")

    # Step 1: Fetch search results
    loading_animation("Searching for anime", 2)
    web = requests.get(f"https://www.animegg.org/search/?q={search_query}")
    soup = BeautifulSoup(web.content, "html.parser")

    # Step 2: Extract anime links
    anime_links = soup.find_all("a", class_="mse")
    anime_list = [a.get("href") for a in anime_links]

    if not anime_list:
        error_message("No anime found with that name. Please try a different search term.")
        sys.exit()

    # Step 3: Display and get anime choice
    display_search_results(anime_list)
    choice = get_user_choice(anime_list, "Enter the number of the anime you want to watch")

    selected_href = anime_list[choice - 1]
    str1 = "https://www.animegg.org" + selected_href

    print(f"\n{Fore.GREEN}✅ Selected: {Fore.WHITE}{selected_href.split('/')[-1].replace('-', ' ').title()}{Style.RESET_ALL}")

    # Step 4: Fetch episode list
    loading_animation("Loading episodes", 2)
    web2 = requests.get(str1)
    soup2 = BeautifulSoup(web2.content, "html.parser")

    anime_links1 = soup2.find_all("a", class_="anm_det_pop")
    anime_list2 = [a.get("href") for a in anime_links1]

    if not anime_list2:
        error_message("No episodes found for this anime.")
        sys.exit()

    # Step 5: Display and get episode choice
    display_episodes(anime_list2)
    choice2 = get_user_choice(anime_list2, "Enter the episode number you want to watch")

    selected_episode = anime_list2[choice2 - 1]
    episode_url = "https://www.animegg.org" + selected_episode

    # Step 6: Get language preference
    lang = get_language_choice()

    # Step 7: Build final URL
    final_episode_str = episode_url + ("#subbed" if lang == 1 else "#dubbed")
    lang_text = "🇯🇵 Subbed" if lang == 1 else "🇺🇸 Dubbed"

    print(f"\n{Fore.GREEN}✅ Final selection: {Fore.WHITE}{lang_text}{Style.RESET_ALL}")

    # Step 8: Extract streaming link
    extract_with_progress()

    # Selenium setup
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-notifications")
    options.add_argument("--mute-audio")
    options.add_argument("--log-level=3")
    service = Service(log_path=os.devnull)

    driver = webdriver.Chrome(service=service, options=options)
    driver.get(final_episode_str)

    iframe_elements = driver.find_elements("tag name", "iframe")
    embed_links = [iframe.get_attribute("src") for iframe in iframe_elements if iframe.get_attribute("src")]

    driver.quit()

    if len(embed_links) < 2:
        error_message("Could not find streaming links for this episode. Please try a different episode.")
        sys.exit()

    # Remove the last link as per requirement
    stream_links = embed_links[:-1]

    # Show all stream links for user to choose
    print(f"\n{Fore.MAGENTA}🌐 Available streaming links:{Style.RESET_ALL}")
    for i, link in enumerate(stream_links, start=1):
        print(f"{Fore.YELLOW}[{i}] {Fore.WHITE}{link}{Style.RESET_ALL}")

    # User choice of streaming link
    choice_link = get_user_choice(stream_links, "Enter the number of the streaming link you want to watch")

    selected_link = stream_links[choice_link - 1]

    success_message(selected_link)
    webbrowser.open(selected_link)

    print(f"\n{Fore.CYAN}🎊 Thank you for using Siddhxx CLI! Have a great watch! 🍿{Style.RESET_ALL}")

except KeyboardInterrupt:
    print(f"\n{Fore.YELLOW}👋 Program interrupted by user. Goodbye!{Style.RESET_ALL}")
except Exception as e:
    error_message(f"An unexpected error occurred: {str(e)}")
