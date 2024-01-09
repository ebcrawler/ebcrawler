// ==UserScript==
// @name         EB downloader
// @namespace    http://github.com/ebcrawler
// @version      2024-01-09
// @description  Adds a button to the profile to download EB history as CSV
// @author       ebcrawler
// @match        https://www.sas.se/profile/
// @icon         data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==
// @grant        none
// ==/UserScript==

(function() {
    'use strict';


    const intervalID = setInterval(setupButton, 500);

    function setupButton() {
        let profileinit = document.querySelector('s4s-profile-init');
        if (!profileinit) {
            return;
        }
        clearInterval(intervalID);
        let newsection = document.createElement('section');
        let button = document.createElement('button');
        button.innerText = 'Download EB history';
        newsection.appendChild(button);
        profileinit.insertBefore(newsection, profileinit.firstChild);

        button.addEventListener("click", (e) => {
            button.innerText = 'Downloading, please wait, this is slow...';
            DoDownloadEBHistory(() => {
                button.innerText = 'Download EB history';
            });
        });
    }

    async function DoDownloadEBHistory(cb_finished) {
        let p = new S4SProfileInfo();
        let pi = await p.loadProfileInfo();
        let csvrows = [[['Date', 'Pointtype', 'Description', 'Base points', 'Points']]];

        pi.eurobonus.transactionHistory.transaction.forEach((t) => {
            let pt = t.basicPointsAfterTransaction.toLowerCase();
            let basepoints = 0;
            let usepoints = 0;

            if (pt === 'status points' || pt === 'mastercard status points') {
                basepoints = t.availablePointsAfterTransaction;
                usepoints = 0;
            }
            else if (pt === 'basic points' || pt === 'swedish domestic') {
                basepoints = t.availablePointsAfterTransaction;
                if (t.typeOfTransaction === 'Flightactivity' || t.typeOfTransaction === 'Flight Activity' || t.typeOfTransaction === 'Special Activity') {
                    usepoints = t.availablePointsAfterTransaction;
                }
            }
            else if (pt === 'extra points' || pt === 'points returned') {
                usepoints = t.availablePointsAfterTransaction;
            }
            else if (pt === 'points used' || pt === 'points expired') {
                usepoints = -t.availablePointsAfterTransaction;
            }
            else {
                alert('Unknown points type: ' + pt);
                return;
            }
            csvrows.push([
                t.datePerformed.split('T')[0],
                t.basicPointsAfterTransaction,
                '"' + t.description1 + ' ' + t.description2 + '"',
                basepoints,
                usepoints
            ]);
        });

        let newsection = document.getElementById('eurobonuscsv');
        if (!newsection) {
            let ebcontent = document.querySelector('div.eurobonus-content');
            newsection = document.createElement('section');
            newsection.id = 'eurobonuscsv';
            ebcontent.append(newsection);
        }
        newsection.innerHTML = '';

        let utf = new TextEncoder().encode(csvrows.join("\n"));
        let datauri = 'data:text/csv;base64,' + btoa(String.fromCodePoint(...utf));

        let link = document.createElement("a");
        link.innerText = 'Download CSV';
        link.href = datauri;
        link.download = 'eb.csv';
        newsection.appendChild(link);
        link.click();

        cb_finished();
    }
})();
