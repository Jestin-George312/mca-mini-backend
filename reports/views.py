# report/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Sum

from quiz.models import QuizResult
from materials.models import Material # To get subject names

class PerformanceSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        # 1. Fetch all quiz results (unchanged)
        results = QuizResult.objects.filter(user=user).select_related('topic__material').order_by('timestamp')

        if not results.exists():
            return Response({
                'learning_rate': 0,
                'subjects': [],
                'chart_data': []
            }, status=status.HTTP_200_OK)

        # 2. Calculate overall "Learning Rate" (unchanged)
        total_score_agg = results.aggregate(total_score=Sum('score'))
        total_questions_agg = results.aggregate(total_questions=Sum('total_questions'))
        
        total_score = total_score_agg.get('total_score') or 0
        total_questions = total_questions_agg.get('total_questions') or 0

        learning_rate = 0
        if total_questions > 0:
            learning_rate = (total_score / total_questions) * 100

        # 3. ✅ --- THIS LOGIC IS UPDATED --- ✅
        # Get a unique list of subjects the user has taken quizzes in
        subject_list_raw = list(results.values_list('topic__material__subject', flat=True).distinct())

        # Clean and de-duplicate the list to handle case/spacing issues
        cleaned_subjects = set()
        for subject in subject_list_raw:
            if subject: # Check if not None or empty string
                # Normalize: convert to title case and strip whitespace
                cleaned_subjects.add(subject.strip().title()) 
        
        # Convert back to a list for the JSON response
        subject_list = list(cleaned_subjects)


        # 4. ✅ --- THIS LOGIC IS ALSO UPDATED --- ✅
        # Format all individual quiz results for the chart
        chart_data = []
        for result in results:
            # Normalize the subject name here too so it matches the dropdown
            subject_name = "Unnamed" # Default
            if result.topic.material and result.topic.material.subject:
                 subject_name = result.topic.material.subject.strip().title()

            chart_data.append({
                'day': result.timestamp.strftime('%Y-%m-%d'),
                'percentage': (result.score / result.total_questions) * 100,
                'subject': subject_name, # Use the cleaned name
                'topic': result.topic.topic_name
            })

        # 5. Assemble the final response
        response_data = {
            'learning_rate': learning_rate,
            'subjects': subject_list, # Send the cleaned list
            'chart_data': chart_data   # Send data with cleaned subjects
        }
        
        return Response(response_data, status=status.HTTP_200_OK)

class QuizHistoryView(APIView):
    """
    Provides a list of all past quiz results for the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        # Fetch all results, newest first
        results = QuizResult.objects.filter(user=user)\
                                    .select_related('topic__material')\
                                    .order_by('-timestamp')

        # Return an empty list if no results
        if not results.exists():
            return Response([], status=status.HTTP_200_OK)

        # Serialize the data into a clean list
        serialized_data = []
        for res in results:
            percentage = 0
            if res.total_questions > 0:
                percentage = (res.score / res.total_questions) * 100
            
            subject_name = "N/A"
            if res.topic.material and res.topic.material.subject:
                subject_name = res.topic.material.subject.strip().title()

            serialized_data.append({
                'id': res.id,
                'date': res.timestamp.strftime('%d %b %Y, %I:%M %p'), # e.g., "22 Oct 2025, 06:30 AM"
                'subject': subject_name,
                'topic': res.topic.topic_name,
                'score': res.score,
                'total_questions': res.total_questions,
                'percentage': round(percentage, 1) # e.g., 85.5
            })
        
        return Response(serialized_data, status=status.HTTP_200_OK)        