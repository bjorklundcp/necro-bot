import json
import requests
import smtplib

from email.mime.text import MIMEText
from pymongo import MongoClient


USER_AGENT = "NecroBot/1.0 by necrophobia155"


def send_email_notification(email, link):
    with open('secrets.json', 'r') as file:
        secrets = json.load(file)
        my_email = secrets.get('test_email')
        my_pw = secrets.get('test_pw')

    message = "\r\n".join([
        "From: {}".format(test_email),
        "To: {}".format(email),
        "Subject: Necro Bot Notification!",
        "",
        "{}".format(link)
    ])

    smtObject = smtplib.SMTP('smtp.gmail.com')
    smtObject.ehlo()
    smtObject.starttls()
    smtObject.login(test_email, test_pw)
    smtObject.sendmail(test_email, test_email, message)
    smtObject.quit()


def get_access_token():
    with open('secrets.json', 'r') as file:
        secrets = json.load(file)

    client_auth = requests.auth.HTTPBasicAuth(secrets.get('api_id'), secrets.get('api_secret'))
    post_data = {"grant_type": "password", "username": secrets.get('user'), "password": secrets.get('password')}
    headers = {"User-Agent": USER_AGENT}
    response = requests.post("https://www.reddit.com/api/v1/access_token", auth=client_auth, data=post_data, headers=headers)
    return response.json().get('access_token')


def get_subreddit_json(endpoint, args=None):
    access_token = get_access_token()
    headers = {"Authorization": "bearer {}".format(access_token), "User-Agent": USER_AGENT}
    response = requests.get(endpoint, params=args, headers=headers)
    return response.json().get('data')


def get_subreddit_set(mongo_collection):
    results = mongo_collection.find({}, {"_id": False, "watch_entry": True})
    subreddits = set()

    for result in results:
        for entry in result.get('watch_entry'):
            subreddits.add(entry.get('subreddit'))

    return subreddits


def check_subreddits_for_key_words(mongo_collection):
    subreddits = get_subreddit_set(mongo_collection)
    for subreddit in subreddits:
        subreddit_json = get_subreddit_json("https://reddit.com/r/{}/new/.json".format(subreddit), {"limit": 100})
        subreddit_data = subreddit_json.get('children')
        related_watches_query = mongo_collection.find(
            {
                'watch_entry': {
                    '$elemMatch': {
                        'subreddit': subreddit
                    }
                }
            }
        )

        for related_watch in related_watches_query:
            for related_information in related_watch.get('watch_entry'):
                if related_information.get('subreddit') == subreddit:
                    related_key_words = related_information.get('key_words')
            for data in subreddit_data:
                post_title = data.get('data').get('title')
                with open('output.json', 'a') as file:
                    file.write('\n{}\n'.format(json.dumps(data.get('data'))))
                if any(keyword in post_title for keyword in related_key_words):
                    send_email_notification(associated_information.get('_id'), data.get('data').get('permalink'))


def main():
    mongo_client = MongoClient()
    mongo_collection = mongo_client.necro_bot.necro_bot_collection
    check_subreddits_for_key_words(mongo_collection)
    mongo_client.close()

