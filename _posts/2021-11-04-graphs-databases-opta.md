---
layout: post
title: Graph Databases for Rugby Analysis
comments: true
categories: [Neo4J, Graph Databases, Rugby]
---

Continuing on the theme of graph databases, I thought this week I would have a look at how we can model and gain insight from some rugby data through Neo4j. The data source is an Opta SuperScout XML which I've parsed but unfortunately can't share the data source itself. The result is a few different tables including:
* Fixture data - scoreline, referee, team ID's
* Team data - which players played, shirt numbers, position, number of minutes.  
* Match stats - each instance/action from throughout the match assigned to each player and team who performed the action.  

I'll not delve too deep into the layout of the XML but instead look more closely at how we can build a graph database model from the data.  

### Creating a fixture, team and referee

The first step in creating the data model was importing the fixture data resulting in nodes for `Fixture`, `Referee` and `Team`. This involves creating constraints on each of these node types in order to prevent duplication and to make querying with Cypher more efficient.  

```python  
def load_fixture_data(fix_data, driver):
    
    # Retrieve fixture data from input
    fxid = fix_data[0]
    fixtureDate = fix_data[1]
    fxHTID = fix_data[2]
    fxATID = fix_data[3]
    HTFTSC = fix_data[4]
    htName = fix_data[5]
    ATFTSC = fix_data[6]
    atName = fix_data[7]
    refId = fix_data[8]
    refName = fix_data[9]
    
    with driver.session() as session:
        try:
            session.run(
                "CREATE CONSTRAINT UniqueFixture IF NOT EXISTS ON (f:Fixture) ASSERT f.FXID IS UNIQUE  "
            )

            session.run(
                "CREATE CONSTRAINT UniqueRef IF NOT EXISTS ON (r:Referee) ASSERT r.refId IS UNIQUE  "
            )

            session.run(
                "CREATE CONSTRAINT UniqueTeam IF NOT EXISTS ON (t:Team) ASSERT t.teamId IS UNIQUE  "
            )

            session.run(
                """
                MERGE (f:Fixture {fxid: $fxid})
                ON CREATE SET 
                  f.fixtureDate = $fixtureDate,
                  f.HTFTSC = $HTFTSC,
                  f.ATFTSC = $ATFTSC
                MERGE (ht:Team {teamId: $fxHTID})
                ON CREATE SET
                  ht.name = $htName
                MERGE (at:Team {teamId: $fxATID})
                ON CREATE SET
                  at.name = $atName
                MERGE (r:Referee {refId: $refId})
                ON CREATE SET
                  r.name = $refName
                MERGE (ht)-[:PLAYED_IN]->(f)<-[:PLAYED_IN]-(at)
                MERGE (r)-[:REFEREED]->(f)
                """,
                fxid=fxid, fixtureDate=fixtureDate, fxHTID=fxHTID, fxATID=fxATID, HTFTSC=HTFTSC, 
                ATFTSC=ATFTSC, htName=htName, atName=atName, refId=refId, refName=refName
            )
        except(Error) as e:
            print(e)
```  

![](/images/fix_data.png)    
  
### Importing all players for a fixture  
The next stage was to import all the players who played in a given fixture...  

```python  
def load_player_data(player_data, driver):
    
    with driver.session() as session:
        session.run(
            "CREATE CONSTRAINT UniquePlayer IF NOT EXISTS ON (p:Player) ASSERT p.PLID IS UNIQUE  "
        )

    
    for player in player_data:
        fxid = player[0]
        PLID = player[1]
        shirtNumber = player[2]
        teamId = player[3]
        posId = player[4]
        plForn = player[5]
        plSurn = player[6]
        mins = player[7]

        with driver.session() as session:

            session.run(
                """
                MERGE (p:Player {PLID: $PLID})
                ON CREATE SET
                  p.forename = $plForn,
                  p.surname = $plSurn
                WITH p
                MATCH (f:Fixture) 
                WHERE f.fxid = $fxid
                MATCH (t:Team)
                WHERE t.teamId = $teamId
                MERGE (t)<-[:PLAYED_FOR]-(p)-[:PLAYED_MATCH {shirtNumber: $shirtNumber,posId: $posId, mins:$mins}]->(f)
                """,
                PLID=PLID, plForn=plForn, plSurn=plSurn, fxid=fxid, 
                teamId=teamId, shirtNumber=shirtNumber, posId=posId,
                mins=mins
            )
```  
We can store the information about the players involvement in the match in the relationship `PLAYED_MATCH` properties.  

### Creating all the match events  
Every event in the Opta data can have multiple descriptors, each of which could be used as a node label. Luckily, APOC has a function that will do this for us - `apoc.create.addLabels(node, [labels])` In the following code, we firstly create each event and assign it multiple labels based on the Opta descriptors. We then use another APOC function to chain all the match events together in a linked list using `apoc.nodes.link(events, "NEXT_EVENT")`.  

```python  
#We can now load the individual match stats into the graph database

def load_individual_match_stats(match_data, driver, cursor):
    
    with driver.session() as session:
        tx = session.begin_transaction()
        
        params = {x[0]:None for x in cur.description}
        for row in match_data:
            for col, event in zip(row, params.keys()):
                params[event] = col
                
            tx.run(
                """
                MERGE (e:Event {eventId: $ID})
                ON CREATE SET
                  e.psTimestamp = $ps_timestamp,
                  e.psEndstamp = $ps_endstamp,
                  e.matchTime = $MatchTime,
                  e.period = $period,
                  e.xCoord = $x_coord,
                  e.yCoord = $y_coord,
                  e.xCoordEnd = $x_coord_end,
                  e.yCoordEnd = $y_coord_end,
                  e.metres = $Metres,
                  e.playNum = $PlayNum,
                  e.setNum = $SetNum,
                  e.sequenceId = $sequence_id
                WITH e, $actionDesc as actionDesc,
                     $actionTypeDesc as actionTypeDesc,
                     $actionResultDesc as actionResultDesc,
                     $qualifier3Desc as qualifier3Desc,
                     $qualifier4Desc as qualifier4Desc,
                     $qualifier5Desc as qualifier5Desc
                WITH e, 
                   [actionDesc, actionTypeDesc, actionResultDesc, qualifier3Desc,
                   qualifier4Desc, qualifier5Desc
                ] as node_labels
                CALL apoc.create.addLabels(e, node_labels)
                YIELD node
                WITH node as e
                MATCH (f:Fixture) WHERE f.fxid = $FXID
                MATCH (p:Player) WHERE p.PLID = $PLID
                MATCH (t:Team) WHERE t.teamId = $team_id
                MERGE (f)-[:HAS_EVENT]->(e)
                MERGE (p)-[:INDIVIDUAL_EVENT]->(e)
                MERGE (t)-[:FIXTURE_EVENT]->(e)
                """,
                params
            )
            
        # Link data into ordered match events
        tx.run(
            """
            MATCH (f:Fixture)-[:HAS_EVENT]->(e:Event) WHERE f.fxid = $FXID
            WITH e ORDER BY e.eventId
            WITH collect(e) AS events
            CALL apoc.nodes.link(events, "NEXT_EVENT")
            RETURN count(*)
            """,
            params
        )    
        
        tx.commit()
            
    return params
```

SuperScout stats return every individual event throughout a match and also every team event, therefore we will create some different relationships based on this. For every individual action, we will create a linked list of events so the whole game can be followed from start to finish based on every individual contribution. For every individual action, we will create a linked list on a **per team** basis, so we can look only at the actions for a team. Finally, for every team event, we will create a linked list on a **per team** basis so these events can also be followed and chained together. The code below imports the team events into the graph and creates the links between them in order of occurrence.  

```python  
#We can now load the team match stats into the graph database
def load_team_match_stats(team_match_data, driver, cursor):
    
    with driver.session() as session:
        tx = session.begin_transaction()
        
        params = {x[0]:None for x in cur.description}
        for row in team_match_data:
            for col, event in zip(row, params.keys()):
                params[event] = col
                
            tx.run(
                """
                MERGE (e:Event {eventId: $ID})
                ON CREATE SET
                  e.psTimestamp = $ps_timestamp,
                  e.psEndstamp = $ps_endstamp,
                  e.matchTime = $MatchTime,
                  e.period = $period,
                  e.xCoord = $x_coord,
                  e.yCoord = $y_coord,
                  e.xCoordEnd = $x_coord_end,
                  e.yCoordEnd = $y_coord_end,
                  e.metres = $Metres,
                  e.playNum = $PlayNum,
                  e.setNum = $SetNum,
                  e.sequenceId = $sequence_id
                WITH e, $actionDesc as actionDesc,
                     $actionTypeDesc as actionTypeDesc,
                     $actionResultDesc as actionResultDesc,
                     $qualifier3Desc as qualifier3Desc,
                     $qualifier4Desc as qualifier4Desc,
                     $qualifier5Desc as qualifier5Desc
                WITH e, 
                   [actionDesc, actionTypeDesc, actionResultDesc, qualifier3Desc,
                   qualifier4Desc, qualifier5Desc
                ] as node_labels
                CALL apoc.create.addLabels(e, node_labels)
                YIELD node
                WITH node as e
                MATCH (f:Fixture) WHERE f.fxid = $FXID
                MATCH (t:Team) WHERE t.teamId = $team_id
                MERGE (f)-[:HAS_EVENT]->(e)
                MERGE (t)-[:TEAM_EVENT]->(e)
                """,
                params
            )
            
        # Link data into ordered match events on per team basis
        tx.run(
            """
            MATCH (f:Fixture)<-[:PLAYED_IN]-(t:Team)-[:TEAM_EVENT]->(e:Event) WHERE f.fxid = $FXID
            WITH t, e ORDER BY t, e.eventId
            WITH t, collect(e) AS events
            CALL apoc.nodes.link(events, "NEXT_EVENT")
            RETURN count(*)
            """,
            params
        )    
        
        tx.commit()
            
    return params
```  

Finally, we can run a small Cypher command to chain together all the individual player events but on a per team basis.  

```sql  
MATCH (t:Team)-[:FIXTURE_EVENT]-(e:Event)
WITH t, e ORDER BY t, e.eventId
WITH t, collect(e) AS events
CALL apoc.nodes.link(events, "NEXT_EVENT_PER_TEAM")
RETURN count(*)
```  

Hopefully all of this will be a bit more clear when we get into querying the graph...

### Querying the data  
Let's start with a simple one. How many carries and tackles did each player make during the game?  

```sql  
MATCH (p:Player)-[rel:INDIVIDUAL_EVENT]->(e:Event) WHERE any(x in labels(e) WHERE x = 'Carry') 
MATCH (p)-[played:PLAYED_MATCH]->(f:Fixture)
RETURN 
  p.forename + " " + p.surname as playerName ,
  COUNT(*) as carries, 
  played.mins as minsPlayed, 
  round(toFloat(played.mins)/toFloat(COUNT(*)),2) as minsPerCarry 
ORDER BY carries DESC LIMIT 6  

+--------------------------------------------------------------+
| playerName             | carries | minsPlayed | minsPerCarry |
+--------------------------------------------------------------+
| "Josh Adams"           | 16      | 80         | 5.0          |
| "Sam Lewis"            | 15      | 80         | 5.33         |
| "Will Spencer"         | 13      | 80         | 6.15         |
| "Callum Chick"         | 13      | 66         | 5.08         |
| "Sonatane Takulua"     | 12      | 73         | 6.08         |
| "Mark Wilson"          | 10      | 80         | 8.0          |
+--------------------------------------------------------------+

```  

Now let's make use of how easily Neo4j can traverse relationships and look at the events leading up to a try. Fist we will look at all of the individual events taking into consideration both teams. Given we're looking at both, we will look for the 20 events leading up to a try. 

```sql  
MATCH p =(e1:Event)-[:NEXT_EVENT*20]->(e2:Try)
RETURN p LIMIT 1
```  
We can see how this looks in the screenshot below 
![](/images/try_data.png)  

We can also add the player nodes in but it starts to look a bit messy!  
![](/images/try_data_player.png)  

Let's see what the events leading up to a try look like.  
```sql
MATCH p =(e1:Event)-[:NEXT_EVENT*20]->(e2:Try)
WITH nodes(p) as events LIMIT 1
UNWIND events as event
MATCH (p:Player)-[:INDIVIDUAL_EVENT]->(event)
MATCH (p)-[:PLAYED_FOR]->(t:Team)
RETURN p.forename + " " + p.surname as playerName, t.name as teamName, labels(event) as eventLabels ORDER BY event.eventId

+----------------------------------------------------------------------------------------------------------------------------------------------------+
| playerName             | teamName    | eventLabels                                                                                                 |
+----------------------------------------------------------------------------------------------------------------------------------------------------+
| "Jack Singleton"       | "Worcester" | ["Event", "Carry", "Other Carry", "Crossed Gainline", "Tackled Neutral", "Neutral Contact"]                 |
| "Sonatane Takulua"     | "Newcastle" | ["Event", "Tackle", "Line Tackle", "Complete"]                                                              |
| "Alex Tait"            | "Newcastle" | ["Event", "Tackle", "Line Tackle", "Complete", "Tackle Assist"]                                             |
| "Jonny Arr"            | "Worcester" | ["Event", "Pass", "Complete Pass"]                                                                          |
| "Tom Heathcote"        | "Worcester" | ["Event", "Pass", "Complete Pass"]                                                                          |
| "Jackson Willison"     | "Worcester" | ["Event", "Carry", "Other Carry", "Tackled Neutral", "Failed Gainline", "Neutral Contact"]                  |
| "Callum Chick"         | "Newcastle" | ["Event", "Tackle", "Line Tackle", "Complete"]                                                              |
| "Jonny Arr"            | "Worcester" | ["Event", "Pass", "Complete Pass"]                                                                          |
| "Tom Heathcote"        | "Worcester" | ["Event", "Kick", "Kick In Play", "Pressure Error", "Bomb"]                                                 |
| "Belisario Agulla"     | "Newcastle" | ["Event", "Collection", "Fail", "Defensive Catch"]                                                          |
| "Josh Adams"           | "Worcester" | ["Event", "Collection", "Fail", "Attacking Catch"]                                                          |
| "Mark Wilson"          | "Newcastle" | ["Event", "Collection", "Success", "Defensive Loose Ball"]                                                  |
| "Mark Wilson"          | "Newcastle" | ["Event", "Penalty Conceded", "No Action", "Defence", "Full Penalty", "Offside", "Offside In General Play"] |
| "Tom Heathcote"        | "Worcester" | ["Event", "Kick", "Touch Kick", "Kick In Touch (Full)", "Penalty Kick"]                                     |
| "Jack Singleton"       | "Worcester" | ["Event", "Lineout Throw", "Won Clean", "Catch And Drive", "Throw Back"]                                    |
| "Gerrit-Jan van Velze" | "Worcester" | ["Event", "Won Clean", "Lineout Take", "Clean Catch", "Catch And Drive", "Lineout Win Back"]                |
| "Jonny Arr"            | "Worcester" | ["Event", "Pass", "Complete Pass"]                                                                          |
| "Tom Heathcote"        | "Worcester" | ["Event", "Pass", "Carry", "Other Carry", "Crossed Gainline"]                                               |
| "Tom Heathcote"        | "Worcester" | ["Event", "Pass", "Try Pass"]                                                                               |
| "Josh Adams"           | "Worcester" | ["Event", "Carry", "Other Carry", "Try Scored"]                                                             |
| "Josh Adams"           | "Worcester" | ["Event", "Try"]                                                                                            |
+----------------------------------------------------------------------------------------------------------------------------------------------------+
```  

Clearly, for every carry, you also get a tackle from the opposition, so can we tidy this up a bit and only look at this for one team? Luckily, the relationships we created earlier will allow us to do this.  

```sql  
MATCH p =(e1:Event)-[:NEXT_EVENT_PER_TEAM*20]->(e2:Try)
WITH nodes(p) as events LIMIT 1
UNWIND events as event
MATCH (p:Player)-[:INDIVIDUAL_EVENT]->(event)
MATCH (p)-[:PLAYED_FOR]->(t:Team)
RETURN p.forename + " " + p.surname as playerName, t.name as teamName, labels(event) as eventLabels ORDER BY event.eventId  

+-------------------------------------------------------------------------------------------------------------------------------------+
| playerName             | teamName    | eventLabels                                                                                  |
+-------------------------------------------------------------------------------------------------------------------------------------+
| "Sam Lewis"            | "Worcester" | ["Event", "Carry", "Other Carry", "Crossed Gainline", "Neutral Contact", "Off Load"]         |
| "Sam Lewis"            | "Worcester" | ["Event", "Pass", "Offload", "Own Player"]                                                   |
| "Donncha O'Callaghan"  | "Worcester" | ["Event", "Carry", "Tackled Neutral", "Neutral Contact", "Support Carry"]                    |
| "Jackson Willison"     | "Worcester" | ["Event", "Pass", "Complete Pass"]                                                           |
| "Jamie Shillcock"      | "Worcester" | ["Event", "Kick", "Kick In Touch (Full)", "Kick In Own 22", "Territorial"]                   |
| "Jack Singleton"       | "Worcester" | ["Event", "Collection", "Success", "Defensive Loose Ball"]                                   |
| "Jack Singleton"       | "Worcester" | ["Event", "Carry", "Other Carry", "Crossed Gainline", "Tackled Neutral", "Neutral Contact"]  |
| "Jonny Arr"            | "Worcester" | ["Event", "Pass", "Complete Pass"]                                                           |
| "Tom Heathcote"        | "Worcester" | ["Event", "Pass", "Complete Pass"]                                                           |
| "Jackson Willison"     | "Worcester" | ["Event", "Carry", "Other Carry", "Tackled Neutral", "Failed Gainline", "Neutral Contact"]   |
| "Jonny Arr"            | "Worcester" | ["Event", "Pass", "Complete Pass"]                                                           |
| "Tom Heathcote"        | "Worcester" | ["Event", "Kick", "Kick In Play", "Pressure Error", "Bomb"]                                  |
| "Josh Adams"           | "Worcester" | ["Event", "Collection", "Fail", "Attacking Catch"]                                           |
| "Tom Heathcote"        | "Worcester" | ["Event", "Kick", "Touch Kick", "Kick In Touch (Full)", "Penalty Kick"]                      |
| "Jack Singleton"       | "Worcester" | ["Event", "Lineout Throw", "Won Clean", "Catch And Drive", "Throw Back"]                     |
| "Gerrit-Jan van Velze" | "Worcester" | ["Event", "Won Clean", "Lineout Take", "Clean Catch", "Catch And Drive", "Lineout Win Back"] |
| "Jonny Arr"            | "Worcester" | ["Event", "Pass", "Complete Pass"]                                                           |
| "Tom Heathcote"        | "Worcester" | ["Event", "Pass", "Carry", "Other Carry", "Crossed Gainline"]                                |
| "Tom Heathcote"        | "Worcester" | ["Event", "Pass", "Try Pass"]                                                                |
| "Josh Adams"           | "Worcester" | ["Event", "Carry", "Other Carry", "Try Scored"]                                              |
| "Josh Adams"           | "Worcester" | ["Event", "Try"]                                                                             |
+-------------------------------------------------------------------------------------------------------------------------------------+
 
```  

This needs to be taken with a pinch of salt as the sequence of 20 events leading to a try doesn't look like a continuous series in this instance as we've got examples of "Kick in Touch". However it shows how powerful it can be to traverse relationships using Cypher. 


