import os
import whisper
from django.conf import settings
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from django.core.files.storage import default_storage


class TranscribeAudioView(GenericAPIView):
    def post(self, request):
        audio_file = request.data['file']
        file_path = default_storage.save(f"temp/{audio_file.name}", audio_file)
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)
        model = whisper.load_model("large-v2")
        result = model.transcribe(audio=full_path, fp16=False, language='fa', temperature=0.0, word_timestamps=True, verbose=True)
        default_storage.delete(file_path)
        return Response({'text': result['text'], 'segments': result['segments']})
