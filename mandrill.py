#!/usr/bin/env python

import argparse
import requests
import json
from colorclass import Color
from terminaltables import SingleTable
from textwrap import wrap
from datetime import datetime, timedelta

URL = 'https://mandrillapp.com/api/1.0/'

class Mandrill(object):

    def call(self, args):
        method=getattr(self, args.action, lambda :'Invalid action')
        return method(args)

    def search(self, args):
        start = datetime.today() + timedelta(days=-args.days)
        end = datetime.today()
        payload = {
            "key": args.key,
            "query": args.query,
            "date_from": start.strftime("%Y-%m-%d"),
            "date_to": end.strftime("%Y-%m-%d"),
            "limit": 100
        }

        r = requests.post(
            "{}{}".format(URL, 'messages/search.json'),
            json=payload
        )

        if r.status_code != 200:
            raise Exception(r.json())

        data = [["ID", "Subject", "To", "State", "Opens/Clicks", "Timestamp"]]
        for email in r.json():
            data.append([
                email["_id"],
                email["subject"],
                email["email"],
                email["state"],
                "{}/{}".format(email["opens"], email["clicks"]),
                datetime.utcfromtimestamp(email["ts"]).strftime('%Y-%m-%d %H:%M:%S')
            ])

        table_instance = SingleTable(data)
        table_instance.inner_heading_row_border = True
        table_instance.justify_columns[0] = 'right'
        table_instance.justify_columns[3] = 'center'
        table_instance.justify_columns[4] = 'right'
        table_instance.justify_columns[5] = 'right'
        table_instance.inner_row_border = True
        print(table_instance.table)

    def info(self, args):
        payload = {
            "key": args.key,
            "id": args.id,
        }

        r = requests.post(
            "{}{}".format(URL, 'messages/content.json'),
            json=payload
        )
        if r.status_code != 200:
            raise Exception(r.json())

        email = r.json()

        r = requests.post(
            "{}{}".format(URL, 'messages/info.json'),
            json=payload
        )
        if r.status_code != 200:
            raise Exception(r.json())

        info = r.json()

        smtp_data = [["TS", "Type", "diag"]]
        for event in info["smtp_events"]:
            smtp_data.append([
                datetime.utcfromtimestamp(event["ts"]).strftime('%Y-%m-%d %H:%M:%S'),
                event["type"],
                event["diag"]
            ])

        events_table = SingleTable(smtp_data)
        events_table.outer_border = False
        events_table.inner_heading_row_border = True
        events_table.inner_row_border = True
        events_table.inner_column_border = True

        data = [
            ["Subject", email["subject"]],
            ["To", email["to"]["email"]],
            ["Timestamp", datetime.utcfromtimestamp(email["ts"]).strftime('%Y-%m-%d %H:%M:%S')],
            ["State", info["state"]],
            ["SMTP events", events_table.table],
            ["Text", ""],
            ["HTML", ""]
        ]

        table_instance = SingleTable(data)
        table_instance.inner_row_border = True
        table_instance.inner_heading_row_border = False
        max_width = table_instance.column_max_width(1)
        wrapped_text = '\n'.join(wrap(email["text"], max_width))
        wrapped_html = '\n'.join(wrap(email["html"], max_width))
        table_instance.table_data[5][1] = wrapped_text
        table_instance.table_data[6][1] = wrapped_html

        print(table_instance.table)

    def reject_add(self, args):
        for email in args.email:
            payload = {
                "key": args.key,
                "email": email
            }
            if args.subaccount is not None:
                payload["subaccount"] = args.subaccount

            r = requests.post(
                "{}{}".format(URL, 'rejects/add.json'),
                json=payload
            )
            if r.status_code != 200:
                print("Failed to add email '{}' to rejection list".format(email))
                print(r.json())
            else:
                print("Email '{}' added to rejection list".format(email))

    def reject_remove(self, args):
        for email in args.email:
            payload = {
                "key": args.key,
                "email": email
            }
            if args.subaccount is not None:
                payload["subaccount"] = args.subaccount

            r = requests.post(
                "{}{}".format(URL, 'rejects/delete.json'),
                json=payload
            )
            if r.status_code != 200:
                print("Failed to delete email '{}' from rejection list".format(email))
                print(r.json())
            else:
                print("Email '{}' deleted from rejection list".format(email))

    def reject_list(self, args):
        payload = {
            "key": args.key
        }
        if args.subaccount is not None:
            payload["subaccount"] = args.subaccount

        r = requests.post(
            "{}{}".format(URL, 'rejects/list.json'),
            json=payload
        )
        if r.status_code != 200:
            raise Exception(r.json())

        data = [["Email", "Reason", "CreatedAt", "LastEventOn", "ExpiresAt", "SubAccount"]]
        for email in r.json():
            if email["reason"] == "soft-bounce":
                reason = Color("{autoyellow}" + email["reason"] + "{/autoyellow}")
            elif email["reason"] == "spam":
                reason = Color("{autoblue}" + email["reason"] + "{/autoblue}")
            else:
                reason = Color("{autored}" + email["reason"] + "{/autored}")

            data.append([
                email["email"],
                reason,
                email["created_at"],
                email["last_event_at"],
                email["expires_at"],
                email["subaccount"]
            ])

        table_instance = SingleTable(data)
        table_instance.inner_heading_row_border = True
        table_instance.justify_columns[2] = 'right'
        table_instance.justify_columns[3] = 'right'
        table_instance.justify_columns[4] = 'right'
        table_instance.inner_row_border = True
        print(table_instance.table)

    def permit_add(self, args):
        for email in args.email:
            payload = {
                "key": args.key,
                "email": email
            }

            r = requests.post(
                "{}{}".format(URL, 'whitelist/add.json'),
                json=payload
            )
            if r.status_code != 200:
                print("Failed to add email '{}' to permission list".format(email))
                print(r.json())
            else:
                print("Email '{}' added to permission list".format(email))

    def permit_remove(self, args):
        for email in args.email:
            payload = {
                "key": args.key,
                "email": email
            }

            r = requests.post(
                "{}{}".format(URL, 'whitelist/delete.json'),
                json=payload
            )
            if r.status_code != 200:
                print("Failed to delete email '{}' from permission list".format(email))
                print(r.json())
            else:
                print("Email '{}' deleted from permission list".format(email))

    def permit_list(self, args):
        payload = {
            "key": args.key
        }
        if args.subaccount is not None:
            payload["subaccount"] = args.subaccount

        r = requests.post(
            "{}{}".format(URL, 'whitelist/list.json'),
            json=payload
        )
        if r.status_code != 200:
            raise Exception(r.json())

        data = [["Email", "Detail", "CreatedAt"]]
        for email in r.json():
            data.append([
                email["email"],
                email["detail"],
                email["created_at"]
            ])

        table_instance = SingleTable(data)
        table_instance.inner_heading_row_border = True
        table_instance.justify_columns[2] = 'right'
        table_instance.justify_columns[3] = 'right'
        table_instance.justify_columns[4] = 'right'
        table_instance.inner_row_border = True
        print(table_instance.table)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Mandrill Helper', prog="mandrill")
    # parser.add_argument('-k', '--key', help='API Key to use')

    subparser = parser.add_subparsers(title="Action", metavar="")
    parser_query = subparser.add_parser("search", help="Performs a search on sent emails")
    parser_query.add_argument('--action', required=False, default='search', help=argparse.SUPPRESS)
    parser_query.add_argument('-k', '--key', help='API Key to use')
    parser_query.add_argument('--days', help='How many days ago to perform search (defaults to 7)', type=int, default=7)
    parser_query.add_argument('query', help='Which query to perform search on')

    parser_info = subparser.add_parser("info", help="Check the information of a specific sent email")
    parser_info.add_argument('--action', required=False, default='info', help=argparse.SUPPRESS)
    parser_info.add_argument('-k', '--key', help='API Key to use')
    parser_info.add_argument('id', help='Which email to get contents from', default="")

    parser_reject = subparser.add_parser("reject", help="Add/Remove/List emails from Rejection List")
    subparser_reject = parser_reject.add_subparsers(title="Rejection List", metavar="")
    parser_reject_action = subparser_reject.add_parser("remove", help="Removes an email from the rejections list")
    parser_reject_action.add_argument('--action', required=False, default='reject_remove', help=argparse.SUPPRESS)
    parser_reject_action.add_argument('-k', '--key', help='API Key to use')
    parser_reject_action.add_argument('-s', '--subaccount', nargs='?', help="Desired SubAccount to perform action")
    parser_reject_action.add_argument('email', nargs='+', help="List of emails to be removed")
    parser_reject_action = subparser_reject.add_parser("add", help="Adds an email from the rejections list")
    parser_reject_action.add_argument('--action', required=False, default='reject_add', help=argparse.SUPPRESS)
    parser_reject_action.add_argument('-k', '--key', help='API Key to use')
    parser_reject_action.add_argument('-s', '--subaccount', nargs='?', help="Desired SubAccount to perform action")
    parser_reject_action.add_argument('email', nargs='+', help="List of emails to be added")
    parser_reject_action = subparser_reject.add_parser("list", help="List emails on the rejections list")
    parser_reject_action.add_argument('--action', required=False, default='reject_list', help=argparse.SUPPRESS)
    parser_reject_action.add_argument('-k', '--key', help='API Key to use')
    parser_reject_action.add_argument('-s', '--subaccount', nargs='?', help="Desired SubAccount to perform action")

    parser_permit = subparser.add_parser("permit", help="Add/Remove/List emails from Permission List")
    subparser_permit = parser_permit.add_subparsers(title="Permission List", metavar="")
    parser_permit_action = subparser_permit.add_parser("remove", help="Removes an email from the permissions list")
    parser_permit_action.add_argument('--action', required=False, default='permit_remove', help=argparse.SUPPRESS)
    parser_permit_action.add_argument('-k', '--key', help='API Key to use')
    parser_permit_action.add_argument('-s', '--subaccount', nargs='?', help="Desired SubAccount to perform action")
    parser_permit_action.add_argument('email', nargs='+', help="List of emails to be removed")
    parser_permit_action = subparser_permit.add_parser("add", help="Adds an email from the permissions list")
    parser_permit_action.add_argument('--action', required=False, default='permit_add', help=argparse.SUPPRESS)
    parser_permit_action.add_argument('-k', '--key', help='API Key to use')
    parser_permit_action.add_argument('-s', '--subaccount', nargs='?', help="Desired SubAccount to perform action")
    parser_permit_action.add_argument('email', nargs='+', help="List of emails to be added")
    parser_permit_action = subparser_permit.add_parser("list", help="List emails on the permissions list")
    parser_permit_action.add_argument('--action', required=False, default='permit_list', help=argparse.SUPPRESS)
    parser_permit_action.add_argument('-k', '--key', help='API Key to use')
    parser_permit_action.add_argument('-s', '--subaccount', nargs='?', help="Desired SubAccount to perform action")

    args = parser.parse_args()

    try:
        Mandrill().call(args)
    except Exception as e:
        print(e)
