import os
import tempfile

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from rest_framework import status

from .models import Material, MaterialAccess
from .utils.drive_api import upload_file_to_drive, generate_public_url
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
