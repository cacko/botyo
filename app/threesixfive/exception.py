class OnTvError(Exception):
    pass


class GameNotFound(OnTvError):
    pass


class TeamNotFound(OnTvError):
    pass


class PlayerNotFound(OnTvError):
    pass


class CompetitionNotFound(OnTvError):
    pass
