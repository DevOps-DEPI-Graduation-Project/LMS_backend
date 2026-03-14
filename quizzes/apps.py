from django.apps import AppConfig


class QuizzesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'quizzes'

    def ready(self):
        import quizzes.signals  # noqa: F401 — registers all quiz signals on app startup