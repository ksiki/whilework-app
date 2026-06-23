import logging


class SuppressUnauthorizedVacancyViewFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        if "Unauthorized: /api/user/add-viewed-vacancy/" in message:
            return False
        if "Forbidden: /api/user/add-viewed-vacancy/" in message:
            return False
        return True
