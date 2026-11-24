POINTS_BY_POSITION = [10, 6, 3, 1]  # positions beyond get 0


class GrandPrix:
    """Course order and accumulated points of a grand prix."""

    def __init__(self, course_names, kart_names, player_kart_name):
        self.course_names = course_names
        self.player_kart_name = player_kart_name
        self.race_index = 0
        self.points = {name: 0 for name in kart_names}
        self.last_race_points = {name: 0 for name in kart_names}


    @property
    def current_course_name(self):
        return self.course_names[self.race_index]


    @property
    def is_last_race(self):
        return self.race_index == len(self.course_names) - 1


    def add_race_results(self, ranking):
        # ranking: kart names, winner first
        for position, kart_name in enumerate(ranking):
            points = POINTS_BY_POSITION[position] if position < len(POINTS_BY_POSITION) else 0
            self.last_race_points[kart_name] = points
            self.points[kart_name] += points


    def next_race(self):
        self.race_index += 1


    def overall_ranking(self):
        return sorted(self.points, key=lambda kart_name: self.points[kart_name], reverse=True)