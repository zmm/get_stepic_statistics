#!/usr/bin/python3.7

import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import argparse
import sys

client_id = ""
client_secret = ""

API_HOST = 'https://stepik.org'
ID = "--id"
ID_DEST = "course_ID"
HELP = "Enter course's ID"
KEY = "--key"
KEY_DEST = "key"
GOOGLE_SHEET = "--sheet"
GOOGLE_SHEET_DEST = "sheet"
GOOGLE_LIST = "--list"
GOOGLE_LIST_DEST = "sheet_list"
GOOGLE_SHEET_HELP = "Enter resulting google sheet url"
FILENAME = "statistics"
CSV = ".csv"
SEP = ";"
DATE_SEP = "/"


def google_sheets_process(sheet_url, result, list):
    scope = ['https://spreadsheets.google.com/feeds']
    creds = ServiceAccountCredentials.from_json_keyfile_name('google_api_key.json', scope)
    client = gspread.authorize(creds)

    sheet = client.open_by_key(sheet_url).worksheet(list)
    index = 1
    for row in result:
        sheet.insert_row(row.replace("\n", "").split(";"), index)
        index += 1


def authorization():
    print("Trying to authorize...")
    auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
    response = requests.post('https://stepik.org/oauth2/token/',
                             data={'grant_type': 'client_credentials'},
                             auth=auth)
    token_t = response.json().get('access_token', None)
    if not token_t:
        print('Unable to authorize with provided credentials')
        exit(1)
    return token_t


def get_id():
    parser = argparse.ArgumentParser()
    parser.add_argument(ID, type=str, required=True,
                        dest=ID_DEST,
                        help=HELP)
    parser.add_argument(GOOGLE_SHEET, type=str, required=True,
                        dest=GOOGLE_SHEET_DEST,
                        help=GOOGLE_SHEET_HELP)
    parser.add_argument(KEY, type=str, required=False,
                        dest=KEY_DEST,
                        help=HELP)
    parser.add_argument(GOOGLE_LIST, type=str, required=False,
                        dest=GOOGLE_LIST_DEST,
                        help=HELP)
    return parser.parse_args()


def invoke_grades(mode, course_id, page):
    api_url = 'https://stepik.org/api/{}?course={}&page={}'.format(mode, course_id, page)
    return json.loads(
        requests.get(api_url, headers={'Authorization': 'Bearer ' + token}).text)


def invoke_username(user_id):
    api_url = 'https://stepik.org/api/users/{}'.format(user_id)
    return json.loads(
        requests.get(api_url, headers={'Authorization': 'Bearer ' + token}).text)["users"][0]["full_name"]


def transform_status(status):
    if status == "wrong":
        return "0"
    return "1"


def transform_date(date):
    date, time = date.split("T")
    date = date.split("-")
    year = date[0]
    month = date[1]
    day = date[2]
    date = month + DATE_SEP + day + DATE_SEP + year
    time = time.split("Z")
    res = date + " " + time[0]
    return res


def generate_result(data):
    return "" + str(current_user_id) + SEP + str(data["user"]) + SEP + invoke_username(str(data["user"])) + SEP + str(
        data["score"]) + '\n'


def read_user_ids():
    file = open("users", "r")
    contents = file.read()
    return contents.split(" ")


def check_args(course, key, sheet, sheet_list):
    if course is None:
        print("No course provided")
        exit(1)
    if sheet is None:
        print("No google sheet provided")
        exit(1)
    if sheet_list is None:
        print("No google sheet list  provided")
        exit(1)


if __name__ == '__main__':

    course = get_id().course_ID
    key = get_id().key
    sheet = get_id().sheet
    sheet_list = get_id().sheet_list
    check_args(course, key, sheet, sheet_list)
    if key is None:
        print("No keyfile is provided")
    else:
        print("Keyfile is provided")
        with open(key) as keyfile:
            client_id = keyfile.readline().strip()
            client_secret = keyfile.readline().strip()

    token = authorization()

    print("Request is in process, wait...")

    api_mode = "course-grades"
    FILEPATH = FILENAME + "_course" + course + CSV
    SUBMISSIONS_AMOUNT = 0
    page = 1

    users_to_find = dict()
    for temp in read_user_ids():
        users_to_find[temp] = False

    result = ["course_id;user_id;username;score" + '\n']

    while True:
        print("current page: " + str(page))
        response = invoke_grades(api_mode, course, page)
        meta = response["meta"]
        response = response[api_mode]
        response_size = len(response)

        for data in response:
            current_user_id = str(data["id"])
            if users_to_find.keys().__contains__(current_user_id):
                print("user " + current_user_id + " found")
                temp_result = generate_result(data)

                # temp_result = u''.join(temp_result).encode('utf-8')
                print(temp_result)
                result.append(temp_result)

                users_to_find[current_user_id] = True
            else:
                print("user " + str(current_user_id) + " not found, skipping results")
        if meta["has_next"] is not True:
            break
        page += 1

    with open(FILEPATH, "w") as csv_file:
        for temp in result:
            csv_file.write(str(temp))

    print("Path: " + sys.path[0] + "/" + FILEPATH)
    print("Statistics not found for the users:")
    for user_key in users_to_find.keys():
        if not users_to_find[user_key]:
            print(user_key)
    google_sheets_process(get_id().sheet, result, sheet_list)
