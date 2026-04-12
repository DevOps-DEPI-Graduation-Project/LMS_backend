from django.urls import path
from .views import (
    CourseQuizListCreateView,
    QuizListView,
    QuizCreateView,
    QuizDetailView,
    QuizUpdateView,
    QuizDeleteView,
    QuizSubmitView,
    QuizMyResultsView,
    QuestionListView,
    QuestionCreateView,
    QuestionDetailView,
    QuestionUpdateView,
    QuestionDeleteView,
    ChoiceListView,
    ChoiceCreateView,
    ChoiceDetailView,
    ChoiceUpdateView,
    ChoiceDeleteView,
    AttemptListView,
    AttemptDetailView,
)

urlpatterns = [
    # Course quizzes
    path('courses/<slug:course_slug>/quizzes/', CourseQuizListCreateView.as_view(), name='course-quizzes'),

    # General quizzes
    path('quizzes/', QuizListView.as_view(), name='quiz-list'),
    path('quizzes/create/', QuizCreateView.as_view(), name='quiz-create'),
    path('quizzes/<slug:slug>/', QuizDetailView.as_view(), name='quiz-detail'),
    path('quizzes/<slug:slug>/update/', QuizUpdateView.as_view(), name='quiz-update'),
    path('quizzes/<slug:slug>/delete/', QuizDeleteView.as_view(), name='quiz-delete'),
    path('quizzes/<slug:slug>/submit/', QuizSubmitView.as_view(), name='quiz-submit'),
    path('quizzes/<slug:slug>/my-results/', QuizMyResultsView.as_view(), name='quiz-my-results'),

    # Questions
    path('quizzes/<slug:quiz_slug>/questions/', QuestionListView.as_view(), name='question-list'),
    path('quizzes/<slug:quiz_slug>/questions/create/', QuestionCreateView.as_view(), name='question-create'),
    path('quizzes/<slug:quiz_slug>/questions/<slug:slug>/', QuestionDetailView.as_view(), name='question-detail'),
    path('quizzes/<slug:quiz_slug>/questions/<slug:slug>/update/', QuestionUpdateView.as_view(), name='question-update'),
    path('quizzes/<slug:quiz_slug>/questions/<slug:slug>/delete/', QuestionDeleteView.as_view(), name='question-delete'),

    # Choices
    path('quizzes/<slug:quiz_slug>/questions/<slug:question_slug>/choices/', ChoiceListView.as_view(), name='choice-list'),
    path('quizzes/<slug:quiz_slug>/questions/<slug:question_slug>/choices/create/', ChoiceCreateView.as_view(), name='choice-create'),
    path('quizzes/<slug:quiz_slug>/questions/<slug:question_slug>/choices/<slug:slug>/', ChoiceDetailView.as_view(), name='choice-detail'),
    path('quizzes/<slug:quiz_slug>/questions/<slug:question_slug>/choices/<slug:slug>/update/', ChoiceUpdateView.as_view(), name='choice-update'),
    path('quizzes/<slug:quiz_slug>/questions/<slug:question_slug>/choices/<slug:slug>/delete/', ChoiceDeleteView.as_view(), name='choice-delete'),

    # Attempts
    path('attempts/', AttemptListView.as_view(), name='attempt-list'),
    path('attempts/<slug:slug>/', AttemptDetailView.as_view(), name='attempt-detail'),
    path('quizzes/<slug:quiz_slug>/attempts/', AttemptListView.as_view(), name='quiz-attempt-list'),
]
# DELETE /api/quizzes/{slug}/questions/{slug}/choices/{slug}/      — Delete choice
#
# GET    /api/attempts/                                            — All attempts (instructor/admin)
# GET    /api/attempts/?quiz_slug={slug}                           — Filter by quiz