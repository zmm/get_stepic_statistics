#!/usr/bin/python3.7

import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import argparse
import sys
from time import sleep

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
CELL_RANGE = "--cell_range"
CELL_RANGE_DEST = "cell_range"
STEPIK_ID_SOURCE_SHEET = "--stepik_id_source_sheet"
STEPIK_ID_SOURCE_SHEET_DEST ="stepik_id_source_sheet"


FILENAME = "statistics"
CSV = ".csv"
SEP = ";"
DATE_SEP = "/"


def authorize_google_sheets():
    scope = ['https://spreadsheets.google.com/feeds']
    creds = ServiceAccountCredentials.from_json_keyfile_name('google_api_key.json', scope)
    return gspread.authorize(creds)

def get_users_list(client, sheet_url, cell_range, sheet_name):
    sheet = client.open_by_key(sheet_url).worksheet(sheet_name)
    users = sheet.range(cell_range)
    result = {}
    for user in users:
        if user.value.isdigit():
            result[user.value] = False
    return result
 

def google_sheets_process(client, sheet_url, result, sheet_list):
    print(sheet_url)
    print(sheet_list)
    sheet = client.open_by_key(sheet_url).worksheet(sheet_list)
    index = 2
    first_cell = sheet.acell('A1').value
    if first_cell != "course_id":
        sheet.insert_row("course_id;user_id;username;score".split(";"), 1)

    updates = 0

    for row in result:
        result_to_insert = row.replace("\n", "").split(";")        
        for i in range(1,5):
            sleep(1)
            if updates % 90 == 0:
               sleep(10)
            sheet.update_cell(index, i, result_to_insert[i-1])
            updates += 1
#        sheet.insert_row(row.replace("\n", "").split(";"), index)
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
    parser.add_argument(CELL_RANGE, type=str, required=False,
                        dest=CELL_RANGE_DEST,
                        help=HELP)
    parser.add_argument(STEPIK_ID_SOURCE_SHEET, type=str, required=False,
                        dest=STEPIK_ID_SOURCE_SHEET_DEST,
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
    return "" + str(data["course"]) + SEP + str(data["user"]) + SEP + invoke_username(str(data["user"])) + SEP + str(
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



    client = authorize_google_sheets()
#    get_users_list(client, "1l1dGLnxLiL03eFZu-O1b6zrrWXubYrxbXBtBMthVy54", "E2:E85", "Form Responses 1")

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

    users_to_find = get_users_list(client, sheet, get_id().cell_range, get_id().stepik_id_source_sheet)
#    for temp in read_user_ids():
#        users_to_find[temp] = False

    users_found = 0
    result = []
    while users_found < len(users_to_find):
        print("current page: " + str(page))
        response = invoke_grades(api_mode, course, page)
        meta = response["meta"]
        response = response[api_mode]
        response_size = len(response)
        for data in response:
            current_user_id = str(data["user"])
            if users_to_find.keys().__contains__(current_user_id):
#                print("user " + current_user_id + " found")
                users_found = users_found + 1
                temp_result = generate_result(data)

                # temp_result = u''.join(temp_result).encode('utf-8')
                print(temp_result)
                result.append(temp_result)

                users_to_find[current_user_id] = True
#            else:
#                print("user " + str(current_user_id) + " not in list, skipping")
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
    google_sheets_process(client, get_id().sheet, result, sheet_list)
