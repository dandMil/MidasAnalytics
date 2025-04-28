import praw
import re
from datetime import datetime, timedelta
import os
reddit_client_id = os.getenv("REDDIT_CLIENT_ID", "default_secret_key")  # Required for session management
reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET", "default_secret_key")  # Required for session management
user_agent = os.getenv("REDDIT_USER_AGENT", "default_secret_key")  # Required for session management

reddit = praw.Reddit(
    client_id=reddit_client_id,
    client_secret=reddit_client_secret,
    user_agent=user_agent
)

subreddits = ['Shortsqueeze', 'SqueezePlays']


# Define a function to retrieve posts within the last X days for a subreddit
def fetch_posts(subreddit_name, days):
    subreddit = reddit.subreddit(subreddit_name)
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)

    posts = []
    for submission in subreddit.new(limit=1000):  # Fetch up to 1000 recent posts
        post_time = datetime.utcfromtimestamp(submission.created_utc)
        if start_time <= post_time <= end_time:
            posts.append(submission.title + " " + submission.selftext)
    return posts


# Define a function to extract words matching criteria
def extract_words(posts):
    pattern = r'\b[A-Z]{3,4}\b|\$[A-Z]{1,10}'  # 3-4 letters in ALL CAPS or prefixed with $
    extracted_words = []
    for post in posts:
        matches = re.findall(pattern, post)
        extracted_words.extend(matches)
    return extracted_words


def scrape_reddit(days_back):
    subreddits = ['Shortsqueeze', 'SqueezePlays']
    days = 1  # Change this to specify the number of days
    all_words = {}

    for subreddit_name in subreddits:
        print(f"Fetching posts from subreddit '{subreddit_name}' for the past {days} days...")
        posts = fetch_posts(subreddit_name, days)

        print(f"Extracting matching words from '{subreddit_name}'...")
        words = extract_words(posts)

        # Store results for each subreddit
        all_words[subreddit_name] = words

    # Print results
    print("\nMatching Words by Subreddit:")
    word_set = set()
    for subreddit, words in all_words.items():
        print(f"\nSubreddit: {subreddit}")
        if words:
            for word in words:
                # Check if the word starts with `$` and remove it if present
                processed_word = word[1:] if word.startswith('$') else word
                # Convert the word to uppercase and add it to the set
                word_set.add(processed_word.upper())
        else:
            print("No matching words found.")
    return word_set
