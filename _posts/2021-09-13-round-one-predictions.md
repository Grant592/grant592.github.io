---
layout: post
title: Gallagher Premiership - Round 1 Elo Predictions
comments: true
categories: [Stats, Rugby]
---

So here we are sports fans...the start of the new prem rugby season this weekend. Let's have a look at what our current [Elo rating system]({% post_url 2021-08-23-elo-ratings %}) is giving us for this weekend.

## Bristol vs Saracens  
One thing to note with this fixture is the rating system has taken Saracens Elo rating from the end of their relegation season and applied the same formula as every other team at the start of the season (i.e. regressed towards the mean).
```python
elo.predict_fixture('BRISTOL', 'SARACENS', teams)
>>> Bristol win = 71%
>>> Saracens win = 29%
```  
The bookies currently have Bristol down as 4/6 favourites compared to Saracens 8/5 odds. Our Elo rating gives an odds of 3/7 Bristol win.

## Leicester vs Exeter  
It's not looking good for Leicester at home to Exeter...
```python
elo.predict_fixture('LEICESTER', 'EXETER', teams)
>>> Leicester win = 27%
>>> Exeter win = 73%
```  
Bookies have Leicester at 8/5 with our Elo system putting it at roughly 3/1.

## Northampton vs Gloucester  
```python 
elo.predict_fixture('NORTHAMPTON', 'GLOUCESTER', teams)
>>> Northampton win = 40%
>>> Gloucester win = 60%
```  

Looks favourable for Gloucester away from home although it's fairly close. Bookies have 8/15 for Saints which is different to our 3/2.  

## Worcester vs London Irish  
```python 
elo.predict_fixture('WORCESTER', 'LONDON IRISH', teams)
>>> Worcester win = 37%
>>> London Irish win = 63%
```  

Looks a little bit different to the bookies odds who have Worcester at 19/20 compared to our systems 3/2  

## Sale vs Bath  
```python
elo.predict_fixture('SALE', 'BATH', teams)
>>> Sale win = 87%
>>> Bath win = 13%
```  
Sale look overwhelming favourites for this one with odds of nearly 1/9. Bookies don't quite have as strong odds with 4/11 for Sale.  

## Newcastle vs Harlequins  
```python
elo.predict_fixture('NEWCASTLE FALCONS', 'HARLEQUINS', teams)
>>> Newcastle Falcons win = 17%
>>> Harlequins win = 83%
```  

As reining champions, we've got Harlequins as strong favourites considering they're away from home at 1/4 whereas the bookies have them at 8/15. It's worth noting that Quins lost up at Kingston Park in Feb last season so maybe these odds are a bit extreme.  

## Closing Remarks  
So here's week one of the predictions. I should state that these aren't my personal predictions! The Elo system doesn't take into account any other contextual info other than a teams Elo score based off their previous results. Every team changes over the off season so signings/injuries etc will all make a big difference but aren't considered in these predictions. Maybe as the season progresses I'll look to add a few more features in...
