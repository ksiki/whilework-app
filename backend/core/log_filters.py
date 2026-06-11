import logging


class SuppressUnauthorizedVacancyViewFilter(logging.Filter):
    def filter(self, record):
        if "Unauthorized: /api/user/add-viewed-vacancy/" in record.getMessage():
            return False
        return True
