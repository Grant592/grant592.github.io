---
layout: post
title: Elo Ratings
comments: true
categories: [Stats, Rugby]
---

Mr Blue Sky - 7/10  
Don't Bring Me Down - 8/10  
Evil Woman - 5/10  

Always good to start with a really terrible joke. Anyway, to the proper stuff...

The Elo rating system was originally developed by Arpad Elo as an improved chess-rating system but has been taken on by loads of other sports bodies and stats sites as a ranking system. From [Wikipedia](https://en.wikipedia.org/wiki/Elo_rating_system):  
> A player's Elo rating is represented by a number which may change depending on the outcome of rated games played. After every game, the winning player takes points from the losing one. The difference between the ratings of the winner and loser determines the total number of points gained or lost after a game. If the high-rated player wins, then only a few rating points will be taken from the low-rated player. However, if the lower-rated player scores an upset win, many rating points will be transferred. The lower-rated player will also gain a few points from the higher rated player in the event of a draw. This means that this rating system is self-correcting. Players whose ratings are too low or too high should, in the long run, do better or worse correspondingly than the rating system predicts and thus gain or lose rating points until the ratings reflect their true playing strength.
> An Elo rating is a comparative rating only, and is valid only within the rating pool where it was established  
[FiveThirtyEight](https://fivethirtyeight.com/methodology/how-our-nfl-predictions-work/) have some fantastic explanations for how they run their Elo rating systems so I'll not try and explain how these guys do it but it's definitely worth a read to see a system in a bit more depth. I'll focus this on how I've implemented the system and how I've tuned some of the parameters.

One of the articles I came across the sparked my interest in this was [this one](https://sites.northwestern.edu/msia/2019/01/25/introducing-a-new-rating-system-for-world-rugby-union-based-on-the-elo-rating-system-the-elor-elo-rugby/) although there was a bit of trawling the web to fill in a few blanks in some of the details.

## Calculating Elo ratings  
There's two factors we need to take into consideration when calculating Elo ratings - the k factor and the home advantage (I'll refer to these a $k$ and $HA$). I'll come onto these later but thought I'd highlight them now so nobody wonders where they've come from in the equation. All you need to know now for now is that they're constants and don't change. We'll use an example of two teams as we go through the calcs to see what's going on. TeamA have an Elo rating of 1600 and TeamB of 1400 (unlucky TeamB). We'll start with home advantage = 50 and k = 50.

### Step 1 - Calculate transformed ratings
$$
R_{home} = 10^{(ELO_H + HA)/400}  
$$  
$$
R_{away} = 10^{(ELO_A)/400}  
$$

Calculating this for TeamA and TeamB gives us $R_{TeamA} = 10^{(1600 + 50)/400} = 13335$ and $R_{TeamA} = 10^{1400/400} = 3162$ 

### Step 2 - Calculate expected scores  
The expected scores will return a probability for each team. It's not necessarily how likely a team is to win but interpreted more as if the game was played 100 times, then this team would win X number of times.    

$$
E_{home} = \frac{R_{home}}{R_{home} + R_{away}}
$$  
$$
E_{away} = \frac{R_{away}}{R_{home} + R_{away}}
$$  

As above, for TeamA this would be $13335/(13335+3162) = 0.808$ and for TeamB this would be $3162/(13335+3162) = 0.192$. Given these are probabilities then we only really need to calculate TeamA and TeamB is just 1 - TeamA. This means that out of 100 games between TeamA and TeamB at their current Elo ratings, TeamA would be expected to win roughly 80% of the time.   
### Step 3 - Margin of victory multiplier  
In rugby, we need something to assess not only the outcome of a match but also how a team win. The margin of victory multiplier (*MOVM*) takes the natural log of the winning points difference to reduce the impact of huge margins on Elo ratings. If a good team has a huge win against a poor team, this will ensure that their Elo rating is not artificially inflated. Alongside this there is also an *autocorrelation* adjustment. Autocorrelation is a measure of how a time series is correlated with past and future values. In Elo ratings, the top teams win more often (obviously) and put up larger winning margins. The Elo systems rewards larger wins meaning the top teams ratings can become inflated over time. The margin of victory is scaled down for teams that were bigger favourites going into the game 

$$
MOVM = ln(\mbox{WinningPointDiff} + 1) \cdot \frac{2.2}{(\mbox{Elo}_{Win} - \mbox{Elo}_{Lose}) \cdot 0.001 + 2.2} 
$$  

The MOVM is the same for both teams. First let's look at what the first part of the equation is doing. We need to take into account the margin of victory without unfairly rewarding huge margins, especially in rugby where you can occasionally a really big points margin. If a team won by one point, then $ln(\mbox{WinningPointDiff + 1})$ would return a value of 0.69 whereas if a team won by 50 points, we would get a value of 3.9. We can see how a larger margin results in a greater MOVM but by using a logarithm, it dampens the effect of extreme margins. Now lets look at the second part of the equation, the correlation coefficient. Let's assume TeamA win, the correlation coefficient would be $\frac{2.2}{(1600-1400)\cdot 0.001 + 2.2} = 0.92$. Now let's assume TeamB win and the coefficient would be $\frac{2.2}{(1400-1600)\cdot 0.001 + 2.2} = 1.1$. If we consider the second scenario where TeamB win, this would be classed as an upset meaning the correlation coefficient is greater than 1 and acts to increase the MOVM. If TeamA won, the coefficient is less than 1 meaning it would decrease the MOVM. We'll be able to see the impact of this in step 4.


### Step 4 - Update Elo ratings  
Now we've calculated all the various parts, all we need to do is multiply them together and update the original ELo rating. The $\mbox{home win}$  value is just a binary value with a 1 for a home win, 0 for home loss and 0.5 for a draw (and the same for $\mbox{away win}$).
$$
Elo_{home_{updated}} = Elo_{home} + k \cdot  MOVM  \cdot (\mbox{home win} - E_{home}) 
$$   
$$
Elo_{away_{updated}} = Elo_{away} + k \cdot  MOVM  \cdot (\mbox{away win} - E_{away}) 
$$   

In step 3, we looked at the effect of MOVM and we can see what it is doing when updating the Elo ratings. If the favourite wins, the MOVM is less than 1 and therefore acts to reduce the overall impact of the result when updating the Elo values i.e. the winning team gains only a few points and the losing team loses only a few points. If the underdog wins, the MOVM is greater than 1 and therefore acts to increase the number of points that a weaker team takes from a stronger team and vice versa. 

Let's assume that TeamA wins by a margin of 50 points. The Elo ratings would be updated as follows:
$$
Elo_{home_{updated}} = 1600 + 50 \cdot 3.9 \cdot 0.92 \cdot (1 - 0.808) = 1634
$$  

$$
Elo_{away_{updated}} = 1400 + 50 \cdot 3.9 \cdot 0.92 \cdot (0 - 0.192) = 1365 
$$

Notice only 34 points transferred from the losing team to the winning team. Now let's assume TeamB wins by a 50 point margin which would be considered a bog upset.

$$
Elo_{home_{updated}} = 1600 + 50 \cdot 3.9 \cdot 1.1 \cdot (0 - 0.808) = 1427
$$  

$$
Elo_{away_{updated}} = 1400 + 50 \cdot 3.9 \cdot 1.1 \cdot (1 - 0.192) = 1573
$$

Now see what happens when an underdog pulls off a huge upset; there is a massive shift in points from TeamA to TeamB, so much that they almost completely reverse their ratings.  

### Round Up  
Hopefully this has shed some light on how Elo ratings work (and not ELO ratings if you didn't get the opening joke) and the effect of scoreline and which team is favourite. In the following posts I'll go over how I've coded these ratings up  









