import os
import tempfile

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from rest_framework import status
from django.db import transaction
from .models import Material, MaterialAccess
from .utils.drive_api import upload_file_to_drive, generate_public_url, delete_file_from_drive
from topic_analysis.analysis_service import analyze_material

class UploadMaterialView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        uploaded_file = request.FILES.get('file')
        subject = request.data.get('subject')  # Get subject from frontend/form

        if not uploaded_file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        if not subject:
            return Response({'error': 'Subject is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            for chunk in uploaded_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        # Upload to Google Drive
        drive_file_id = upload_file_to_drive(tmp_path, uploaded_file.name)
        os.remove(tmp_path)

        if not drive_file_id:
            return Response({'error': 'Google Drive upload failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Generate public URLs
        public_urls = generate_public_url(drive_file_id)
        view_url = public_urls.get('view_url')
        download_url = public_urls.get('download_url')

        # Save to database
        material = Material.objects.create(
            title=uploaded_file.name,
            subject=subject,
            drive_file_id=drive_file_id,
            view_url=view_url,
            download_url=download_url
        )
        MaterialAccess.objects.create(user=request.user, material=material)


        # --- DIRECTLY TRIGGERING ANALYSIS ---
        # WARNING: This will block the request and may cause a timeout on the server.
        # This is NOT recommended for production use. A background task queue
        # like Celery is the appropriate solution.
        print("--- Starting analysis directly after upload... ---")
        analyze_material(material.id)
        print("--- Direct analysis finished. ---")
        # --- END OF DIRECT CALL ---



        return Response({
            'message': 'File uploaded successfully',
            'material_id': material.id,
            'drive_file_id': drive_file_id,
            'subject': subject,
            'view_url': view_url,
            'download_url': download_url
        }, status=status.HTTP_201_CREATED)



class MaterialListView(APIView):
    """
    Provides a list of materials accessible by the currently authenticated user
    by manually creating the JSON structure.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        user_materials = Material.objects.filter(materialaccess__user=user)

        # Manually build the list of dictionaries
        data = []
        for material in user_materials:
            data.append({
                'id': material.id,
                'title': material.title,
                'subject': material.subject,
                'view_url': material.view_url,
            })
        
        return Response(data)



class DeleteMaterialView(APIView):
    """
    Handles DELETE requests to remove a material from Google Drive and the database.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, material_id, *args, **kwargs):
        user = request.user

        try:
            # 1. Find the material
            material = Material.objects.get(id=material_id)

            # 2. Check if the user has access to this material
            if not MaterialAccess.objects.filter(user=user, material=material).exists():
                return Response(
                    {"error": "Forbidden: You do not have access to this material."},
                    status=status.HTTP_403_FORBIDDEN
                )

            drive_id = material.drive_file_id

            # 3. Use a database transaction to ensure data consistency.
            # This means if the Drive delete fails, the database won't be changed.
            with transaction.atomic():
                # 4. Delete the file from Google Drive FIRST.
                if drive_id:
                    try:
                        delete_file_from_drive(drive_id)
                    except Exception as e:
                        # If the drive delete fails, roll back the transaction
                        # and return an error.
                        return Response(
                            {"error": f"Failed to delete file from cloud storage: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )

                # 5. If Drive delete was successful (or no drive_id),
                #    delete the material from the database.
                material.delete()

            # 6. Return a "No Content" response
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Material.DoesNotExist:
            return Response(
                {"error": "Material not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )