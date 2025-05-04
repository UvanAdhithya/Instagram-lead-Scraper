# InstagramLeadScraper

An automated Instagram lead scraper that logs in, searches for posts under specified hashtags, extracts influencer profiles, and calculates engagement rates — helping you discover high-potential leads for your business.

---

## 🚀 Features

- Logins to Instagram using credentials 
- Searches and scrapes posts from any hashtag
- Extracts unique influencer profiles
- Visits each profile and scrapes recent post data
- Calculates engagement rate based on likes and comments
- Exports leads to CSV with profile and performance metrics

---

## Input Parameters

- Keyword/Hashtag
- Follower count range
- serach by country
- Number of posts to scrape per hashtag
- Number of posts to scrape per profile

---

## Output
A CSV file with:
- Username
- Bio
- Followers count
- Country
- Engagement rate (%)
- Contact information

## 📦 Tech Stack

- Python
- Selenium
- BeautifulSoup
- Pandas
- NumPy

---

## ⚙️ How to Use

1. **Clone the repo**
   ```bash
   git clone https://github.com/yourusername/Instagram-lead-Scraper.git
   cd Instagram-lead-Scraper
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
3. **Run program**
   ```bash
   python igScraper.py
4. **Create Executable**(optional)
   - Run these cmds from the directory containing igSraper.py
   ```bash
   pip install pyinstaller
   pyinstaller --onefile --add-data "login_details.pkl:." your_script.py
