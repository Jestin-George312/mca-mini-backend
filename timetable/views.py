import os
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
import google.generativeai as genai

from materials.models import Material
from .models import StudyPlanRequest, StudyPlan, DailyTask

# --- Gemini API Setup ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("⚠️ Warning: GEMINI_API_KEY not set.")
else:
    genai.configure(api_key=GEMINI_API_KEY)


# ✅ NEW VIEW TO FETCH THE PLAN
class StudyPlanDetailView(APIView):
    """
    Retrieves the latest study plan for the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            # Find the latest study plan for the logged-in user
            study_plan = StudyPlan.objects.filter(
                request__user=request.user
            ).order_by('-created_at').first()

            if not study_plan:
                return Response(
                    {"message": "No study plan found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Serialize the daily tasks into the required format
            tasks = study_plan.daily_tasks.all().order_by('day')
            tasks_data = [
                {
                    "day": task.day,
                    "focus_subject": task.focus_subject,
                    "topics": task.topics,
                    "notes": task.notes,
                }
                for task in tasks
            ]

            response_data = {"study_plan": tasks_data}
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ✅ GENERATE STUDY PLAN VIEW
class GenerateStudyPlanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            # 1️⃣ Get input data
            data = request.data
            material_ids = data.get("material_ids")
            total_days = int(data.get("totalDays", 7))
            hours_per_day = int(data.get("hoursPerDay", 2))

            if not material_ids:
                return Response(
                    {"error": "No study materials selected."},
                    status=400
                )

            # 2️⃣ Fetch materials
            materials = Material.objects.filter(id__in=material_ids)
            if not materials.exists():
                return Response(
                    {"error": "Selected materials not found."},
                    status=404
                )

            # Prepare subject list for prompt
            subjects_str = "\n".join(
                [f"- {m.title} ({m.subject})" for m in materials]
            )

            # 3️⃣ Build prompt for Gemini
            prompt = f"""
You are an expert academic planner and time management coach.

Create a personalized {total_days}-day study plan for a student who studies {hours_per_day} hours per day.

The student has uploaded the following study materials:
{subjects_str}

Distribute all the provided subjects and materials evenly across {total_days} days. 
Each day should include multiple time slots (for example, 8:00 AM–10:00 AM, 10:30 AM–12:30 PM, etc.) 
based on the total available study hours per day. 

Ensure every subject mentioned above is included in the plan, proportionally and realistically. 
Include revision and practice sessions near the end. 
Each day should also include a short motivational or productivity note.

**Output strictly in JSON (no markdown, no explanations):**
{{
  "study_plan": [
    {{
      "day": 1,
      "schedule": [
        {{
          "time": "8:00 AM - 10:00 AM",
          "subject": "Name of one subject from the list",
          "topics": "Specific topics or chapters from that material"
        }},
        {{
          "time": "10:30 AM - 12:30 PM",
          "subject": "Another subject from the list",
          "topics": "Next set of topics or sections"
        }}
      ],
      "notes": "Motivational or productivity tip for the day"
    }},
    ...
  ]
}}
Ensure the subjects and topics match only the materials listed above. 
Do not invent unrelated subjects. 
Return valid JSON only — no markdown, explanations, or extra text.
"""

            prompt_nill = f"""
You are an expert academic planner. Create a detailed {total_days}-day study plan 
for a student who studies {hours_per_day} hours per day.

Materials to cover:
{subjects_str}

**Output JSON format (no markdown, no explanations):**
{{
  "study_plan": [
    {{
      "day": 1,
      "focus_subject": "Subject Name",
      "topics": "List of topics or chapters",
      "notes": "Short motivational or productivity tip"
    }},
    ...
  ]
}}
"""

            # 4️⃣ Call Gemini API
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            result_text = (
                response.text.strip()
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )

            # 5️⃣ Parse JSON
            plan_json = json.loads(result_text)

            # 6️⃣ Save request and plan
            plan_request = StudyPlanRequest.objects.create(
                user=request.user,
                total_days=total_days,
                hours_per_day=hours_per_day
            )
            plan_request.materials.set(materials)

            study_plan = StudyPlan.objects.create(request=plan_request)

            tasks = [
                DailyTask(
                    study_plan=study_plan,
                    day=item.get("day"),
                    focus_subject=item.get("focus_subject"),
                    topics=item.get("topics"),
                    notes=item.get("notes", "")
                )
                for item in plan_json.get("study_plan", [])
            ]
            DailyTask.objects.bulk_create(tasks)

            return Response(plan_json, status=200)

        except json.JSONDecodeError:
            return Response({"error": "Invalid JSON from Gemini."}, status=500)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
