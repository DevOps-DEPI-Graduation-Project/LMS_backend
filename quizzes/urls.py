from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers
from .views import QuizViewSet, QuestionViewSet, ChoiceViewSet, AttemptViewSet

# Main router
router = DefaultRouter()
router.register(r'quizzes', QuizViewSet, basename='quiz')
router.register(r'attempts', AttemptViewSet, basename='attempt')

# Nested: /api/quizzes/{quiz_slug}/questions/
quiz_router = nested_routers.NestedDefaultRouter(router, r'quizzes', lookup='quiz')
quiz_router.register(r'questions', QuestionViewSet, basename='quiz-questions')

# Nested: /api/quizzes/{quiz_slug}/questions/{question_slug}/choices/
question_router = nested_routers.NestedDefaultRouter(quiz_router, r'questions', lookup='question')
question_router.register(r'choices', ChoiceViewSet, basename='question-choices')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(quiz_router.urls)),
    path('', include(question_router.urls)),
]

# ===================== Endpoints =====================
# GET    /api/quizzes/                                              — List quizzes
# POST   /api/quizzes/                                             — Create quiz (instructor/admin)
# GET    /api/quizzes/{slug}/                                       — Detail
# PATCH  /api/quizzes/{slug}/                                       — Update quiz
# DELETE /api/quizzes/{slug}/                                       — Delete quiz
# POST   /api/quizzes/{slug}/submit/                               — Submit attempt (student)
# GET    /api/quizzes/{slug}/my-results/                           — My results (student)
#
# GET    /api/quizzes/{slug}/questions/                            — List questions
# POST   /api/quizzes/{slug}/questions/                            — Add question (instructor/admin)
# GET    /api/quizzes/{slug}/questions/{slug}/                     — Question detail
# PATCH  /api/quizzes/{slug}/questions/{slug}/                     — Update question
# DELETE /api/quizzes/{slug}/questions/{slug}/                     — Delete question
#
# GET    /api/quizzes/{slug}/questions/{slug}/choices/             — List choices
# POST   /api/quizzes/{slug}/questions/{slug}/choices/             — Add choice (instructor/admin)
# GET    /api/quizzes/{slug}/questions/{slug}/choices/{slug}/      — Choice detail
# PATCH  /api/quizzes/{slug}/questions/{slug}/choices/{slug}/      — Update choice
# DELETE /api/quizzes/{slug}/questions/{slug}/choices/{slug}/      — Delete choice
#
# GET    /api/attempts/                                            — All attempts (instructor/admin)
# GET    /api/attempts/?quiz_slug={slug}                           — Filter by quiz