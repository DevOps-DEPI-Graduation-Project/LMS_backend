from .quiz_views import (
    CourseQuizListCreateView,
    QuizListView,
    QuizCreateView,
    QuizDetailView,
    QuizUpdateView,
    QuizDeleteView,
    QuizSubmitView,
    QuizMyResultsView,
)
from .question_views import (
    QuestionListView,
    QuestionCreateView,
    QuestionDetailView,
    QuestionUpdateView,
    QuestionDeleteView,
)
from .choice_views import (
    ChoiceListView,
    ChoiceCreateView,
    ChoiceDetailView,
    ChoiceUpdateView,
    ChoiceDeleteView,
)
from .attempt_views import (
    AttemptListView,
    AttemptDetailView,
)

__all__ = [
    'CourseQuizListCreateView',
    'QuizListView',
    'QuizCreateView',
    'QuizDetailView',
    'QuizUpdateView',
    'QuizDeleteView',
    'QuizSubmitView',
    'QuizMyResultsView',
    'QuestionListView',
    'QuestionCreateView',
    'QuestionDetailView',
    'QuestionUpdateView',
    'QuestionDeleteView',
    'ChoiceListView',
    'ChoiceCreateView',
    'ChoiceDetailView',
    'ChoiceUpdateView',
    'ChoiceDeleteView',
    'AttemptListView',
    'AttemptDetailView',
]