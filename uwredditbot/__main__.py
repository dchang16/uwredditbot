import local_settings
import logging
import praw
import re
import sqlite3
import time

from uwaterlooapi import UWaterlooAPI
from datetime import datetime as dt

# Initialize Constants
HELP = "HELP"
TERM = "TERM"
HOLIDAYS = "HOLIDAYS"
SCHEDULE = ["-S", "-s"]
LOGIN = local_settings.PARAM_LOGIN
PASSWORD = local_settings.PARAM_PASSWORD
KEY = local_settings.PARAM_KEY
USER_AGENT = local_settings.PARAM_USER_AGENT
DATABASE = local_settings.PARAM_DATABASE

# Initialize DB
conn = sqlite3.connect(DATABASE)
conn.isolation_level = None
cursor = conn.cursor()

# Initialize Logging
logging.basicConfig(format="%(asctime)s %(message)s", level=logging.DEBUG)
logging.debug("Connecting to %", DATABASE)

if __name__ == "__main__":
    # Set UW API
    uw = UWaterlooAPI(api_key=KEY)
    uw_subjects = []
    avail_codes = [TERM, HOLIDAYS, SCHEDULE, HELP]
    term_dates = {}
    term_dates[1159] = {"start_date": "2015-09-14", "end_date": "2015-12-22"}
    term_dates[1161] = {"start_date": "2016-01-04", "end_date": "2016-04-23"}
    term_dates[1165] = {"start_date": "2016-05-02", "end_date": "2016-08-13"}


    for course in uw.subject_codes():
        uw_subjects.append(course.get("subject"))

    reddit = praw.Reddit(user_agent=USER_AGENT)
    reddit.login(LOGIN, PASSWORD)

    # Main loop
    while True:
        logging.debug("Loop")
        subreddit = reddit.get_subreddit("bottesting")
        subreddit_comments = subreddit.get_comments()
        current_term = uw.terms().get("current_term")
        term_dates.get(current_term)
        start_date = term_dates.get(current_term).get("start_date")
        end_date = term_dates.get(current_term).get("end_date")

        # Scrape subreddit comments
        for comment in subreddit_comments:
            logging.debug(comment)
            logging.debug(comment.id)
            cursor.execute("SELECT comment_id FROM comments")
            already_done = [r[0] for r in cursor]
            # Check comments that have not already been replied to
            if comment.id not in already_done:
                reply = ""
                # Find all comments with [[]]
                result = re.findall(r'\[\[(.+?)\]\]', comment.body)
                for code in result:
                    code_list = code.split()
                    logging.debug(code_list)
                    # Check if comment is a valid course
                    if code_list[0].upper() in uw_subjects:
                        try:
                            course = uw.course(code_list[0].upper(), code_list[1])
                            if course:
                                online = "Yes" if course.get("offerings").get("online") else "No"
                                reply += \
                                "[{} {} {} {} | {} | Course ID: {}](https://uwflow.com/course/{}{})\
                                \n\n{}\
                                \n\n*Prerequisites: {}*\n\n*Antirequisites: {}*\
                                \n\n*Available Online: {}*\n\n"\
                                .format(course.get("subject"),\
                                course.get("catalog_number"),\
                                ','.join(course.get("instructions")),\
                                course.get("units"),\
                                course.get("title"),\
                                course.get("course_id"),\
                                course.get("subject").lower(),\
                                course.get("catalog_number"),\
                                course.get("description"),\
                                course.get("prerequisites"),\
                                course.get("antirequisites"),\
                                online)
                                reply += \
                                "\n\n-----------------------------------------------\
                                \n\n"
                            # Check for SCHEDULE flag
                            if len(code_list) == 3 and code_list[2] in SCHEDULE:
                                course_schedule = uw.term_course_schedule(\
                                current_term, code_list[0].upper(), code_list[1])

                                if not course_schedule:
                                    reply += "This course is not offered this term"

                                else:
                                    for lec in course_schedule:
                                        for classes in lec.get("classes"):
                                            if classes.get("instructors") \
                                            and classes.get("date").get("weekdays"):
                                                reply += "*{} | {} {}-{} | {} | {} {}*\n\n"\
                                                .format(\
                                                lec.get("section"),\
                                                classes.get("date").get("weekdays"),\
                                                classes.get("date").get("start_time"),\
                                                classes.get("date").get("end_time"),\
                                                ', '.join(classes.get("instructors")),\
                                                classes.get("location").get("building"),\
                                                classes.get("location").get("room"))
                                reply += \
                                        "\n\n-----------------------------------------------\
                                        \n\n"
                        except Exception as e:
                            logging.error(e)
                            pass
                    # Check if comment has a valid code
                    if len(code_list) == 1 and code_list[0].upper() in avail_codes:
                        if code_list[0].upper() == TERM:
                            reply += \
                            "**Current Term: {}**\
                            \n\nStart Date: {}\
                            \n\nEnd Date: {}\
                            \n\n-----------------------------------------------\
                            \n\n"\
                            .format(current_term,\
                            dt.strptime(start_date, "%Y-%m-%d").date().strftime("%d %b, %Y"),\
                            dt.strptime(end_date, "%Y-%m-%d").date().strftime("%d %b, %Y"))
                        if code_list[0].upper() == HOLIDAYS:
                            reply += \
                            "**Holidays this term:** \n\n"
                            for holiday in uw.holidays():
                                date = dt.strptime(holiday.get("date"), "%Y-%m-%d").date()
                                if date >= dt.strptime(start_date, "%Y-%m-%d").date() \
                                    and date <= dt.strptime(end_date, "%Y-%m-%d").date():
                                    reply += \
                                    "*{}* on {}\
                                    \n\n-----------------------------------------------\
                                    \n\n"\
                                    .format(holiday.get("name"), date.strftime("%d %b, %Y"))
                        if code_list[0].upper() == HELP:
                            reply += \
                            "Hi, I am a bot. The following commands are what I support:\
                            \n\nUsage: *[[{Keyword}]]*\
                            \n\n**{Subject} {Course Number} |** Shows information about the course.\
                            \n\n*[option] -S* | Shows available classes for the current term.\
                            \n\n **HOLIDAYS |** Shows holidays for the current term.\
                            \n\n **TERM |** Shows information about the current school term.\
                            \n\n\
                            \n\nSend me a direct message if you have any questions or comments.\
                            \n\n*-UWRedditBot*\
                            \n\n-----------------------------------------------\
                            \n\n"
                # Update the already done set
                cursor.execute("INSERT INTO comments VALUES('{}')".format(comment.id))
                # Reply to comment with relevant information
                if reply:
                    try:
                        comment.reply(reply)
                    except Exception as e:
                        logging.error(e)
                        pass
        time.sleep(120)
