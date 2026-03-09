# utils/reddit_scraper.py

import praw
import re
import os
from datetime import datetime, timedelta


class RedditScraper:
    def __init__(self, subreddits=None, days_back=1):
        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        user_agent = os.getenv("REDDIT_USER_AGENT")
        
        # Check if credentials are provided
        if not client_id or not client_secret or not user_agent:
            raise ValueError(
                "Reddit API credentials not found. Please set REDDIT_CLIENT_ID, "
                "REDDIT_CLIENT_SECRET, and REDDIT_USER_AGENT in your .env file. "
                "Reddit scraping is optional - the daily summary will work without it."
            )
        
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        self.subreddits = subreddits or ['Shortsqueeze', 'SqueezePlays']
        self.days_back = days_back
        self.exclusion_list = {"CEO", "USD", "AI", "ETF", "YOLO"}  # extend this as needed

    def fetch_posts(self, subreddit_name):
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            start_time = datetime.utcnow() - timedelta(days=self.days_back)

            posts = []
            for submission in subreddit.new(limit=500):
                post_time = datetime.utcfromtimestamp(submission.created_utc)
                if post_time >= start_time and submission.score > 5:
                    posts.append(submission.title + " " + submission.selftext)
            return posts
        except Exception as e:
            raise Exception(f"Failed to fetch Reddit posts from {subreddit_name}: {str(e)}. Check your Reddit API credentials.")

    def extract_tickers(self, text):
        pattern = r'\b[A-Z]{3,5}\b|\$[A-Z]{1,5}'
        matches = re.findall(pattern, text)
        tickers = set()
        for match in matches:
            ticker = match[1:] if match.startswith('$') else match
            ticker = ticker.upper()
            if ticker not in self.exclusion_list:
                tickers.add(ticker)
        return tickers

    def scrape(self):
        all_tickers = set()
        for subreddit in self.subreddits:
            posts = self.fetch_posts(subreddit)
            for post in posts:
                all_tickers.update(self.extract_tickers(post))
        return list(all_tickers)
