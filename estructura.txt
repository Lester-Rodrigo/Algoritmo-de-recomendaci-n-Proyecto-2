FOR each user in dataset:
  CREATE node User(u.id)

FOR each game in dataset:
  CREATE node Game(g.id)

FOR each genre:
  CREATE node Genre(name)

FOR each interaction:
  CREATE relationship (user)-[:PLAYED {hours}] -> (Game)

FOR each liked game:
 CREATE relationship (user)-[:LIKED] -> (Game)

FOR each game in dataset:
  CONNECT (Game)-[:HAS_GENRE] -> (Genre)

FOR each pair of games (g1, g2):
    score = similarity(g1.genres, g2.genres)

    IF score > threshold:
        CREATE (g1)-[:SIMILAR_TO {score}]->(g2)


FUNCTION recommend_games(user_id):

    user_games = GET games played/liked by user

    candidate_games = EMPTY SET

    // 1. Collaborative filtering
    similar_users = FIND users connected via SIMILAR_USER

    FOR each similar_user:
        FOR each game played by similar_user:
            IF game NOT in user_games:
                ADD game to candidate_games

    // 2. Content-based expansion
    FOR each game in user_games:
        similar_games = GET games via SIMILAR_TO

        FOR each similar_game:
            IF not already played:
                ADD to candidate_games

    RETURN candidate_games

FUNCTION rank_games(user, candidate_games):

    FOR each game in candidate_games:

        score = 0

        // Collaborative weight
        score += (# of similar users who played it) * w1

        // Content similarity weight
        score += (similarity to user's liked games) * w2

        // Popularity (optional)
        score += log(total_players(game)) * w3

        // Personalization
        score += match(user.favorite_genres, game.genres) * w4

    SORT candidate_games by score DESC

    RETURN top N games

FUNCTION get_recommendations(user_id):
     candidates = recommend_games(user_id)

     ranked =rank_games(user_id, candidates)

     RETURN top 10 ranked 

