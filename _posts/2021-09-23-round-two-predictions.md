---
layout: post
title: Gallagher Premiership - Round 2 - Elo...more like E-No ratings
comments: true
categories: [Stats, Rugby]
---

Anyone hoping to find an article on Roxy Music and airport synth extraordinaire [Brian Eno](https://www.youtube.com/watch?v=vNwYtllyt3Q) may want to stop reading now. E-No was a more apt description of the Elo rating system after last week's win predictions which were right on 2 out of 6 of the fixtures. It certainly looks from last weeks scorelines (except Sarries vs Bristol) that home advantage is having more of an effect now that crowds are back. 

Here's the changes in Elo ratings after last weeks fixtures:


| Team   | Start of 2021-22 Season  | After Round 1  | Elo change  |
| -------|------------------------|----------------------------|---------|
Bristol | 1604 | 1524 | -80
Exeter | 1670 | 1595 | -75
Sale | 1647 | 1652 | +5
Harlequins | 1648 | 1668 | +20
Northampton | 1442 | 1503 | +61
Leicester | 1524 | 1599 | +75
Bath | 1459 | 1454 | -5
Wasps | 1427 | 1427 | 0
London Irish | 1357 | 1297 | -60
Newcastle Falcons | 1434 | 1415 | -19
Gloucester | 1522 | 1461 | -61
Worcester | 1264 | 1324 | +60
Saracens | 1532 | 1612 | +80

Big jumps up for Saracens and Leicester and correspondingly big drops for Bristol and Exeter. You'll notice that Sale were big favourites to win at home to Bath so due to those odds and home advantage, Sale's Elo rating barely changes. Once we get a few games into the season, hopefully the ratings will start to be a bit more reflective of this seasons form. Now onto this weeks odds...

## Gloucester vs Leicester
```python
elo.predict_fixture('GLOUCESTER', 'LEICESTER', teams)
>>> Gloucester win = 38%
>>> Leicester win = 62%
```  
Looking at roughly 9/5 for Gloucester which isn't too far off the bookies odds of 7/5

## Bath vs Newcastle
```python
elo.predict_fixture('BATH', 'NEWCASTLE', teams)
>>> Bath win = 63%
>>> Newcastle win = 37%
```  
Very similar odds to the Gloucester match with Newcastle at 9/5 whereas the bookies are backing Bath a bit more at 4/11  

## Exeter vs Nothampton
```python 
elo.predict_fixture('EXETER', 'NORTHAMPTON', teams)
>>> Exeter win = 69%
>>> Northampton win = 31%
```  
It takes a brave person not to back Exeter at Sandy Park. Clearly the Elo rating system knows this as well. It's looking fairly good for them at roughly 3/7 with similar odds from the bookies at 2/7.  

## Harlequins vs Worcester
```python 
elo.predict_fixture('HARLEQUINS', 'WORCESTER', teams)
>>> Harlequins win = 91%
>>> Worcester win = 9%
```  
I doubt many people can see anything other than a Quins win for this one but stranger things have happened. Elo system has them at 1/9 which is close to the bookies odds of 1/8.


## Wasps vs Bristol
```python
elo.predict_fixture('WASPS', 'BRISTOL', teams)
>>> Wasps win = 43%
>>> Bristol win = 57%
```  
This looks like a close one and with Wasps having a bye last week there's no real update on their form in the rating system from last year. We have Wasps at 8/6 whereas the bookies have them at 8/5.  

## London Irish vs Sale
```python
elo.predict_fixture('LONDON IRISH', 'SALE', teams)
>>> London Irish win = 15%
>>> Sale win = 85%
```  
OOSH...big odds for Sale to win away from home. I'm not sure Irish are as bad as the Elo ratings would suggest so it will be interesting to see how this one pans out. With Worcester having a low rating coming into the season and Irish losing to Worcester last week, that's had a big effect on their ratings coming into this match. Irish ar 17/3 but bookies have them at 8/5. 


## Closing Remarks  
A lot of this weeks odds seem to be roughly in line with what the bookies are offering. As I mentioned earlier, the Elo system should start to be a bit more reflective of each teams form as the season progresses...until the whole thing is thrown out of whack when the Autumn internationals start and teams begin to lose their players. Until then though, we'll crack on with the system as is and see how it fares. Thanks for reading.
