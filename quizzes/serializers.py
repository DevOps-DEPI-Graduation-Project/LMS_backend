import uuid
from rest_framework import serializers
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Quiz, Question, Choice, Attempt, StudentAnswer
from notifications.models import Notification
from cources.models import Course

# =================== Choice Serializers ===================
class ChoiceSerializer(serializers.ModelSerializer):
    """Full choice data including is_correct — instructors/admins only"""
    choice_name = serializers.CharField(source='text_choice')
    class Meta:
        model = Choice
        fields = ['slug', 'choice_name', 'is_correct']

class ChoiceStudentSerializer(serializers.ModelSerializer):
    """Hides is_correct from students"""
    choice_name = serializers.CharField(source='text_choice')
    class Meta:
        model = Choice
        fields = ['slug', 'choice_name']

class ChoiceCreateSerializer(serializers.ModelSerializer):
    """Handles single/multiple choice updates with data integrity in save()"""
    choice_name = serializers.CharField(source='text_choice')
    class Meta:
        model = Choice
        fields = ['slug', 'choice_name', 'is_correct']
        read_only_fields = ['slug']
    def save(self, **kwargs):
        question = self.context.get('question')
        is_correct = self.validated_data.get('is_correct', False)
        with transaction.atomic():
            if is_correct and question and question.question_type == 'single':
                Choice.objects.filter(question=question, is_correct=True).update(is_correct=False)
            return super().save(**kwargs)

# =================== Question Serializers ===================
class QuestionSerializer(serializers.ModelSerializer):
    """Instructor view with nested choices"""
    question_name = serializers.CharField(source='q_name')
    choices = ChoiceSerializer(many=True, read_only=True)
    class Meta:
        model = Question
        fields = ['slug', 'question_name', 'mark', 'question_type', 'choices']

class QuestionStudentSerializer(serializers.ModelSerializer):
    """Student view with safe choice data"""
    question_name = serializers.CharField(source='q_name')
    choices = ChoiceStudentSerializer(many=True, read_only=True)
    class Meta:
        model = Question
        fields = ['slug', 'question_name', 'question_type', 'choices']

class QuestionCreateSerializer(serializers.ModelSerializer):
    """Standalone question creation"""
    question_name = serializers.CharField(source='q_name')
    class Meta:
        model = Question
        fields = ['slug', 'question_name', 'mark', 'question_type']
        read_only_fields = ['slug']

# =================== Nested Quiz Serializers ===================
class NestedChoiceSerializer(serializers.Serializer):
    slug = serializers.SlugField(required=False)
    choice_name = serializers.CharField()
    isCorrect = serializers.BooleanField()

class NestedQuestionSerializer(serializers.Serializer):
    slug = serializers.SlugField(required=False)
    question_name = serializers.CharField()
    mark = serializers.IntegerField(min_value=1)
    question_type = serializers.ChoiceField(choices=Question.QUESTION_TYPE_CHOICES, default='single')
    choices = NestedChoiceSerializer(many=True)

    def validate(self, data):
        choices = data.get('choices', [])
        if len(choices) < 2:
            raise serializers.ValidationError("Must have at least 2 choices.")
        correct_count = sum(1 for c in choices if c.get('isCorrect', False))
        q_type = data.get('question_type', 'single')
        if q_type == 'single' and correct_count != 1:
            raise serializers.ValidationError("Single-choice must have exactly 1 correct answer.")
        if q_type == 'multiple' and correct_count < 1:
            raise serializers.ValidationError("Multiple-choice must have at least 1 correct answer.")
        return data

# =================== Full Quiz Management ===================
class CourseQuizCreateSerializer(serializers.Serializer):
    """Orphan-removal enabled creation and updates for Quizzes using slugs"""
    slug = serializers.SlugField(read_only=True)
    quiz_name = serializers.CharField(required=False)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    passing_percentage = serializers.IntegerField(required=False, min_value=0, max_value=100)
    max_attempts = serializers.IntegerField(required=False, min_value=1)
    questions = NestedQuestionSerializer(many=True, required=False)

    def _update_choices(self, question, choices_data):
        incoming_slugs = {c['slug'] for c in choices_data if 'slug' in c}
        question.choices.exclude(slug__in=incoming_slugs).delete()
        
        for c_data in choices_data:
            c_slug = c_data.pop('slug', None)
            fields = {
                'text_choice': c_data['choice_name'],
                'is_correct': c_data['isCorrect']
            }
            if c_slug:
                Choice.objects.filter(slug=c_slug, question=question).update(**fields)
            else:
                Choice.objects.create(
                    question=question,
                    slug=f"c-{uuid.uuid4().hex[:12]}",
                    **fields
                )

    def _update_questions(self, quiz, question_list):
        incoming_slugs = {q['slug'] for q in question_list if 'slug' in q}
        quiz.questions.exclude(slug__in=incoming_slugs).delete()
        
        total_mark = 0
        for q_data in question_list:
            c_list = q_data.pop('choices', [])
            q_slug = q_data.pop('slug', None)
            fields = {
                'q_name': q_data['question_name'],
                'mark': q_data['mark'],
                'question_type': q_data.get('question_type', 'single')
            }
            
            if q_slug:
                Question.objects.filter(slug=q_slug, quiz=quiz).update(**fields)
                question = Question.objects.get(slug=q_slug, quiz=quiz)
            else:
                question = Question.objects.create(
                    quiz=quiz,
                    slug=f"q-{uuid.uuid4().hex[:12]}",
                    **fields
                )
            
            self._update_choices(question, c_list)
            total_mark += q_data['mark']
        return total_mark

    def create(self, validated_data):
        course = self.context['course']
        q_list = validated_data.pop('questions', [])
        
        with transaction.atomic():
            quiz = Quiz.objects.create(
                course=course,
                quiz_name=validated_data.get('quiz_name'),
                description=validated_data.get('description', ''),
                passing_percentage=validated_data.get('passing_percentage', 50),
                max_attempts=validated_data.get('max_attempts', 1)
            )
            total_mark = self._update_questions(quiz, q_list)
            Quiz.objects.filter(pk=quiz.pk).update(total_mark=total_mark)
            quiz.refresh_from_db()
        return quiz

    def update(self, instance, validated_data):
        q_list = validated_data.pop('questions', None)
        
        instance.quiz_name = validated_data.get('quiz_name', instance.quiz_name)
        instance.description = validated_data.get('description', instance.description)
        instance.passing_percentage = validated_data.get('passing_percentage', instance.passing_percentage)
        instance.max_attempts = validated_data.get('max_attempts', instance.max_attempts)
        instance.save()
        
        if q_list is not None:
            with transaction.atomic():
                total_mark = self._update_questions(instance, q_list)
                Quiz.objects.filter(pk=instance.pk).update(total_mark=total_mark)
                instance.refresh_from_db()
        return instance

# =================== Quiz Lists & Details ===================
class QuizListSerializer(serializers.ModelSerializer):
    course_name = serializers.ReadOnlyField(source='course.title')
    quiz_status = serializers.SerializerMethodField()
    attempts_used = serializers.SerializerMethodField()
    best_score = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = [
            'slug', 'quiz_name', 'total_mark', 'passing_percentage', 
            'max_attempts', 'course_name', 'attempts_used', 
            'best_score', 'quiz_status'
        ]

    def _get_attempts(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return Attempt.objects.none()
        return Attempt.objects.filter(student=request.user, quiz=obj)

    def get_attempts_used(self, obj):
        return getattr(obj, 'attempts_count', self._get_attempts(obj).count())

    def get_best_score(self, obj):
        from django.db.models import Max
        return getattr(obj, 'best_score_value', self._get_attempts(obj).aggregate(Max('score'))['score__max'] or 0)

    def get_quiz_status(self, obj):
        attempts = self._get_attempts(obj)
        count = getattr(obj, 'attempts_count', attempts.count())
        if count == 0:
            return 'not_started'
        
        # Check if passed (passed_count is an annotation from the view)
        passed_count = getattr(obj, 'passed_count', None)
        if passed_count is not None:
            has_passed = passed_count > 0
        else:
            has_passed = attempts.filter(status='passed').exists()

        if has_passed:
            return 'passed'
            
        if obj.max_attempts and count >= obj.max_attempts:
            return 'failed'
        return 'can_retry'

class QuizDetailInstructorSerializer(serializers.ModelSerializer):
    course_name = serializers.ReadOnlyField(source='course.title')
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = [
            'slug', 'quiz_name', 'description', 'total_mark', 
            'passing_percentage', 'max_attempts', 'course_name', 
            'questions', 'created_at', 'updated_at'
        ]

class QuizDetailStudentSerializer(serializers.ModelSerializer):
    course_name = serializers.ReadOnlyField(source='course.title')
    questions = QuestionStudentSerializer(many=True, read_only=True)
    attempts_used = serializers.SerializerMethodField()
    best_score = serializers.SerializerMethodField()
    quiz_status = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = [
            'slug', 'quiz_name', 'description', 'total_mark', 
            'passing_percentage', 'max_attempts', 'course_name', 
            'questions', 'attempts_used', 'best_score', 'quiz_status'
        ]

    def _get_attempts(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return Attempt.objects.none()
        return Attempt.objects.filter(student=request.user, quiz=obj)

    def get_attempts_used(self, obj):
        return self._get_attempts(obj).count()

    def get_best_score(self, obj):
        from django.db.models import Max
        return self._get_attempts(obj).aggregate(Max('score'))['score__max'] or 0

    def get_quiz_status(self, obj):
        attempts = self._get_attempts(obj)
        count = attempts.count()
        if count == 0: return 'not_started'
        if attempts.filter(status='passed').exists(): return 'passed'
        if obj.max_attempts and count >= obj.max_attempts: return 'failed'
        return 'can_retry'

# =================== Streak & Notifications ===================
def _check_and_notify_streak(user):
    from django.utils import timezone
    from datetime import timedelta
    today = timezone.now().date()
    # Logic to check for 7 consecutive days of attempts with score > 0
    recent_dates = list(
        Attempt.objects.filter(student=user, score__gt=0)
        .values_list('attempt_date__date', flat=True)
        .distinct()
        .order_by('-attempt_date__date')[:7]
    )
    if len(recent_dates) == 7:
        is_streak = all(
            recent_dates[i] - recent_dates[i+1] == timedelta(days=1)
            for i in range(6)
        )
        if is_streak:
            if not Notification.objects.filter(user=user, notification_type='streak', created_at__date=today).exists():
                Notification.objects.create(
                    user=user,
                    title="7-Day Streak!",
                    body="Congrats on your 7-day learning streak!",
                    notification_type='streak'
                )

# =================== Submission Flow (Optimized) ===================
class StudentAnswerInputSerializer(serializers.Serializer):
    question_slug = serializers.SlugField()
    choice_slugs = serializers.ListField(
        child=serializers.SlugField(),
        min_length=1
    )

class SubmitAttemptSerializer(serializers.Serializer):
    """Optimized submission with prefetch_related to solve N+1 queries"""
    answers = StudentAnswerInputSerializer(many=True)

    def validate(self, data):
        user = self.context['request'].user
        quiz = self.context['quiz']
        
        if Attempt.objects.filter(student=user, quiz=quiz).count() >= quiz.max_attempts:
            raise serializers.ValidationError("Maximum attempts reached for this quiz.")
            
        if Attempt.objects.filter(student=user, quiz=quiz, status='pending').exists():
            raise serializers.ValidationError("You have a pending attempt. Please complete it first.")
            
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        quiz = self.context['quiz']
        
        # Optimization: Fetch all questions and choices in ONE query
        questions = quiz.questions.prefetch_related('choices').all()
        question_map = {q.slug: q for q in questions}
        
        if len(validated_data['answers']) != len(question_map):
            raise serializers.ValidationError("All questions must be answered.")

        with transaction.atomic():
            # Attempt number is handled by pre_save signal in signals.py
            attempt = Attempt.objects.create(student=user, quiz=quiz)
            
            total_score = 0
            answer_objs = []
            
            for ans_data in validated_data['answers']:
                q_slug = ans_data['question_slug']
                submitted_choice_slugs = set(ans_data['choice_slugs'])
                
                question = question_map.get(q_slug)
                if not question:
                    raise serializers.ValidationError(f"Invalid question slug: {q_slug}")
                
                # Check choices
                choices = {c.slug: c for c in question.choices.all()}
                correct_choice_slugs = {c.slug for c in choices.values() if c.is_correct}
                
                if not submitted_choice_slugs.issubset(choices.keys()):
                    raise serializers.ValidationError(f"Invalid choice slug for question {q_slug}")
                
                # Calculate score
                if submitted_choice_slugs == correct_choice_slugs:
                    total_score += question.mark
                
                # Prepare StudentAnswer objects for bulk_create
                for choice_slug in submitted_choice_slugs:
                    answer_objs.append(StudentAnswer(
                        attempt=attempt,
                        question=question,
                        selected_choice=choices[choice_slug]
                    ))
            
            StudentAnswer.objects.bulk_create(answer_objs)
            attempt.score = total_score
            attempt.save(update_fields=['score'])
            attempt.calculate_status()
            
            # Notify user
            Notification.objects.create(
                user=user,
                title=f"Quiz Result: {quiz.quiz_name}",
                body=f"You scored {attempt.score}/{quiz.total_mark} in the quiz.",
                notification_type='quiz_result'
            )
            
            _check_and_notify_streak(user)
            
        return attempt

# =================== Results & Monitoring ===================
class AttemptResultSerializer(serializers.ModelSerializer):
    quiz_name = serializers.ReadOnlyField(source='quiz.quiz_name')
    total_mark = serializers.ReadOnlyField(source='quiz.total_mark')
    answers = serializers.SerializerMethodField()

    class Meta:
        model = Attempt
        fields = [
            'slug', 'quiz_name', 'total_mark', 'score', 'status', 
            'attempt_number', 'attempt_date', 'answers'
        ]

    def get_answers(self, obj):
        """Optimized to avoid N+1 queries by using prefetched data"""
        # Ensure answers and their related questions/choices are prefetched in the view
        # or use select_related/prefetch_related here if not already done.
        
        results = []
        # Group student answers by question
        # Note: We use .all() which should be prefetched
        student_answers = obj.answers.all()
        
        # To avoid multiple hits, we group them in memory
        from collections import defaultdict
        q_answers = defaultdict(list)
        for sa in student_answers:
            q_answers[sa.question].append(sa)
            
        for question, answers in q_answers.items():
            # Get all choices for this question to find correct ones
            # Optimization: If choices are prefetched on question, this is fast
            all_choices = list(question.choices.all())
            correct_slugs = {c.slug for c in all_choices if c.is_correct}
            selected_slugs = {a.selected_choice.slug for a in answers}
            selected_texts = [a.selected_choice.text_choice for a in answers]
            
            results.append({
                "question": question.q_name,
                "question_slug": question.slug,
                "question_type": question.question_type,
                "selected_choices": selected_texts,
                "is_correct": selected_slugs == correct_slugs
            })
            
        return results

class AttemptListSerializer(serializers.ModelSerializer):
    student_email = serializers.ReadOnlyField(source='student.email')
    quiz_name = serializers.ReadOnlyField(source='quiz.quiz_name')
    total_mark = serializers.ReadOnlyField(source='quiz.total_mark')

    class Meta:
        model = Attempt
        fields = [
            'slug', 'student_email', 'quiz_name', 'total_mark', 
            'score', 'status', 'attempt_number', 'attempt_date'
        ]