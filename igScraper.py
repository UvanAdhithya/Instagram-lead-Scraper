from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException
import pandas as pd
import os
import pickle
import re
import chromedriver_autoinstaller


def get_html(driver):
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    with open("instagram_source.html","w",encoding='utf-8') as f:
        f.write(soup.prettify())
    
    print("Page source saved as 'instagram_source.html'.")

def remove_emojis(text):
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002700-\U000027BF"  # dingbats
        "\U000024C2-\U0001F251"  # enclosed characters
        "]+", flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)

def parse_count(count_str):
    """Remove commas and convert to int."""
    count_str = count_str.replace(',', '').strip()
    if count_str == "":
        return 0  # or raise an error if you'd rather handle it upstream
    return int(count_str)

def parse_shorthand(text):
    if 'k' in text.lower():
        return int(float(text.lower().replace('k', '')) * 1000)
    elif 'm' in text.lower():
        return int(float(text.lower().replace('m', '')) * 1_000_000)
    else:
        return int(text.replace(',', ''))

def get_like_comment_of_post(driver):
    try:
        # Wait for the like or view element to show
        like_elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//section//span[contains(text(),'likes')]/..")
            )
        )
        
        like_text = like_elem.text.split(' ')[0].replace(',', '')
        likes = parse_shorthand(like_text)
    except:
        likes = 0

    try:
        # Count all comment containers (excluding caption)
        comment_elems = driver.find_elements(By.XPATH, "//ul/ul")
        comments = len(comment_elems)
    except:
        comments = 0

    return likes, comments

def get_engagement_ratio(driver, posts_number, username, followers):
    xpath = f"//a[starts-with(@href, '/{username}/p/') or starts-with(@href, '/{username}/reel/')]"
    post_results = WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
    #click on post
    post_href = [post.get_attribute("href") for post in post_results]
    total_likes, total_comments = 0,0
    for index,post in enumerate(post_href[:posts_number]):
        driver.get(post)
        if index == 0:
            time_posted_elem = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//time[contains(@class, 'x1p4m5qa')]")))
            time_posted = time_posted_elem.text
        likes, comments = get_like_comment_of_post(driver)
        total_likes += likes
        total_comments += comments
    engagement_ratio = (total_likes + total_comments) / followers

    return round(engagement_ratio * 100, 2), time_posted
    

def parse_page(driver, href_op, posts_in_profile):
    driver.get(href_op)
    # if country not india or follower < 10k return -1, save time by not parsing name, posts and likes
    try:
        username_elem = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//h2//span[contains(@class, 'x193iq5w')]"))
        )

        # Click using JavaScript in case it's not directly interactable
        driver.execute_script("arguments[0].click();", username_elem)

        country_elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//span[text()='Account based in']/following-sibling::span"))
        )
        country = country_elem.text
    except TimeoutException:
        print("❌ Username or modal not found — maybe not available on this account.")

    follower_elem = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//ul/li[2]//span[contains(@class, 'x5n08af x1s688f')]")))
    follower_text = follower_elem.get_attribute("title")

    follower_count = parse_count(follower_text)

    if (follower_count < min_followers or follower_count > max_followers)  or "india" not in country.lower():
        return
    
    try:
        bio_elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@role='button']/span[contains(@class, '_ap3a')]"))
        )
        bio = bio_elem.text
        clean_bio = remove_emojis(bio)
    except TimeoutException:
        clean_bio = ""
    
    username = username_elem.text
    if username not in seen_usernames:
        seen_usernames.add(username)

        engagement_percentage, last_posted = get_engagement_ratio(driver,posts_in_profile,username, follower_count)
        
        influencers.append({
            "Username": username,
            "Followers": follower_count,
            "Engagement_rate": engagement_percentage,
            "Bio": clean_bio,
            "Last Posted": last_posted
        })

        save_to_excel(influencers,filename)

        print("Name: ", username)
        print("Followers: ", follower_count)
        print("Country: ", country)
        print("Engagement Ratio: ", engagement_percentage)
        print()


def initialize_driver(website):
    chromedriver_autoinstaller.install()  # Automatically installs matching ChromeDriver

    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options = options)
    driver.get(website)
    
    return driver

def login_instagram(driver, name, password):
    # target username
    username_input = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='username']")))
    password_input = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='password']")))

    # enter username and password
    username_input.clear()
    username_input.send_keys(name)
    password_input.clear()
    password_input.send_keys(password)

    # target the login button and click it
    button = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))).click()
    

    return username_input,password_input

def search_keyword(driver, keyword):
    search = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Search']")))

    search.send_keys(keyword)

    # Wait for dropdown links after search
    search_results = WebDriverWait(driver, 30).until(
        EC.presence_of_all_elements_located((By.XPATH, f"//a[contains(@href, '/explore/tags/')]"))
    )
    hrefs = [link.get_attribute("href") for link in search_results] 

    return hrefs
    
def save_to_excel(data_list,filename):
    try:
        new_df = pd.DataFrame(data_list)

        # Append mode, add header only if file doesn't exist
        new_df.to_csv(filename, mode='a', header=not os.path.exists(filename), index=False, encoding = 'utf-8')
        print(f"✅ Data successfully saved to {filename}")
    except Exception as e:
        print(f"❌ Error saving to {filename}: {e}")

def get_user_input():

    # Load the dictionary from the file (if it exists)
    try:
        with open("login_details.pkl", "rb") as f:
            login_details = pickle.load(f)
    except FileNotFoundError:
        # If the file doesn't exist, start with an empty dictionary and create file
        login_details = {}
        with open("login_details.pkl", "wb") as f:
            pickle.dump(login_details, f)
        print("New file created for login details.")


    print("=== Instagram Scraper Menu ===")

    while True:
        keyword = input("Enter the hashtag keyword (include #): ").strip()
        
        if keyword and keyword.startswith("#"):
            break  # Valid input, exit loop
        else:
            print("❌ Please enter a valid hashtag (e.g., #example).")

    while True:
        try:
            posts_per_hashtag = int(input("Number of posts to scrape per hashtag: "))
            break
        except ValueError:
            print("❌ Please enter a valid number for posts per hashtag.")

    while True:
        try:
            posts_in_profile = int(input("Number of posts to scrape from profile for engagement rate: "))
            break
        except ValueError:
            print("❌ Please enter a valid number for profile posts.")

    while True:
        try:
            last_active = int(input("Last post(days): "))
            break
        except ValueError:
            print("❌ Please enter a valid number for profile posts.")

    while True:
        try:
            min_followers = int(input("Minimum follower count: "))
            max_followers = int(input("Maximum follower count: "))
            break
        except ValueError:
            print("❌ Please enter a valid number for minimum follower count.")
    
    while True:
        try:
            filename = input("Name of file to be stored: ")
            filename += ".csv"
            break
        except ValueError:
            print("❌ Please enter a valid nae for filename. (e.g., example)")

    # Skip option selection if dictionary is empty
    if not login_details:
        # Directly go to option 2
        username = input("Enter username: ")
        password = input("Enter password: ")
        login_details[username] = password
        
        # Save the updated login_details to the file
        with open("login_details.pkl", "wb") as f:
            pickle.dump(login_details, f)
        print("New login details saved.")
    else:

        print("\n🔑 Choose an option:")
        print("1. View Saved Login Details")
        print("2. Enter New Login Details")

        choice = int(input("\nPlease enter your choice (1 or 2): "))

        if choice == 1:
            print("Login Details:\n" + "-"*30)
            for i, (key, value) in enumerate(login_details.items(), start=1):
                print(f"{i}. Username: {key:<15}    Password: {value}")
            print("-" * 30)

            # Get the user's option, ensuring it's valid
            while True:
                try:
                    option = int(input(f"\nEnter option (1 to {len(login_details)}): "))
                    
                    # Validate option input
                    if 1 <= option <= len(login_details):
                        username = list(login_details)[option-1]
                        password = login_details[username]
                        break
                    else:
                        print("❌ Number Out Of Range, please choose a valid number.")
                except ValueError:
                    print("❌ Invalid input. Please enter a valid number.")

        elif choice == 2:
            username = input("Enter username: ")
            password = input("Enter password: ")
            login_details[username] = password
        else:
            print("❌ Invalid choice! Try again")
    return username, password, keyword, posts_per_hashtag, posts_in_profile, last_active, min_followers, max_followers, filename

def remove_duplicates(filename):
    # Load the data
    df = pd.read_csv(filename)

    # Drop duplicate usernames (keep first occurrence)
    df = df.drop_duplicates(subset="Username", keep="first")

    # Save cleaned data back to the same file
    df.to_csv(filename, index=False)

    print("✅ Duplicates removed successfully.")

def switch_to_headless(driver, website):
    # Save session cookies and current URL
    cookies = driver.get_cookies()
    current_url = driver.current_url

    # Close the normal driver
    driver.quit()

    # Headless Chrome setup
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')

    headless_driver = webdriver.Chrome(options=options)
    headless_driver.get(website)

    # Add cookies to headless session
    for cookie in cookies:
        cookie.pop('sameSite', None)  # Remove unsupported field
        headless_driver.add_cookie(cookie)

    # Resume at the original page
    headless_driver.get(current_url)
    
    return headless_driver

# ====CONFIGURATION====
website = "https://www.instagram.com"
driver = initialize_driver(website)

# Get all inputs (including credentials)
username, password, keyword, posts_per_hashtag, posts_in_profile, last_active, min_followers,max_followers, filename = get_user_input()

influencers = []
seen_usernames = set()


# Perform login
login_instagram(driver,username, password)

get_html(driver)

# VISIT each link directly
hrefs = search_keyword(driver, keyword)

# Before switching to headless
#input("🔍 After clicking on search icon and results load, press ENTER to continue...")

#Switch
driver = switch_to_headless(driver, website)


for link in hrefs: # Each link is a hashtag
    driver.get(link)
    print("Now visiting: ", link)

    #time.sleep(3) # wait to load be4 scraping
    #scrapefunction
    try:
        post_results = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "_aagu")))
    except TimeoutException:
        print("⚠️ Post content not found. Skipping hashtag....")
        continue
        
    post_links = set() # To prevent duplicate links
    scroll_attempts = 0

    # Keep scrolling untill n or scroll_attempt limit is met
    while len(post_links) < posts_per_hashtag and scroll_attempts < 20:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # give time for posts to load

            posts = driver.find_elements(By.XPATH, "//a[contains(@href, '/p/')]") # finding all posts in a scroll page
            for p in posts[:posts_per_hashtag]:         # Gets href of n posts
                href_post = p.get_attribute("href")
                if href_post:
                    post_links.add(href_post)

            scroll_attempts += 1
    
    print(f"✅ Final {posts_per_hashtag} links from {link}:")

    Influencer_links = set()
    for link in post_links:
        print(f"🔗 Visiting post: {link}")
        driver.get(link)
        time.sleep(2)
        try:
            #  Accessing Profile page of OP
            op_page = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/') and not(contains(@href, '/p/'))]")))
            href_op = op_page.get_attribute('href')
            if href_op:
                Influencer_links.add(href_op)
                parse_page(driver,href_op, posts_in_profile)
        except TimeoutException:
            print("TimeOut❌")
remove_duplicates(filename)


driver.quit()