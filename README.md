# UWRedditBot
UWRedditBot is a bot made to provide relevant course information upon request on /r/uwaterloo subreddit.

## License
http://www.gnu.org/licenses/gpl.txt

## Setup
    pip install virtualenv
    virtualenv venv
    source venv/bin/activate
    pip install -r requirements.txt

## Creating the database
    sqlite3 DBNAME
    CREATE TABLE comments(comment_id varchar(255), UNIQUE(comment_id));

## Configuration
    mv local_settings.py.def uwredditbot/local_settings.py
Uncomment out the definitions and place your user information.

## Disclaimer
I am not liable for anything that happens to your reddit account if you choose to use this bot.

