#!/usr/bin/python3

import sys
import requests
import argparse
import getpass
import csv
from datetime import datetime

def page_transactions(page):
    for j in page['transactionHistory']['transaction']:
        basepoints = usepoints = 0
        pt = j['basicPointsAfterTransaction']
        if pt in ['Basic Points', 'Swedish Domestic']:
            basepoints = int(j['availablePointsAfterTransaction'])
        if pt in ['Basic Points', 'Extra Points', 'Points Returned']:
            usepoints = int(j['availablePointsAfterTransaction'])
        if pt in ['Points Used', 'Points Expired']:
            usepoints = -int(j['availablePointsAfterTransaction'])
        yield (datetime.strptime(j['datePerformed'], '%Y-%m-%dT%H:%M:%S.%fZ').date(),
               pt,
               j.get('description', ''),
               basepoints,
               usepoints,
               )


def fetch_page(pageno, tokenjson):
    print("Fetching page {0}".format(pageno))
    r = requests.get('https://api.flysas.com/customer/euroBonus/getAccountInfo?pageNumber={0}&customerSessionId={1}'.format(pageno, tokenjson['customerSessionId']),
                    headers={'Authorization': tokenjson['access_token'], 'Referrer': 'www.sas.se', 'Origin': 'www.sas.se'},
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
                      headers={'Referrer': 'www.sas.se', 'Origin': 'www.sas.se', 'Authorization': 'Basic U0FTLVVJOg=='},
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

    transactions = list(page_transactions(page))
    highpage = 1
    if args.pages:
        highpage = min(args.pages, totalpages)
    elif args.all:
        highpage = totalpages

    if highpage > 1:
        for i in range(2, highpage+1):
            p = fetch_page(i, tokenjson)
            transactions.extend(list(page_transactions(p)))

    if args.csv:
        with open(args.csv, "w") as f:
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
