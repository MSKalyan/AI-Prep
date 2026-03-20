from datetime import datetime, timedelta
from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone
from ..models import StudySession, PerformanceMetrics, WeakArea, DailyProgress,PerformanceSnapshot


class AnalyticsService:
    """Service layer for analytics calculations"""
    
    @staticmethod
    def get_user_analytics(user):
        """Get comprehensive analytics for a user"""
        
        # Overall statistics
        overall_stats = AnalyticsService._calculate_overall_stats(user)
        
        # Subject-wise performance
        subject_performance = PerformanceMetrics.objects.filter(user=user)
        
        # Weak areas
        weak_areas = WeakArea.objects.filter(user=user)[:10]
        
        # Recent progress (last 30 days)
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        recent_progress = DailyProgress.objects.filter(
            user=user,
            date__gte=thirty_days_ago
        ).order_by('-date')
        
        # Study streak
        study_streak = AnalyticsService._calculate_study_streak(user)
        
        # Total study time
        total_study_time = StudySession.objects.filter(user=user).aggregate(
            total=Sum('duration_minutes')
        )['total'] or 0
        
        return {
            'overall_stats': overall_stats,
            'subject_performance': subject_performance,
            'weak_areas': weak_areas,
            'recent_progress': recent_progress,
            'study_streak': study_streak,
            'total_study_time': total_study_time
        }
    
    @staticmethod
    def _calculate_overall_stats(user):
        """Calculate overall performance statistics"""
        
        from apps.mocktest.models import TestAttempt
        
        # Test statistics
        test_attempts = TestAttempt.objects.filter(
            user=user,
            submitted_at__isnull=False
        )
        
        total_tests = test_attempts.count()
        avg_score = test_attempts.aggregate(Avg('percentage'))['percentage__avg'] or 0
        
        # Question statistics
        total_correct = test_attempts.aggregate(Sum('correct_answers'))['correct_answers__sum'] or 0
        total_incorrect = test_attempts.aggregate(Sum('incorrect_answers'))['incorrect_answers__sum'] or 0
        total_questions = total_correct + total_incorrect
        
        accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0
        
        # AI usage
        from apps.ai_service.models import Message
        ai_queries = Message.objects.filter(
            conversation__user=user,
            role='user'
        ).count()
        
        # Roadmap progress
        from apps.roadmap.models import RoadmapTopic
        completed_topics = RoadmapTopic.objects.filter(
            roadmap__user=user,
            is_completed=True
        ).count()
        
        return {
            'total_tests': total_tests,
            'average_score': round(avg_score, 2),
            'total_questions': total_questions,
            'correct_answers': total_correct,
            'incorrect_answers': total_incorrect,
            'accuracy': round(accuracy, 2),
            'ai_queries': ai_queries,
            'completed_topics': completed_topics
        }
    
    @staticmethod
    def _calculate_study_streak(user):
        """Calculate current study streak in days"""
        
        today = timezone.now().date()
        streak = 0
        current_date = today
        
        while True:
            has_activity = DailyProgress.objects.filter(
                user=user,
                date=current_date,
                study_time_minutes__gt=0
            ).exists()
            
            if has_activity:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break
            
            # Limit to 365 days
            if streak >= 365:
                break
        
        return streak
    
    @staticmethod
    def update_performance_metrics(user, subject, test_attempt):
        """Update performance metrics after a test"""
        
        metrics, created = PerformanceMetrics.objects.get_or_create(
            user=user,
            subject=subject,
            defaults={
                'total_attempts': 0,
                'total_questions': 0,
                'correct_answers': 0,
                'incorrect_answers': 0
            }
        )
        
        # Update counts
        metrics.total_attempts += 1
        metrics.total_questions += (test_attempt.correct_answers + 
                                   test_attempt.incorrect_answers + 
                                   test_attempt.unanswered)
        metrics.correct_answers += test_attempt.correct_answers
        metrics.incorrect_answers += test_attempt.incorrect_answers
        
        # Calculate accuracy
        total_answered = metrics.correct_answers + metrics.incorrect_answers
        metrics.accuracy_percentage = (
            (metrics.correct_answers / total_answered * 100) 
            if total_answered > 0 else 0
        )
        
        # Calculate average score
        from apps.mocktest.models import TestAttempt
        all_attempts = TestAttempt.objects.filter(
            user=user,
            mock_test__exam_type=test_attempt.mock_test.exam_type
        )
        metrics.average_score = all_attempts.aggregate(
            Avg('score')
        )['score__avg'] or 0
        
        # Update time statistics
        metrics.total_time_minutes += test_attempt.time_taken_minutes
        metrics.average_time_per_question = (
            (metrics.total_time_minutes * 60) / metrics.total_questions
            if metrics.total_questions > 0 else 0
        )
        
        metrics.last_activity = timezone.now()
        metrics.save()
        
        return metrics
    
    @staticmethod
    def update_weak_areas(user, test_attempt):
        """Identify and update weak areas based on test performance"""
        
        from apps.mocktest.models import Answer
        
        # Get incorrect answers
        incorrect_answers = Answer.objects.filter(
            attempt=test_attempt,
            is_correct=False
        ).select_related('question')
        
        # Group by topic
        topic_stats = {}
        for answer in incorrect_answers:
            topic = answer.question.topic
            subject = answer.question.subject
            
            key = f"{subject}:{topic}"
            if key not in topic_stats:
                topic_stats[key] = {
                    'subject': subject,
                    'topic': topic,
                    'attempts': 0,
                    'correct': 0
                }
            
            topic_stats[key]['attempts'] += 1
        
        # Also count correct answers
        correct_answers = Answer.objects.filter(
            attempt=test_attempt,
            is_correct=True
        ).select_related('question')
        
        for answer in correct_answers:
            topic = answer.question.topic
            subject = answer.question.subject
            
            key = f"{subject}:{topic}"
            if key not in topic_stats:
                topic_stats[key] = {
                    'subject': subject,
                    'topic': topic,
                    'attempts': 0,
                    'correct': 0
                }
            
            topic_stats[key]['attempts'] += 1
            topic_stats[key]['correct'] += 1
        
        # Update or create weak areas
        for stats in topic_stats.values():
            weak_area, created = WeakArea.objects.get_or_create(
                user=user,
                subject=stats['subject'],
                topic=stats['topic'],
                defaults={
                    'attempts': 0,
                    'correct': 0
                }
            )
            
            old_accuracy = weak_area.accuracy
            
            weak_area.attempts += stats['attempts']
            weak_area.correct += stats['correct']
            weak_area.accuracy = (
                (weak_area.correct / weak_area.attempts * 100)
                if weak_area.attempts > 0 else 0
            )
            
            # Check if improving
            if not created and weak_area.accuracy > old_accuracy:
                weak_area.is_improving = True
            
            # Set priority based on accuracy
            if weak_area.accuracy < 40:
                weak_area.priority = 1  # High
            elif weak_area.accuracy < 70:
                weak_area.priority = 2  # Medium
            else:
                weak_area.priority = 3  # Low
            
            weak_area.save()
    
    @staticmethod
    def update_daily_progress(user, activity_data):
        """Update daily progress tracking"""
        
        today = timezone.now().date()
        
        progress, created = DailyProgress.objects.get_or_create(
            user=user,
            date=today,
            defaults={
                'study_time_minutes': 0,
                'questions_attempted': 0,
                'questions_correct': 0,
                'mock_tests_taken': 0,
                'ai_queries': 0,
                'topics_covered': []
            }
        )
        
        # Update fields
        if 'study_time' in activity_data:
            progress.study_time_minutes += activity_data['study_time']
        
        if 'questions_attempted' in activity_data:
            progress.questions_attempted += activity_data['questions_attempted']
        
        if 'questions_correct' in activity_data:
            progress.questions_correct += activity_data['questions_correct']
        
        if 'mock_test' in activity_data and activity_data['mock_test']:
            progress.mock_tests_taken += 1
        
        if 'ai_query' in activity_data and activity_data['ai_query']:
            progress.ai_queries += 1
        
        if 'topic' in activity_data and activity_data['topic']:
            if activity_data['topic'] not in progress.topics_covered:
                progress.topics_covered.append(activity_data['topic'])
        
        # Calculate streak
        progress.streak_days = AnalyticsService._calculate_study_streak(user)
        
        # Check if goals met (e.g., study time >= target)
        target_minutes = user.study_hours_per_day * 60
        progress.goals_met = progress.study_time_minutes >= target_minutes
        
        progress.save()
        
        return progress
    @staticmethod
    def rebuild_performance_metrics(user, subject):

        snapshots = PerformanceSnapshot.objects.filter(
            user=user,
            subject=subject
        )

        total_attempts = snapshots.count()

        aggregates = snapshots.aggregate(
            total_score=Sum("score"),
            avg_accuracy=Avg("accuracy"),
            total_marks=Sum("total_marks")
        )

        total_score = aggregates["total_score"] or 0
        total_marks = aggregates["total_marks"] or 0
        avg_accuracy = aggregates["avg_accuracy"] or 0

        metrics, _ = PerformanceMetrics.objects.get_or_create(
            user=user,
            subject=subject
        )

        metrics.total_attempts = total_attempts
        metrics.total_questions = total_marks
        metrics.correct_answers = total_score
        metrics.accuracy_percentage = avg_accuracy

        metrics.save()

        return metrics
    @staticmethod
    def create_performance_snapshot(test_attempt):

        user = test_attempt.user
        subject = (
            test_attempt.mock_test.exam.name
            if test_attempt.mock_test.exam else "Unknown"
        )
        if test_attempt.total_marks == 0:
            accuracy = 0
        else:
            accuracy = (test_attempt.score / test_attempt.total_marks) * 100

        snapshot = PerformanceSnapshot.objects.get_or_create(
            test_attempt=test_attempt,
        defaults={
            "user": user,
            "subject": subject,
            "score": test_attempt.score,
            "total_marks": test_attempt.total_marks,
            "accuracy": accuracy,
        }
          
        )

        AnalyticsService.rebuild_performance_metrics(user, subject)

        return snapshot
    
    @staticmethod
    def get_weak_subject(user):

        weak = PerformanceMetrics.objects.filter(
            user=user,
            total_attempts__gt=0
        ).order_by("accuracy_percentage").first()

        if not weak:
            return None

        return {
            "subject": weak.subject,
            "accuracy": round(weak.accuracy_percentage, 2),
            "attempts": weak.total_attempts
        }