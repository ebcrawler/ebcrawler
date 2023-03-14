#!/usr/bin/python3

import sys
import requests
import argparse
import getpass
import csv
from datetime import datetime

def getdescription(j):
    if j.get('decription', None):
        return j['description']
    return "{0} {1}".format(j.get('description1', ''), j.get('description2', ''))

def page_transactions(page, debug):
    for j in page['transactionHistory']['transaction']:
        if debug:
            print(j)
        d = datetime.strptime(j['datePerformed'], '%Y-%m-%dT%H:%M:%S.%fZ').date()
        basepoints = usepoints = 0
        ptfull = j['basicPointsAfterTransaction']
        pt = ptfull.lower()
        if pt in ['status points', 'mastercard status points']:
            # Status points only, e.g. mastercard
            basepoints = int(j['availablePointsAfterTransaction'])
            usepoints = 0
        elif pt in ['basic points', 'swedish domestic']:
            basepoints = int(j['availablePointsAfterTransaction'])
            if j['typeOfTransaction'] in ('Flightactivity', 'Flight Activity', 'Special Activity'):
                # Flights give both basic and usable points
                usepoints = int(j['availablePointsAfterTransaction'])
            elif j['typeOfTransaction'] == 'Transactioncorrection':
                # E.g. Amex points (old style?)
                pass
            else:
                print("Unknown type for base points: %s" % j['typeOfTransaction'])
        elif pt in ['extra points', 'points returned']:
            usepoints = int(j['availablePointsAfterTransaction'])
        elif pt in ['points used', 'points expired']:
            usepoints = -int(j['availablePointsAfterTransaction'])
        else:
            print("Unknown transaction: %s" % j)
        yield (d,
               ptfull,
               getdescription(j),
               basepoints,
               usepoints,
               )


def fetch_page(pageno, tokenjson):
    print("Fetching page {0}".format(pageno))
    token = tokenjson['access_token']
    sessionid = tokenjson['customerSessionId']
    r = requests.get('https://api.flysas.com/customer/euroBonus/getAccountInfo?pageNumber={0}&customerSessionId={1}'.format(pageno, sessionid),
                    headers={'Authorization': token,
                             'Referer': 'https://www.sas.se/',
                             'Origin': 'https://www.sas.se',
                             'Accept': 'application/json, text/plain, */*',
                    },
                    )
    if r.status_code != 200:
        print("Failed to get page {0}:".format(pageno))
        print(r.text)
        sys.exit(1)

    return r.json()['euroBonus']

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EuroBonus transaction crawler")
    parser.add_argument('ebnumber', type=str, help='EuroBonus number')
    parser.add_argument('--password', type=str, help='Password')
    parser.add_argument('--all', action='store_true', help='Crawl all transactions')
    parser.add_argument('--pages', type=int, help='Number of pages to crawl')
    parser.add_argument('--csv', type=str, help='Write to file in CSV format')
    parser.add_argument('--debug', action='store_true', help='Enable debugging')

    args = parser.parse_args()

    if args.all and args.pages:
        print("Can't specify both all and number of pages.")
        sys.exit(1)

    if args.password:
        password = args.password
    else:
        password = getpass.getpass('Password for EB{0}: '.format(args.ebnumber))

    print("Logging in...")
    r = requests.post('https://api.flysas.com/authorize/oauth/token',
                      data={'grant_type': 'password', 'username': args.ebnumber, 'password': password},
                      headers={'Referer': 'https://www.sas.se/',
                               'Origin': 'https://www.sas.se',
                               'Authorization': 'Basic U0FTLVVJOg==',
                               'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                               'accept': 'application/json, text/plain, */*'
                      },
                      )
    if r.status_code != 200:
        print("Failed to log in:")
        print(r.text)
        sys.exit(1)
    tokenjson = r.json()

    page = fetch_page(1, tokenjson)
    print("Base points:    {0}".format(int(page['pointsAvailable'])))
    print("Total points:   {0}".format(int(page['totalPointsForUse'])))
    totalpages = int(page['transactionHistory']['totalNumberOfPages'])

    transactions = list(page_transactions(page, args.debug))
    highpage = 1
    if args.pages:
        highpage = min(args.pages, totalpages)
    elif args.all:
        highpage = totalpages

    if highpage > 1:
        for i in range(2, highpage+1):
            p = fetch_page(i, tokenjson)
            transactions.extend(list(page_transactions(p, args.debug)))

    if args.csv:
        with open(args.csv, "w", encoding='utf8') as f:
            c = csv.writer(f)
            c.writerow(['Date', 'Pointtype', 'Description', 'Base points', 'Points'])
            for r in transactions:
                c.writerow(r)
    else:
        fmtstr = "{0: <10} {1: <17} {2: <50} {3:>9} {4:>9}"
        # Plain output/sync format
        h = fmtstr.format("DATE", "POINTTYPE", "DESCRIPTION", "BASE", "POINTS")
        print(h)
        print("-" * len(h))
        for d,tp,desc,bp,up in transactions:
            print(fmtstr.format(
                d.strftime('%Y-%m-%d'), # Date
                tp[:17],                # Type of points
                desc[:50],              # Description
                bp,                     # Base points
                up,                     # Use points
            ))

    print("Fetched {0} EuroBonus transactions.".format(len(transactions)))
