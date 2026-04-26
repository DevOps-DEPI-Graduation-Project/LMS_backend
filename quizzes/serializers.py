import uuid
from rest_framework import serializers
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Quiz, Question, Choice, Attempt, StudentAnswer
from notifications.models import Notification
from cources.models import Course

# =================== Choice Serializer (Instructor) ===================
class ChoiceSerializer(serializers.ModelSerializer):
    """Full choice data including is_correct — for instructors and admins only"""
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
    Used by instructors to add or update a single choice via the /choices/ endpoint.
    Single-choice questions:
        Auto-unsets the previous correct choice when a new correct one is set.
        This avoids raising a ValidationError while still enforcing the single-correct rule.

    Multiple-choice questions:
        Multiple correct choices are freely allowed — no auto-unset logic applied.
    """
    choice_name = serializers.CharField(source='text_choice')
    class Meta:
        model = Choice
        fields = ['slug', 'choice_name', 'is_correct']
        read_only_fields = ['slug']
    def validate(self, data):
        question = self.context.get('question')
        is_correct = data.get('is_correct', False)

        if is_correct and question and question.question_type == 'single':
            existing_correct = Choice.objects.filter(
                question=question, is_correct=True
            )
            if self.instance:
                existing_correct = existing_correct.exclude(pk=self.instance.pk)
            existing_correct.update(is_correct=False)
        return data
# =================== Question Serializer (Instructor) ===================
class QuestionSerializer(serializers.ModelSerializer):
    """Full question data with correct answers visible — instructors and admins only"""
    question_name = serializers.CharField(source='q_name')
    choices = ChoiceSerializer(many=True, read_only=True)
    class Meta:
        model = Question
        fields = ['slug', 'question_name', 'mark', 'question_type', 'choices']
# =================== Question Serializer (Student) ===================
class QuestionStudentSerializer(serializers.ModelSerializer):
    """Question data without correct answer flags — safe to expose to students"""
    question_name = serializers.CharField(source='q_name')
    choices = ChoiceStudentSerializer(many=True, read_only=True)
    class Meta:
        model = Question
        fields = ['slug', 'question_name', 'question_type', 'choices']
# =================== Question Create Serializer (Standalone) ===================
class QuestionCreateSerializer(serializers.ModelSerializer):
    """
    Used by instructors to add or update a standalone question
    via the /questions/ endpoint. Does not include nested choices.
    For full nested creation use CourseQuizCreateSerializer instead.
    """
    question_name = serializers.CharField(source='q_name')
    class Meta:
        model = Question
        fields = ['slug', 'question_name', 'mark', 'question_type']
        read_only_fields = ['slug']

# =================== Nested Serializers for Quiz Create/Update ===================
class NestedChoiceSerializer(serializers.Serializer):
    """
    Used inside NestedQuestionSerializer during quiz creation/update.
    Accepts `id` to identify existing choices for orphan-removal updates.
    """
    id = serializers.IntegerField(required=False)
    choice_name = serializers.CharField()
    isCorrect = serializers.BooleanField()
class NestedQuestionSerializer(serializers.Serializer):
    """
    Used inside CourseQuizCreateSerializer during quiz creation/update.
    Accepts `id` to identify existing questions for orphan-removal updates.
    Validation:
    - At least 2 choices per question.
    - single: exactly 1 correct choice.
    - multiple: at least 1 correct choice.
    """
    id = serializers.IntegerField(required=False)
    question_name = serializers.CharField()
    mark = serializers.IntegerField(min_value=1)
    question_type = serializers.ChoiceField(
        choices=Question.QUESTION_TYPE_CHOICES,
        default='single'
    )
    choices = NestedChoiceSerializer(many=True)
    def validate(self, data):
        choices = data.get('choices', [])

        if len(choices) < 2:
            raise serializers.ValidationError(
                f"Question '{data.get('question_name')}' must have at least 2 choices."
            )
        correct_count = sum(1 for c in choices if c.get('isCorrect', False))
        q_type = data.get('question_type', 'single')

        if q_type == 'single' and correct_count != 1:
            raise serializers.ValidationError(
                f"Single-choice question '{data.get('question_name')}' "
                f"must have exactly 1 correct answer. Got {correct_count}."
            )
        if q_type == 'multiple' and correct_count < 1:
            raise serializers.ValidationError(
                f"Multiple-choice question '{data.get('question_name')}' "
                f"must have at least 1 correct answer."
            )
        return data
# =================== Course Quiz Create/Update Serializer ===================
class CourseQuizCreateSerializer(serializers.Serializer):
    """
    Handles full nested creation and intelligent orphan-removal update of a Quiz.

    CREATE:
        Accepts one payload (quiz + questions + choices).
        Wrapped in transaction.atomic() for data integrity.
        total_mark calculated from question marks — NOT triggered via signal
        (uses Quiz.objects.filter().update() to avoid re-firing post_save).

    UPDATE (PUT / PATCH):
        - Pass `id` on an existing question/choice → update it in place.
        - Omit `id` → treated as new, will be created.
        - Remove entirely from payload → deleted (orphan removal).
        total_mark recalculated after all changes.

    `course` is resolved from the URL by the view and injected via context.
    It is NOT accepted in the request body.
    """
    quiz_name = serializers.CharField(required=False)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    max_attempts = serializers.IntegerField(required=False, min_value=1)
    questions = NestedQuestionSerializer(many=True, required=False)

    # ── Internal helpers ────────────────────────────────────────────────────────
    def _bulk_create_choices(self, question, choices_data):
        """Bulk-inserts choices for a newly created question."""
        Choice.objects.bulk_create([
            Choice(
                question=question,
                text_choice=c['choice_name'],
                is_correct=c['isCorrect'],
                slug=f"c-{uuid.uuid4().hex[:12]}"
            )
            for c in choices_data
        ])
    def _create_questions(self, quiz, question_list):
        """
        Creates all questions and their choices for a new quiz.
        Returns the total mark so we can set it in one .update() call.
        """
        total_mark = 0
        for q_data in question_list:
            choices_data = q_data.pop('choices', [])
            question = Question.objects.create(
                quiz=quiz,
                q_name=q_data['question_name'],
                mark=q_data['mark'],
                question_type=q_data.get('question_type', 'single'),
                slug=f"q-{uuid.uuid4().hex[:12]}"
            )
            self._bulk_create_choices(question, choices_data)
            total_mark += question.mark
        return total_mark
    def _update_choices(self, question, choices_data):
        """
        Orphan-removal update for choices under one question:
        - Update existing if `id` supplied.
        - Create new if no `id`.
        - Delete choices not present in the payload.
        """
        incoming_ids = {c['id'] for c in choices_data if 'id' in c}
        question.choices.exclude(pk__in=incoming_ids).delete()
        for c_data in choices_data:
            choice_id = c_data.pop('id', None)
            fields = {
                'text_choice': c_data['choice_name'],
                'is_correct': c_data['isCorrect'],
            }
            if choice_id:
                Choice.objects.filter(pk=choice_id, question=question).update(**fields)
            else:
                Choice.objects.create(
                    question=question,
                    slug=f"c-{uuid.uuid4().hex[:12]}",
                    **fields
                )
    def _update_questions(self, quiz, question_list):
        """
        Orphan-removal update for questions:
        - Update existing if `id` supplied.
        - Create new if no `id`.
        - Delete questions (and their choices) not present in the payload.
        Returns recalculated total mark.
        """
        incoming_ids = {q['id'] for q in question_list if 'id' in q}
        quiz.questions.exclude(pk__in=incoming_ids).delete()
        total_mark = 0
        for q_data in question_list:
            choices_data = q_data.pop('choices', [])
            question_id = q_data.pop('id', None)
            fields = {
                'q_name': q_data['question_name'],
                'mark': q_data['mark'],
                'question_type': q_data.get('question_type', 'single'),
            }
            if question_id:
                Question.objects.filter(pk=question_id, quiz=quiz).update(**fields)
                question = Question.objects.get(pk=question_id)
            else:
                question = Question.objects.create(
                    quiz=quiz,
                    slug=f"q-{uuid.uuid4().hex[:12]}",
                    **fields
                )
            self._update_choices(question, choices_data)
            total_mark += q_data['mark']
        return total_mark
    # ── Create ──────────────────────────────────────────────────────────────────
    def create(self, validated_data):
        course = self.context['course']  # Injected by view — not from request body
        question_list = validated_data.pop('questions', [])
        with transaction.atomic():
            quiz = Quiz.objects.create(
                course=course,
                quiz_name=validated_data.get('quiz_name'),
                description=validated_data.get('description', ''),
                max_attempts=validated_data.get('max_attempts', 1),
            )
            total_mark = self._create_questions(quiz, question_list)

            # Use .update() to avoid re-triggering post_save signal
            Quiz.objects.filter(pk=quiz.pk).update(total_mark=total_mark)
            quiz.refresh_from_db()
        return quiz
    # ── Update ──────────────────────────────────────────────────────────────────
    def update(self, instance, validated_data):
        question_list = validated_data.pop('questions', None)

        instance.quiz_name = validated_data.get('quiz_name', instance.quiz_name)
        instance.description = validated_data.get('description', instance.description)
        instance.max_attempts = validated_data.get('max_attempts', instance.max_attempts)
        instance.save()
        if question_list is not None:
            with transaction.atomic():
                total_mark = self._update_questions(instance, question_list)
                Quiz.objects.filter(pk=instance.pk).update(total_mark=total_mark)
                instance.refresh_from_db()
        return instance
# =================== Quiz List Serializer ===================
class QuizListSerializer(serializers.ModelSerializer):
    """Compact quiz view for dashboards and lists — avoids loading full question data"""

    course_name = serializers.ReadOnlyField(source='course.title')
    quiz_status = serializers.SerializerMethodField()
    attempts_used = serializers.SerializerMethodField()
    best_score = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = [
            'slug', 'quiz_name', 'total_mark', 'max_attempts',
            'course_name', 'attempts_used', 'best_score', 'quiz_status'
        ]

    def _get_attempts(self, obj):
        request = self.context.get('request')
        if not request:
            return Attempt.objects.none()
        return Attempt.objects.filter(student=request.user, quiz=obj)

    def get_attempts_used(self, obj):
        # Use annotated value if available (avoids N+1 on list view)
        if hasattr(obj, 'attempts_count'):
            return obj.attempts_count
        return self._get_attempts(obj).count()

    def get_best_score(self, obj):
        if hasattr(obj, 'best_score_value'):
            return obj.best_score_value or 0
        from django.db.models import Max
        return self._get_attempts(obj).aggregate(best=Max('score'))['best'] or 0

    def get_quiz_status(self, obj):
        """
        not_started → no attempts yet
        passed      → at least one passed attempt
        failed      → all attempts used, none passed
        can_retry   → has failed attempt but retries remaining
        """
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
# =================== Quiz Detail Serializers ===================
class QuizDetailInstructorSerializer(serializers.ModelSerializer):
    """Full quiz detail with correct answers — instructors and admins only"""
    questions = QuestionSerializer(many=True, read_only=True)
    course_name = serializers.ReadOnlyField(source='course.title')
    class Meta:
        model = Quiz
        fields = [
            'slug', 'quiz_name', 'description', 'total_mark',
            'max_attempts', 'course_name', 'questions'
        ]
class QuizDetailStudentSerializer(serializers.ModelSerializer):
    """Full quiz detail without correct answers — safe for students"""

    questions = QuestionStudentSerializer(many=True, read_only=True)
    course_name = serializers.ReadOnlyField(source='course.title')
    attempts_used = serializers.SerializerMethodField()
    class Meta:
        model = Quiz
        fields = [
            'slug', 'quiz_name', 'description', 'total_mark',
            'max_attempts', 'course_name', 'attempts_used', 'questions'
        ]
    def get_attempts_used(self, obj):
        return Attempt.objects.filter(
            student=self.context['request'].user, quiz=obj
        ).count()
# =================== Streak Helper ===================
def _check_and_notify_streak(user):
    """
    Fires after every quiz submission.
    Sends a streak notification if the student made attempts on 7 consecutive days.
    Sends at most once per day to avoid spam.
    """
    from django.utils import timezone
    from datetime import timedelta
    today = timezone.now().date()
    recent_days = list(
        Attempt.objects.filter(student=user, score__gt=0)
        .values_list('attempt_date__date', flat=True)
        .distinct()
        .order_by('-attempt_date__date')[:7]
    )
    if len(recent_days) < 7:
        return
    for i in range(6):
        if recent_days[i] - recent_days[i + 1] != timedelta(days=1):
            return
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
# =================== Submission Serializers ===================
class StudentAnswerInputSerializer(serializers.Serializer):
    """
    Standardized input for both single and multiple-choice questions.
    `choice_slugs` is a list — for single-choice, only one slug is expected.
    """
    question_slug = serializers.SlugField()
    choice_slugs = serializers.ListField(
        child=serializers.SlugField(),
        min_length=1
    )
class SubmitAttemptSerializer(serializers.Serializer):
    """
    Handles the full quiz submission flow:

    1. Validates no duplicate questions in the payload.
    2. Enforces max_attempts limit.
    3. Blocks concurrent pending submissions (anti-cheat).
    4. Enforces all questions must be answered (no partial submissions).
    5. Validates single-choice questions don't receive multiple slugs.
    6. Validates all submitted choice slugs belong to their question.
    7. Applies All-or-Nothing scoring:
       - Student must select ALL correct choices and NO wrong ones to earn the mark.
    8. Writes attempt + student answers atomically.
    9. Sends quiz result notification.
    10. Checks 7-day streak.

    NOTE: attempt_number is set automatically by the pre_save signal — do NOT set it here.
    """
    answers = StudentAnswerInputSerializer(many=True)
    def validate_answers(self, answers):
        if not answers:
            raise serializers.ValidationError("Answers list cannot be empty.")
        quiz = self.context['quiz']
        question_type_map = {
            q.slug: q.question_type
            for q in quiz.questions.only('slug', 'question_type')
        }
        seen_questions = set()
        for ans in answers:
            q_slug = ans['question_slug']

            if q_slug in seen_questions:
                raise serializers.ValidationError(
                    f"Duplicate entry for question '{q_slug}'. "
                    f"Each question must appear exactly once."
                )
            seen_questions.add(q_slug)
            q_type = question_type_map.get(q_slug)
            if q_type == 'single' and len(ans['choice_slugs']) > 1:
                raise serializers.ValidationError(
                    f"Question '{q_slug}' is single-choice. "
                    f"Only one choice slug is allowed."
                )
        return answers
    def validate(self, data):
        user = self.context['request'].user
        quiz = self.context['quiz']
        # Enforce max_attempts
        attempts_used = Attempt.objects.filter(student=user, quiz=quiz).count()
        if attempts_used >= quiz.max_attempts:
            raise serializers.ValidationError(
                f"You have reached the maximum number of attempts ({quiz.max_attempts})."
            )
        # Block concurrent pending submissions
        if Attempt.objects.filter(student=user, quiz=quiz, status='pending').exists():
            raise serializers.ValidationError(
                "You already have a pending attempt for this quiz. "
                "Please wait for it to be finalized before starting a new one."
            )
        return data
    def create(self, validated_data):
        user = self.context['request'].user
        quiz = self.context['quiz']
        # Enforce all questions answered before touching the DB
        question_count = quiz.questions.count()
        submitted_count = len(validated_data['answers'])
        if submitted_count != question_count:
            raise serializers.ValidationError(
                f"You must answer all {question_count} questions. "
                f"You submitted {submitted_count}."
            )
        # Resolve all slugs to DB objects before writing anything
        resolved = []
        for ans in validated_data['answers']:
            question = get_object_or_404(
                Question, slug=ans['question_slug'], quiz=quiz
            )
            choices = list(
                Choice.objects.filter(
                    slug__in=ans['choice_slugs'], question=question
                )
            )
            # Validate that all submitted slugs resolved to real choices
            if len(choices) != len(ans['choice_slugs']):
                raise serializers.ValidationError(
                    f"One or more invalid choice slugs for question '{question.slug}'."
                )
            resolved.append((question, choices))
        # Atomic write — all or nothing
        with transaction.atomic():
            # attempt_number is set automatically by the pre_save signal
            attempt = Attempt.objects.create(student=user, quiz=quiz)
            total_score = 0
            student_answer_objs = []
            for question, choices in resolved:
                submitted_slugs = {c.slug for c in choices}
                correct_slugs = set(
                    question.choices.filter(is_correct=True).values_list('slug', flat=True)
                )
                # All-or-Nothing scoring:
                # Student must select exactly all correct choices and nothing else
                if submitted_slugs == correct_slugs:
                    total_score += question.mark
                for choice in choices:
                    student_answer_objs.append(
                        StudentAnswer(
                            attempt=attempt,
                            question=question,
                            selected_choice=choice
                        )
                    )
            StudentAnswer.objects.bulk_create(student_answer_objs)
            attempt.score = total_score
            attempt.save(update_fields=['score'])
            attempt.calculate_status()
            # Notify student with their result
            Notification.objects.create(
                user=user,
                title=f"Quiz Result: {quiz.quiz_name}",
                body=(
                    f"Your score: {attempt.score}/{quiz.total_mark} "
                    f"({attempt.get_score_percentage()}%). "
                    f"Status: {attempt.status.capitalize()}."
                ),
                notification_type='quiz_result'
            )
            _check_and_notify_streak(user)
        return attempt
# =================== Attempt Result Serializer ===================
class AttemptResultSerializer(serializers.ModelSerializer):
    """
    Full result for a single attempt.
    Groups multiple selected choices under the same question for multiple-choice display.
    is_correct uses All-or-Nothing logic matching the scoring in SubmitAttemptSerializer.
    """
    quiz_name = serializers.ReadOnlyField(source='quiz.quiz_name')
    total_mark = serializers.ReadOnlyField(source='quiz.total_mark')
    score_percentage = serializers.SerializerMethodField()
    answers = serializers.SerializerMethodField()
    class Meta:
        model = Attempt
        fields = [
            'slug', 'quiz_name', 'total_mark', 'score', 'score_percentage',
            'status', 'attempt_number', 'attempt_date', 'answers'
        ]
    def get_score_percentage(self, obj):
        return obj.get_score_percentage()

    def get_answers(self, obj):
        """
        Groups selected choices by question.
        is_correct = True only if the student selected ALL correct choices
        and NO wrong ones (All-or-Nothing, matching the scoring logic).
        """
        # Group answers by question
        question_map = {}
        for ans in obj.answers.select_related('question', 'selected_choice').all():
            q = ans.question
            if q.slug not in question_map:
                question_map[q.slug] = {
                    "question": q.q_name,
                    "question_type": q.question_type,
                    "selected_choices": [],
                    "selected_slugs": set(),
                    "question_obj": q,
                }
            question_map[q.slug]["selected_choices"].append(
                ans.selected_choice.text_choice
            )
            question_map[q.slug]["selected_slugs"].add(ans.selected_choice.slug)
        # Build result with is_correct per question
        result = []
        for data in question_map.values():
            q = data["question_obj"]
            correct_slugs = set(
                q.choices.filter(is_correct=True).values_list('slug', flat=True)
            )
            is_correct = data["selected_slugs"] == correct_slugs
            result.append({
                "question": data["question"],
                "question_type": data["question_type"],
                "selected": data["selected_choices"],
                "is_correct": is_correct,
            })
        return result
# =================== Attempt List Serializer (Instructor/Admin) ===================
class AttemptListSerializer(serializers.ModelSerializer):
    """Summary view of all student attempts — for instructors and admins"""

    student_email = serializers.ReadOnlyField(source='student.email')
    quiz_name = serializers.ReadOnlyField(source='quiz.quiz_name')
    total_mark = serializers.ReadOnlyField(source='quiz.total_mark')

    class Meta:
        model = Attempt
        fields = [
            'slug', 'student_email', 'quiz_name', 'total_mark',
            'score', 'status', 'attempt_number', 'attempt_date'
        ]