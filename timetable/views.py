# timetable/views.py

import os
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
import google.generativeai as genai
from collections import defaultdict

from materials.models import Material
# ✅ Import the updated TimeSlotTask model
from .models import StudyPlanRequest, StudyPlan, TimeSlotTask
from topic_analysis.models import Topic 

# --- Gemini API Setup (unchanged) ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("⚠️ Warning: GEMINI_API_KEY not set.")
else:
    genai.configure(api_key=GEMINI_API_KEY)


# --- StudyPlanDetailView (✅ MODIFIED) ---
class StudyPlanDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            study_plan = StudyPlan.objects.filter(
                request__user=request.user
            ).order_by('-created_at').first()

            if not study_plan:
                return Response(
                    {"message": "No study plan found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            slots = study_plan.time_slot_tasks.all().order_by('day', 'id')

            plan_by_day = defaultdict(list)
            for slot in slots:
                # ✅ Use slot.duration
                plan_by_day[slot.day].append({
                    "duration": slot.duration,
                    "subject": slot.subject,
                    "topics": slot.topics,
                    "notes": slot.notes,
                })

            tasks_data = [
                {"day": day, "tasks": task_list}
                for day, task_list in plan_by_day.items()
            ]

            response_data = {"study_plan": tasks_data}
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# --- GenerateStudyPlanView (✅ MODIFIED) ---
class GenerateStudyPlanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            # 1️⃣ & 2️⃣ & 3️⃣ (No change in logic)
            data = request.data
            material_ids = data.get("material_ids")
            total_days = int(data.get("totalDays", 7))
            hours_per_day = int(data.get("hoursPerDay", 2))

            if not material_ids:
                return Response({"error": "No study materials selected."}, status=400)
            materials = Material.objects.filter(id__in=material_ids)
            if not materials.exists():
                return Response({"error": "Selected materials not found."}, status=404)
            all_topics = Topic.objects.filter(
                material_id__in=material_ids
            ).select_related('material')
            if not all_topics.exists():
                return Response({"error": "No topic analysis data found."}, status=404)

            material_topic_map = defaultdict(list)
            for topic in all_topics:
                topic_detail = (
                    f"{topic.topic_name} "
                    f"(Difficulty: {topic.difficulty_class}, "
                    f"Summary: {topic.summary})"
                )
                material_topic_map[topic.material].append(topic_detail)

            subjects_and_topics_builder = []
            for material, topics_list in material_topic_map.items():
                subjects_and_topics_builder.append(f"\nSubject: {material.subject}")
                subjects_and_topics_builder.append(f"  Material Title: {material.title}")
                subjects_and_topics_builder.append("    Topics to cover:")
                for topic_str in topics_list:
                    subjects_and_topics_builder.append(f"      - {topic_str}")
            subjects_str = "\n".join(subjects_and_topics_builder)

            # 4️⃣ [✅ NEW PROMPT]
            prompt = f"""
You are an expert academic planner. Create a detailed {total_days}-day study plan
for a student who studies {hours_per_day} hours per day.

Here are the student's materials and the specific topics to cover:
{subjects_str}

**Instructions (CRITICAL):**
1.  **Assign Durations:** The student has {hours_per_day} hours per day. Assign a duration for each task (e.g., "2 hours", "1.5 hours"). The sum of durations for one day **must equal** {hours_per_day}.
2.  **Use Difficulty:** Allocate time based on topic difficulty. 'Hard' topics need *more time* (e.g. "2 hours") than 'easy' topics (e.g. "1 hour").
3.  **Mix Subjects:** If total daily hours is 3 or more, schedule *multiple different subjects* in a single day.
4.  **Cover All Topics:** Ensure *all* topics from the list are scheduled.
5.  **Smart Notes:** "notes" field must contain *specific, helpful advice* related to the topics (e.g., "Practice joins for this SQL topic"). **DO NOT** use generic motivational quotes.

**Output strictly in JSON (no markdown, no explanations):**
{{
  "study_plan": [
    {{
      "day": 1,
      "tasks": [
        {{
          "duration": "2 hours",
          "subject": "Name of the Subject (e.g., Python)",
          "topics": "List of TOPIC NAMES ONLY for this slot (e.g., 'Variables', 'Data Types')",
          "notes": "Topic-specific advice here. (e.g., 'Focus on the difference between lists and tuples.')"
        }},
        {{
          "duration": "1 hour",
          "subject": "Name of another Subject (e.g., SQL)",
          "topics": "TOPIC NAME for this slot (e.g., 'Basic SELECT Statements')",
          "notes": "Topic-specific advice here. (e.g., 'Practice using the WHERE clause.')"
        }}
      ]
    }},
    {{
      "day": 2,
      "tasks": [
        {{
          "duration": "3 hours",
          "subject": "Python",
          "topics": "Functions, Dictionaries (Hard)",
          "notes": "Dictionaries are a key concept. Practice creating and accessing them."
        }}
      ]
    }}
    ...
  ]
}}
**Crucial:** The "topics" field must contain **only the topic names**.
"""

            # 5️⃣ Call Gemini API (unchanged)
            model = genai.GenerativeModel('models/gemini-pro-latest') 
            response = model.generate_content(prompt)
            result_text = (
                response.text.strip()
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )

            # 6️⃣ Parse JSON (unchanged)
            try:
                plan_json = json.loads(result_text)
            except json.JSONDecodeError:
                print("--- GEMINI FAILED TO RETURN VALID JSON ---")
                print(result_text)
                print("------------------------------------------")
                return Response(
                    {"error": "Failed to generate study plan. The AI returned an invalid format.", "raw_response": result_text},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # 7️⃣ [✅ NEW SAVING LOGIC]
            plan_request = StudyPlanRequest.objects.create(
                user=request.user,
                total_days=total_days,
                hours_per_day=hours_per_day
            )
            plan_request.materials.set(materials)
            study_plan = StudyPlan.objects.create(request=plan_request)

            tasks_to_create = []
            for day_data in plan_json.get("study_plan", []):
                day_number = day_data.get("day")
                if not day_number:
                    continue
                
                for slot_data in day_data.get("tasks", []):
                    tasks_to_create.append(
                        TimeSlotTask(
                            study_plan=study_plan,
                            day=day_number,
                            # ✅ Use duration
                            duration=slot_data.get("duration", "N/A"),
                            subject=slot_data.get("subject", "N/A"),
                            topics=slot_data.get("topics", ""),
                            notes=slot_data.get("notes", "")
                        )
                    )
            
            TimeSlotTask.objects.bulk_create(tasks_to_create)

            return Response(plan_json, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=500)

class UpdateStudyPlanView(APIView):
    """
    Updates a user's latest study plan based on quiz performance,
    *only if* the topic is part of their current plan.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            # 1️⃣ Get input data from the quiz
            data = request.data
            user = request.user
            topic_id = data.get('topicId')
            score = data.get('score')
            total_questions = data.get('totalQuestions')

            if not all([topic_id, score is not None, total_questions is not None]):
                return Response({'error': 'Missing data'}, status=status.HTTP_400_BAD_REQUEST)

            # 2️⃣ Get the topic
            try:
                underperforming_topic = Topic.objects.get(id=topic_id)
            except Topic.DoesNotExist:
                return Response({'error': 'Topic not found'}, status=status.HTTP_404_NOT_FOUND)

            # 3️⃣ Find the user's latest study plan
            latest_plan = StudyPlan.objects.filter(
                request__user=user
            ).order_by('-created_at').first()

            if not latest_plan:
                return Response({'message': 'No study plan found. No update needed.'}, status=status.HTTP_200_OK)
            
            # 4️⃣ ✅ --- THE CRITICAL CHECK --- ✅
            # Check if the topic's material is in the materials set of the latest plan
            plan_materials = latest_plan.request.materials.all()
            if underperforming_topic.material not in plan_materials:
                # If not, do nothing.
                return Response(
                    {'message': 'Quiz topic not part of the current study plan. No update needed.'}, 
                    status=status.HTTP_200_OK
                )

            # 5️⃣ (If check passed) Get original plan's parameters
            plan_request = latest_plan.request
            total_days = plan_request.total_days
            hours_per_day = plan_request.hours_per_day

            # 6️⃣ Re-build the *original* topics list
            all_topics = Topic.objects.filter(
                material_id__in=plan_materials.values_list('id', flat=True)
            ).select_related('material')

            material_topic_map = defaultdict(list)
            for topic in all_topics:
                topic_detail = (
                    f"{topic.topic_name} "
                    f"(Difficulty: {topic.difficulty_class}, "
                    f"Summary: {topic.summary})"
                )
                material_topic_map[topic.material].append(topic_detail)

            subjects_and_topics_builder = []
            for material, topics_list in material_topic_map.items():
                subjects_and_topics_builder.append(f"\nSubject: {material.subject}")
                subjects_and_topics_builder.append(f"  Material Title: {material.title}")
                subjects_and_topics_builder.append("    Topics to cover:")
                for topic_str in topics_list:
                    subjects_and_topics_builder.append(f"      - {topic_str}")
            
            subjects_str = "\n".join(subjects_and_topics_builder)

            # 7️⃣ Build the NEW prompt for Gemini
            prompt = f"""
You are an expert academic planner, and you are **revising** a student's study plan.

**Original Plan Context:**
The plan was for {total_days} days, with {hours_per_day} hours of study per day.
The materials and topics to cover were:
{subjects_str}

**New Information (Performance Feedback):**
The student just took a quiz on the topic **"{underperforming_topic.topic_name}"** and scored **{score} out of {total_questions}**. This is an underperforming topic that needs more focus.

**Your Task:**
Regenerate the **entire {total_days}-day study plan** from scratch with this new information.
The new plan **MUST** give **more time and focus** to the underperforming topic: **"{underperforming_topic.topic_name}"**.
You should also increase focus on any related topics. Allocate more time (longer durations) to this topic.

**Output strictly in JSON (same format as before):**
{{
  "study_plan": [
    {{
      "day": 1,
      "tasks": [
        {{
          "duration": "2 hours",
          "subject": "Subject Name",
          "topics": "Topic Names (e.g., 'Variables', 'Data Types')",
          "notes": "Specific advice (e.g., 'Focus on {underperforming_topic.topic_name} today.')"
        }}
      ]
    }}
    ...
  ]
}}
"""
            
            # 8️⃣ Call Gemini API
            model = genai.GenerativeModel('models/gemini-pro-latest')
            response = model.generate_content(prompt)
            result_text = (
                response.text.strip()
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )

            # 9️⃣ Parse JSON
            try:
                plan_json = json.loads(result_text)
            except json.JSONDecodeError:
                return Response(
                    {"error": "AI returned invalid JSON.", "raw_response": result_text},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # 1️⃣0️⃣ Delete the OLD tasks and save the NEW tasks
            latest_plan.time_slot_tasks.all().delete() # Delete old plan slots

            tasks_to_create = []
            for day_data in plan_json.get("study_plan", []):
                day_number = day_data.get("day")
                if not day_number: continue
                
                for slot_data in day_data.get("tasks", []):
                    tasks_to_create.append(
                        TimeSlotTask(
                            study_plan=latest_plan, # Link to the *same* plan
                            day=day_number,
                            duration=slot_data.get("duration", "N/A"),
                            subject=slot_data.get("subject", "N/A"),
                            topics=slot_data.get("topics", ""),
                            notes=slot_data.get("notes", "")
                        )
                    )
            
            TimeSlotTask.objects.bulk_create(tasks_to_create)

            # 1️⃣1️⃣ Return the new plan
            return Response(plan_json, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)