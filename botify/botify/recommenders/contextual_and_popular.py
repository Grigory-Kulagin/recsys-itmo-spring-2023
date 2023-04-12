from .toppop import TopPop
from .recommender import Recommender
import random
from collections import OrderedDict, defaultdict


class ContextualAndPopular(Recommender):
    """
    Recommend tracks closest to the previous one.
    Fall back to the TopPop recommender if no
    recommendations found for the track.
    """

    def __init__(self, tracks_redis, catalog, popular_tracks):
        self.tracks_redis = tracks_redis
        self.catalog = catalog
        self.fallback = TopPop(tracks_redis, popular_tracks)

    def recommend_next(self, user: int, prev_track: int, prev_track_time: float) -> int:
        previous_track = self.tracks_redis.get(prev_track)

        if previous_track is None:
            return self.fallback.recommend_next(user, prev_track, prev_track_time)

        previous_track = self.catalog.from_bytes(previous_track)

        if prev_track_time < 0.1:
            anti_recommendations = previous_track.recommendations
            for i in range(10):
                next_track = self.fallback.recommend_next(user, prev_track, prev_track_time)
                if next_track not in anti_recommendations:
                    break
            return next_track

        if prev_track_time < 0.3:
            return self.fallback.recommend_next(user, prev_track, prev_track_time)

        recommendations = previous_track.recommendations

        if not recommendations:
            return self.fallback.recommend_next(user, prev_track, prev_track_time)

        shuffled = list(recommendations)
        random.shuffle(shuffled)
        return shuffled[0]
