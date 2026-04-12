from rest_framework import serializers
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Quiz, Question, Choice, Attempt, StudentAnswer
from notifications.models import Notification
from cources.models import Course


# =================== Choice Serializer (Instructor) ===================
class ChoiceSerializer(serializers.ModelSerializer):
    """Full choice data including correct answer — for instructors and admins only"""

    choice_name = serializers.CharField(source='text_choice')

    class Meta:
        model = Choice
        fields = ['slug', 'choice_name', 'is_correct']


# =================== Choice Serializer (Student) ===================
class ChoiceStudentSerializer(serializers.ModelSerializer):
    """Hides is_correct from students to prevent cheating"""

    choice_name = serializers.CharField(source='text_choice')

    class Meta:
        model = Choice
        fields = ['slug', 'choice_name']


# =================== Choice Create Serializer ===================
class ChoiceCreateSerializer(serializers.ModelSerializer):
    """
    Used by instructors to add or update choices.
    Automatically handles single-choice questions to keep only one correct answer.
    """

    choice_name = serializers.CharField(source='text_choice')

    class Meta:
        model = Choice
        fields = ['slug', 'choice_name', 'is_correct']
        read_only_fields = ['slug']

    def validate(self, data):
        """
        If the question is single-choice, unset any other correct answer before saving.
        """
        question = self.context.get('question')
        if data.get('is_correct') and question and question.question_type == 'single':
            existing = Choice.objects.filter(
                question=question, is_correct=True
            )
            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)
            existing.update(is_correct=False)
        return data


# =================== Question Serializer (Instructor) ===================
class QuestionSerializer(serializers.ModelSerializer):
    """Full question data with correct answers — for instructors and admins only"""

    question_name = serializers.CharField(source='q_name')
    choices = ChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['slug', 'question_name', 'mark', 'question_type', 'choices']


# =================== Question Serializer (Student) ===================
class QuestionStudentSerializer(serializers.ModelSerializer):
    """Question data with hidden correct answers — safe to expose to students"""

    question_name = serializers.CharField(source='q_name')
    choices = ChoiceStudentSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['slug', 'question_name', 'question_type', 'choices']


# =================== Question Create Serializer ===================
class QuestionCreateSerializer(serializers.ModelSerializer):
    """Used by instructors to add or update questions in a quiz"""

    question_name = serializers.CharField(source='q_name')
    question_type = serializers.ChoiceField(choices=Question.QUESTION_TYPE_CHOICES, default='single')

    class Meta:
        model = Question
        fields = ['slug', 'question_name', 'mark', 'question_type']
        read_only_fields = ['slug']


# =================== Nested choice input for course quiz creation
class NestedChoiceCreateSerializer(serializers.Serializer):
    choice_name = serializers.CharField()
    isCorrect = serializers.BooleanField()


class NestedQuestionCreateSerializer(serializers.Serializer):
    question_name = serializers.CharField()
    mark = serializers.IntegerField(min_value=1)
    question_type = serializers.ChoiceField(choices=Question.QUESTION_TYPE_CHOICES, default='single')
    choices = NestedChoiceCreateSerializer(many=True)

    def validate(self, data):
        choices = data.get('choices', [])
        if len(choices) < 2:
            raise serializers.ValidationError("Each question must include at least two choices.")

        correct_count = sum(choice['isCorrect'] for choice in choices)
        if data['question_type'] == 'single' and correct_count != 1:
            raise serializers.ValidationError(
                "Single-choice questions must have exactly one correct choice."
            )
        if data['question_type'] == 'multiple' and correct_count < 1:
            raise serializers.ValidationError(
                "Multiple-choice questions must have at least one correct choice."
            )
        return data


class CourseQuizCreateSerializer(serializers.Serializer):
    quiz_name = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    max_attempts = serializers.IntegerField(min_value=1, default=1)
    questions = NestedQuestionCreateSerializer(many=True)
    course_slug = serializers.SlugField(required=False, write_only=True)

    def validate(self, data):
        course = self.context.get('course')
        if data.get('course_slug') and course and data['course_slug'] != course.slug:
            raise serializers.ValidationError({
                'course_slug': 'course_slug in body must match the URL course slug.'
            })
        return data

    def create(self, validated_data):
        course = self.context['course']
        question_list = validated_data.pop('questions', [])
        total_mark = sum(question_data['mark'] for question_data in question_list)

        quiz = Quiz.objects.create(
            course=course,
            quiz_name=validated_data.get('quiz_name'),
            description=validated_data.get('description', ''),
            max_attempts=validated_data.get('max_attempts', 1),
            total_mark=total_mark
        )

        for question_data in question_list:
            choices_data = question_data.pop('choices')
            question = Question.objects.create(
                quiz=quiz,
                q_name=question_data['question_name'],
                mark=question_data['mark'],
                question_type=question_data['question_type']
            )

            for choice_data in choices_data:
                Choice.objects.create(
                    question=question,
                    text_choice=choice_data['choice_name'],
                    is_correct=choice_data['isCorrect']
                )

        return quiz


# =================== Quiz List Serializer ===================
class QuizListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing quizzes without loading questions"""

    course_name = serializers.ReadOnlyField(source='course.title')
    quiz_status = serializers.SerializerMethodField()
    attempts_used = serializers.SerializerMethodField()
    best_score = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = ['slug', 'quiz_name', 'total_mark', 'max_attempts',
                  'course_name', 'attempts_used', 'best_score', 'quiz_status']

    def _get_attempts(self, obj):
        """Cache attempts per request to avoid repeated queries"""
        request = self.context.get('request')
        if not request:
            return Attempt.objects.none()
        return Attempt.objects.filter(student=request.user, quiz=obj)

    def get_attempts_used(self, obj):
        # Use annotated value if available (avoids N+1)
        if hasattr(obj, 'attempts_count'):
            return obj.attempts_count
        return self._get_attempts(obj).count()

    def get_best_score(self, obj):
        # Use annotated value if available (avoids N+1)
        if hasattr(obj, 'best_score_value'):
            return obj.best_score_value or 0
        from django.db.models import Max
        result = self._get_attempts(obj).aggregate(best=Max('score'))
        return result['best'] or 0

    def get_quiz_status(self, obj):
        """
        Returns the student's status for this quiz:
        - not_started: no attempts yet
        - passed: has a passed attempt
        - failed: all attempts used and none passed
        - can_retry: has failed attempts but retries remaining
        """
        # Use annotated values if available (avoids N+1)
        if hasattr(obj, 'attempts_count'):
            count = obj.attempts_count
            passed = getattr(obj, 'passed_count', 0)
        else:
            attempts = self._get_attempts(obj)
            count = attempts.count()
            passed = attempts.filter(status='passed').count()

        if count == 0:
            return 'not_started'
        if passed > 0:
            return 'passed'
        if count >= obj.max_attempts:
            return 'failed'
        return 'can_retry' 


# =================== Quiz Create/Update Serializer ===================
class QuizCreateSerializer(serializers.ModelSerializer):
    """Used by instructors to create or update a quiz"""

    course = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Course.objects.all()
    )

    class Meta:
        model = Quiz
        fields = ['slug', 'quiz_name', 'description', 'max_attempts', 'course', 'total_mark']
        read_only_fields = ['slug', 'total_mark']


# =================== Quiz Detail Serializer (Instructor) ===================
class QuizDetailInstructorSerializer(serializers.ModelSerializer):
    """Full quiz detail including questions and correct answers — instructors and admins only"""

    questions = QuestionSerializer(many=True, read_only=True)
    course_name = serializers.ReadOnlyField(source='course.title')

    class Meta:
        model = Quiz
        fields = ['slug', 'quiz_name', 'description', 'total_mark',
                  'max_attempts', 'course_name', 'questions']


# =================== Quiz Detail Serializer (Student) ===================
class QuizDetailStudentSerializer(serializers.ModelSerializer):
    """Quiz detail with hidden correct answers and attempt tracking — safe for students"""

    questions = QuestionStudentSerializer(many=True, read_only=True)
    course_name = serializers.ReadOnlyField(source='course.title')
    attempts_used = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = ['slug', 'quiz_name', 'description', 'total_mark',
                  'max_attempts', 'course_name', 'attempts_used', 'questions']

    def get_attempts_used(self, obj):
        """Returns how many attempts the current student has already used for this quiz"""
        user = self.context['request'].user
        return Attempt.objects.filter(student=user, quiz=obj).count()


# =================== Streak Helper ===================
def _check_and_notify_streak(user):
    """
    Checks if the student has made at least one attempt on 7 consecutive days.
    Triggered after every quiz submission.
    Sends a streak notification only once per day.
    """
    from django.utils import timezone
    from datetime import timedelta

    today = timezone.now().date()

    # Get last 7 distinct days the student made a serious attempt (score > 0)
    recent_days = list(
        Attempt.objects.filter(student=user, score__gt=0)
        .values_list('attempt_date__date', flat=True)
        .distinct()
        .order_by('-attempt_date__date')[:7]
    )

    # Must have exactly 7 distinct days
    if len(recent_days) < 7:
        return

    # Check if the 7 days are consecutive
    for i in range(6):
        if recent_days[i] - recent_days[i + 1] != timedelta(days=1):
            return

    # Avoid sending streak notification more than once per day
    already_sent = Notification.objects.filter(
        user=user,
        notification_type='streak',
        created_at__date=today
    ).exists()

    if not already_sent:
        Notification.objects.create(
            user=user,
            title="7-Day Streak Achieved!",
            body="Congratulations! You have completed your 7-day learning streak. Keep it up!",
            notification_type='streak'
        )


# =================== Student Answer Input ===================
class StudentAnswerInputSerializer(serializers.Serializer):
    """Represents a single answer submitted by a student"""

    question_slug = serializers.SlugField()
    choice_slug = serializers.SlugField()


# =================== Submit Attempt Serializer ===================
class SubmitAttemptSerializer(serializers.Serializer):
    """
    Handles the full quiz submission flow:
    - Enforces max attempts limit
    - Blocks concurrent pending attempts (prevents multi-tab cheating)
    - Validates all answers before writing to the DB
    - Calculates score and saves pass/fail status
    - Sends a quiz result notification to the student
    """

    answers = StudentAnswerInputSerializer(many=True)

    def validate_answers(self, answers):
        if not answers:
            raise serializers.ValidationError("Answers list cannot be empty.")

        question_slugs = [ans['question_slug'] for ans in answers]
        if len(question_slugs) != len(set(question_slugs)):
            raise serializers.ValidationError(
                "Duplicate questions detected. Each question must be answered once."
            )

        return answers

    def create(self, validated_data):
        user = self.context['request'].user
        quiz = self.context['quiz']

        # Step 1: Enforce max attempts limit
        attempts_used = Attempt.objects.filter(student=user, quiz=quiz).count()
        if attempts_used >= quiz.max_attempts:
            raise serializers.ValidationError(
                f"You have reached the maximum number of attempts ({quiz.max_attempts})."
            )

        # Step 2: Block concurrent submissions
        if Attempt.objects.filter(student=user, quiz=quiz, status='pending').exists():
            raise serializers.ValidationError(
                "You already have a pending attempt for this quiz. "
                "Please wait for it to be finalized before starting a new one."
            )

        # Step 3: Validate answer count matches quiz question count
        question_count = quiz.questions.count()
        submitted_count = len(validated_data['answers'])
        if submitted_count != question_count:
            raise serializers.ValidationError(
                f"You must answer all {question_count} questions. "
                f"You submitted {submitted_count}."
            )

        # Step 4: Resolve all slugs to DB objects before writing anything
        resolved_answers = []
        for ans in validated_data['answers']:
            question = get_object_or_404(Question, slug=ans['question_slug'], quiz=quiz)
            choice = get_object_or_404(Choice, slug=ans['choice_slug'], question=question)
            resolved_answers.append((question, choice))

        # Step 5: All validations passed — write to DB atomically
        with transaction.atomic():
            attempt = Attempt.objects.create(student=user, quiz=quiz)

            total_score = 0
            student_answers = []

            for question, choice in resolved_answers:
                student_answers.append(
                    StudentAnswer(
                        attempt=attempt,
                        question=question,
                        selected_choice=choice
                    )
                )
                if choice.is_correct:
                    total_score += question.mark

            StudentAnswer.objects.bulk_create(student_answers)

            attempt.score = total_score
            attempt.save(update_fields=['score'])
            attempt.calculate_status()

            # Notify the student with their result immediately after submission
            Notification.objects.create(
                user=user,
                title=f"Quiz Result: {quiz.quiz_name}",
                body=f"Your score: {attempt.score}/{quiz.total_mark}. Status: {attempt.status}.",
                notification_type='quiz_result'
            )

            # Check for 7-day streak
            _check_and_notify_streak(user)

        return attempt


# =================== Attempt Result Serializer ===================
class AttemptResultSerializer(serializers.ModelSerializer):
    """Returns the full result of a single attempt including per-answer breakdown"""

    quiz_name = serializers.ReadOnlyField(source='quiz.quiz_name')
    total_mark = serializers.ReadOnlyField(source='quiz.total_mark')
    answers = serializers.SerializerMethodField()

    class Meta:
        model = Attempt
        fields = ['quiz_name', 'total_mark', 'score', 'status',
                  'attempt_number', 'attempt_date', 'answers']

    def get_answers(self, obj):
        """Returns per-question breakdown showing what the student picked and whether it was correct"""
        return [
            {
                "question": answer.question.q_name,
                "selected": answer.selected_choice.text_choice,
                "is_correct": answer.selected_choice.is_correct,
            }
            for answer in obj.answers.select_related('question', 'selected_choice').all()
        ]


# =================== Attempt List Serializer (Instructor/Admin) ===================
class AttemptListSerializer(serializers.ModelSerializer):
    """Summary view of all student attempts — for instructors and admins to monitor results"""

    student_email = serializers.ReadOnlyField(source='student.email')
    quiz_name = serializers.ReadOnlyField(source='quiz.quiz_name')
    total_mark = serializers.ReadOnlyField(source='quiz.total_mark')

    class Meta:
        model = Attempt
        fields = ['student_email', 'quiz_name', 'total_mark',
                  'score', 'status', 'attempt_number', 'attempt_date']