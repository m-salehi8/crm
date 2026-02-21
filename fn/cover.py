import os
from django.conf import settings
from django.template.loader import render_to_string
from weasyprint import HTML

from fn.models import InvoiceCover
from rest_framework.response import Response
from rest_framework.views import APIView


def generate_invoice_cover_pdf(cover_id):
    """
    Generate and save Invoice Cover PDF
    Returns saved file path
    """

    cover = InvoiceCover.objects.get(id=cover_id)

    # Render HTML
    html_string = render_to_string(
        'invoice_list.html',
        {'cover': cover}
    )

    # Generate PDF bytes
    pdf_bytes = HTML(string=html_string).write_pdf()

    # Define save path
    pdf_dir = os.path.join(settings.MEDIA_ROOT, 'invoice_covers')
    os.makedirs(pdf_dir, exist_ok=True)

    file_name = f'cover_{cover.id}.pdf'
    file_path = os.path.join(pdf_dir, file_name)

    # Save file
    with open(file_path, 'wb') as f:
        f.write(pdf_bytes)

    return file_path


class CvAPI(APIView):
    def get(self, request):
        generate_invoice_cover_pdf('945')
        return Response({'d': 'd'})