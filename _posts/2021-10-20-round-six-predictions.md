---
layout: post
title: Prem Round 6 Predictions + Force Velocity Update
comments: true
categories: [Stats, Rugby, Sports Science]
---

Welcome to Round 6 predictions from the Elo rating system. Firstly a quick update on the force-velocity dashboard that I posted about last week.

## Force Velocity Update  
So I had a few questions about how to use the dashboard and realised some of the caveats were only mentioned if the reader visited this [link](https://github.com/Grant592/force-velocity-app). Here are the requirements for the csv file if you want to be able to use the dashboard:
* The field delimiter should be a semicolon ';' and delete any column headers.
* The csv should have 5 columns. The app only reads the time (in seconds) and velocity columns, however these should be the first and third columns of the csv respectively. It was built to handle a csv with these columns `['time', 'data', 'velocity','lat', 'lon']` but as long as it has time and velocity in the correct position, it'll work OK (in theory!).  
* Don't trim the sprints in your GPS software so that it stops at the top speed. The app extracts the peaks in the GPS trace so it needs the accel and the decel phase to extract the info.  
* The filename should be in the format '{firstname_surname}-{bodyweight in kg}-{date}.csv' for example 'john_smith-96-20211020.csv' 

Hopefully that will resolve any issues anybody had.

### Elo Ratings Round 6

So not a bad week for the Elo system last week. 4 matches predicted correctly, Sale throwing a spanner in the works by beating Quins and then a draw. Let's see what the Elo ratings look like after round 5:  

| Team   | After Round 4  | After Round 5  | 
| -------|------------------------|----------------------------|
Exeter | 1643 | 1668 |
Leicester | 1649 | 1667 | 
Saracens | 1632 | 1665 | 
Harlequins | 1697 | 1646 | 
Sale | 1566 | 1616 |
Newcastle Falcons | 1469 | 1503 |
Northampton | 1500 | 1500
Wasps | 1522 | 1497 |
Gloucester | 1483 | 1483 |
Bristol | 1442 | 1408 |
Bath | 1374 | 1341 |
London Irish | 1282 | 1282 |
Worcester | 1272 | 1255 |

And the predictions for this week are:

```python  
elo.predict_fixture('NORTHAMPTON', 'WORCESTER', teams)
>>> Northampton win = 85%
>>> Worcester win = 15%

elo.predict_fixture('EXETER', 'LONDON IRISH', teams)
>>> Exeter win = 92%
>>> London Irish win = 8%

elo.predict_fixture('GLOUCESTER', 'NEWCASTLE FALCONS', teams)
>>> Gloucester win = 54%
>>> Newcastle Falcons win = 46%

elo.predict_fixture('HARLEQUINS', 'BATH', teams)
>>> Harlequins win = 89%
>>> Bath win = 11%

elo.predict_fixture('LEICESTER', 'SALE', teams)
>>> Leicester win = 64%
>>> Sale win = 36%

elo.predict_fixture('SARACENS', 'WASPS', teams)
>>> Saracens win = 78%
>>> Wasps win = 22%
```

Looks like it could be close ones for Gloucester/Falcons and Leicester/Sale and I doubt Bath fans will be looking forward to facing Quins after last weekends results. The bookies have got similar odds with:
* Northampton/Worcester with Saints at 1/8
* Chiefs/Irish with Exeter at 1/11
* Gloucester/Falcons with Gloucester at 4/9
* Quins/Bath with Quins at 1/8
* Leicester/Sale with Tigers at 3/8 compared to our 3/5  
* Big odds on a home win for Sarries with the bookies having them at 1/20. The Elo system isn't quite giving such extreme odds but it's difficult to see Sarries losing at home.

Another week in and the Elo ratings table is starting to reflect this seasons form a bit better. Bath are being saved from being rock bottom of the Elo ratings by the virtue of a few of the close losses they had earlier in the season although on their current form they won't be moving up without some big upsets!  








