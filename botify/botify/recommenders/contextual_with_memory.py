from .toppop import TopPop
from .recommender import Recommender
import random
from collections import OrderedDict, defaultdict


class ContextualWithMemory(Recommender):
    """
    Recommend tracks closest to the previous one.
    Fall back to the random recommender if no
    recommendations found for the track.
    """

    def __init__(self, tracks_redis, catalog, popular_tracks, max_memory_size: int = 10_000):
        self.tracks_redis = tracks_redis
        self.catalog = catalog
        self.max_memory_size = max_memory_size
        self.top_tracks = OrderedDict()
        self.listened_tracks = defaultdict(set)
        self.fallback = TopPop(tracks_redis, popular_tracks)

    def recommend_next(self, user: int, prev_track: int, prev_track_time: float) -> int:
        self.listened_tracks[user].add(prev_track)
        recommendations = []
        previous_track = self.tracks_redis.get(prev_track)

        if (prev_track_time > 0.9) and (previous_track is not None):
            good_prev_track = prev_track
            self.top_tracks[user] = good_prev_track
            if len(self.top_tracks) > self.max_memory_size:
                self.top_tracks.popitem(False)
        else:
            good_prev_track = self.top_tracks.get(user)

        if good_prev_track is not None:
            good_previous_track = self.tracks_redis.get(good_prev_track)
            good_previous_track = self.catalog.from_bytes(good_previous_track)
            recommendations = good_previous_track.recommendations

        if recommendations:
            shuffled = list(recommendations)
            random.shuffle(shuffled)

            for i in range(100):
                if shuffled[i] not in self.listened_tracks[user]:
                    break
            return shuffled[i]

        for i in range(100):
            recommendation = self.fallback.recommend_next(user, prev_track, prev_track_time)
            if recommendation not in self.listened_tracks[user]:
                return recommendation
        return recommendation
