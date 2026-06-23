"""
Public Site management views — CRUD for public website content.
Owner-only for management, AllowAny for the public data endpoint.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from ..models import SiteSettings, WhyChooseUsPoint, PublicService, JobUpdate, EducationApplication
from ..serializers import (
    SiteSettingsSerializer, WhyChooseUsPointSerializer,
    PublicServiceSerializer, JobUpdateSerializer, EducationApplicationSerializer,
)


# ---------------------------------------------------------------------------
# Site Settings (singleton) — GET / PUT
# ---------------------------------------------------------------------------
class SiteSettingsView(APIView):
    """GET/PUT /api/public-site/settings/"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        if request.user.role != 'owner':
            return Response(status=status.HTTP_403_FORBIDDEN)
        settings = SiteSettings.get_settings()
        return Response(SiteSettingsSerializer(settings, context={'request': request}).data)

    def put(self, request):
        if request.user.role != 'owner':
            return Response(status=status.HTTP_403_FORBIDDEN)
        settings = SiteSettings.get_settings()
        serializer = SiteSettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# Why Choose Us Points — list / create / delete
# ---------------------------------------------------------------------------
class WhyChooseUsListCreateView(APIView):
    """GET/POST /api/public-site/why-choose-us/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'owner':
            return Response(status=status.HTTP_403_FORBIDDEN)
        points = WhyChooseUsPoint.objects.all()
        return Response(WhyChooseUsPointSerializer(points, many=True).data)

    def post(self, request):
        if request.user.role != 'owner':
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = WhyChooseUsPointSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class WhyChooseUsDetailView(APIView):
    """PUT/DELETE /api/public-site/why-choose-us/<id>/"""
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        if request.user.role != 'owner':
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            point = WhyChooseUsPoint.objects.get(pk=pk)
            serializer = WhyChooseUsPointSerializer(point, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        except WhyChooseUsPoint.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        if request.user.role != 'owner':
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            point = WhyChooseUsPoint.objects.get(pk=pk)
            point.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except WhyChooseUsPoint.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# Public Services — list / create / update / delete
# ---------------------------------------------------------------------------
class PublicServiceListCreateView(APIView):
    """GET/POST /api/public-site/services/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'owner':
            return Response(status=status.HTTP_403_FORBIDDEN)
        services = PublicService.objects.all()
        return Response(PublicServiceSerializer(services, many=True).data)

    def post(self, request):
        if request.user.role != 'owner':
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = PublicServiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PublicServiceDetailView(APIView):
    """PUT/DELETE /api/public-site/services/<id>/"""
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        if request.user.role != 'owner':
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            service = PublicService.objects.get(pk=pk)
            serializer = PublicServiceSerializer(service, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        except PublicService.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        if request.user.role != 'owner':
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            service = PublicService.objects.get(pk=pk)
            service.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except PublicService.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# Job Updates — list / create / update / delete
# ---------------------------------------------------------------------------
class JobUpdateListCreateView(APIView):
    """GET/POST /api/public-site/jobs/"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        if request.user.role != 'owner':
            return Response(status=status.HTTP_403_FORBIDDEN)
        jobs = JobUpdate.objects.all()
        return Response(JobUpdateSerializer(jobs, many=True).data)

    def post(self, request):
        if request.user.role != 'owner':
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = JobUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class JobUpdateDetailView(APIView):
    """PUT/DELETE /api/public-site/jobs/<id>/"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def put(self, request, pk):
        if request.user.role != 'owner':
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            job = JobUpdate.objects.get(pk=pk)
            serializer = JobUpdateSerializer(job, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        except JobUpdate.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        if request.user.role != 'owner':
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            job = JobUpdate.objects.get(pk=pk)
            job.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except JobUpdate.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# Education Applications — list / create / update / delete
# ---------------------------------------------------------------------------
class EducationApplicationListCreateView(APIView):
    """GET/POST /api/public-site/education/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'owner':
            return Response(status=status.HTTP_403_FORBIDDEN)
        apps = EducationApplication.objects.all()
        return Response(EducationApplicationSerializer(apps, many=True).data)

    def post(self, request):
        if request.user.role != 'owner':
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = EducationApplicationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EducationApplicationDetailView(APIView):
    """PUT/DELETE /api/public-site/education/<id>/"""
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        if request.user.role != 'owner':
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            app = EducationApplication.objects.get(pk=pk)
            serializer = EducationApplicationSerializer(app, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        except EducationApplication.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        if request.user.role != 'owner':
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            app = EducationApplication.objects.get(pk=pk)
            app.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except EducationApplication.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# Public Data Endpoint (for future public website)
# ---------------------------------------------------------------------------
class PublicSiteDataView(APIView):
    """GET /api/public-site/data/ — Returns all public site data (no auth)."""
    permission_classes = [AllowAny]

    def get(self, request):
        settings = SiteSettings.get_settings()
        ctx = {'request': request}
        return Response({
            'settings': SiteSettingsSerializer(settings, context=ctx).data,
            'why_choose_us': WhyChooseUsPointSerializer(
                WhyChooseUsPoint.objects.all(), many=True
            ).data,
            'services': PublicServiceSerializer(
                PublicService.objects.filter(is_active=True), many=True
            ).data,
            'jobs': JobUpdateSerializer(
                JobUpdate.objects.filter(is_active=True), many=True
            ).data,
            'education_apps': EducationApplicationSerializer(
                EducationApplication.objects.filter(is_active=True), many=True
            ).data,
        })
