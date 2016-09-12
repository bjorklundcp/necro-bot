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
    mongo_client = MongoClient()
    mongo_db = mongo_client.test
    mongo_collection = mongo_db.test_collection

    results = mongo_collection.find({}, {"_id": False, "subreddits": True})
    subreddits = set()

    for result in results:
        subreddit_list = result.get('subreddits')
        for subreddit in subreddit_list:
            subreddits.add(subreddit)

    return subreddits
    mongo_client.close()


def check_subreddits_for_key_words(mongo_collection):
    subreddits = get_subreddit_set(mongo_collection)
    for subreddit in subreddits:
        subreddit_json = get_subreddit_json("{}new/.json".format(subreddit), {"limit": 2})
        subreddit_data = subreddit_json.get('children')
        subreddit_query = mongo_collection.find({"subreddits":subreddit}, {"_id": False, "subreddits": False})
        for associated_information in subreddit_query:
            for data in subreddit_data:
                post_title = data.get('data').get('title')
                if any(chosen in post_title for chosen in associated_information.get('key_words')):
                    send_email_notification(associated_information.get('email'), data.get('data').get('permalink'))


def main():
    mongo_client = MongoClient()
    mongo_collection = mongo_client.test.test_collection
    check_subreddits_for_key_words(mongo_collection)
    mongo_client.close()

