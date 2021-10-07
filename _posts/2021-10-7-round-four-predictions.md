---
layout: post
title: Gallagher Premiership - Round 3+4
comments: true
categories: [Stats, Rugby]
---

After missing a week here's what the teams looked like going into week 3 and then coming into round 4 this weeked:


| Team   | After Round 2  | After Round 3  | 
| -------|------------------------|----------------------------|
Harlequins | 1674 |  1674 | 
Leicester | 1629 | 1640 | 
Exeter | 1563 | 1632 | 
Saracens | 1612 | 1601 | 
Sale | 1652 | 1583 | 
Northampton | 1535 | 1541 | 
Newcastle Falcons | 1468 | 1500 | 
Wasps | 1513 | 1480 |
Gloucester | 1431 | 1466 | 
Bristol | 1438 | 1465 | 
Bath | 1401 | 1374 | 
London Irish | 1297 | 1291 | 
Worcester | 1318 | 1284 | 

I've ordered the table above by each teams current Elo rating and interestingly it doesn't look too similar to the actual Premiership table. On to this weeks fixtures.

## Harlequins vs Bristol
```python
elo.predict_fixture('HARELQUINS', 'BRISTOL', teams)
>>> Harlequins win = 82%
>>> Bristol win = 18%
```  

Elo system has Quins at roughly 1/4 whereas bookies put them at 4/9.

## Exeter vs Worcester
```python
elo.predict_fixture('EXETER', 'WORCESTER', teams)
>>> Exeter win = 91%
>>> Worcester win = 9%
```  
1/9 odds for Exeter here which is pretty close to the bookies odds at 1/10.

## Gloucester vs Sale
```python 
elo.predict_fixture('GLOUCESTER', 'SALE', teams)
>>> Gloucester win = 40%
>>> Sale win = 60%
```  

Gloucester coming in at 6/4 which is exactly the same as the bookies this week.

## London Irish vs Leicester
```python 
elo.predict_fixture('LONDON IRISH', 'LEICESTER', teams)
>>> London Irish win = 15%
>>> Leicester win = 85%
```  
Leicester strong favourites as expected here at 5/17, bookies not as optimistic with them at 4/6.

## Saracens vs Newcastle
```python
elo.predict_fixture('SARACENS', 'NEWCASTLE', teams)
>>> Saracens win = 70%
>>> Newcastle win = 30%
```  
Newcastle are the underdogs for this fixture with odds of 7/3. Bookies favouring Sarries much more at 1/10. 


## Wasps vs Northampton
```python
elo.predict_fixture('WASPS', 'NORTHAMPTON', teams)
>>> Wasps win = 48%
>>> Northampton win = 52%
``` 
This is close with both teams evenly matched. The bookies have Wasps as slight favourites at 4/6. 

## Closing Remarks  
It's interesting seeing how the Elo ratings table compares to the Prem table. Elo probably gives a better reflection of the true quality of the team at the moment compared to the actual table. I can't imagine Worcester will stay too high up the table whereas most people will probably expect Bristol, Exeter and Saracens to quickly climb up. Hopefully I'll get time to pose something slightly different next week and look at Force Velocity profiling for team sports.
