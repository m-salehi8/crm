import jdatetime
from .models import Work
from core.models import Key
from core.models import User
from rest_framework import status
from core.permissions import IsHrAdmin
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView

# RahkaranConnectionString = 'Driver={SQL Server};Server=172.30.230.66;Database=majazi_sg3;uid=pbi;pwd=>An[8w,=TS03'
RahkaranConnectionString = 'Driver={ODBC Driver 18 for SQL Server};Server=172.30.230.66;Database=majazi_sg3;uid=pbi;pwd=>An[8w,=TS03'


class UpdateProfiles(GenericAPIView):
    permission_classes = [IsHrAdmin]

    def get(self, request):

        return Response(data='results')


class UpdateWorks(GenericAPIView):
    permission_classes = [IsHrAdmin]

    def get(self, request):
        return Response(data='results')
