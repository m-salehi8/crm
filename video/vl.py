import requests
from video.models import *

v = "c67431bcb6158ff79daaa04253e69a4ce7d0f669"
url = "http://it.local/backend/videos/"
all = Video.objects.all()
for a in all:
    url = "http://it.local/backend/videos/" + str(a.pk)
    header = {'Authorization': "token c67431bcb6158ff79daaa04253e69a4ce7d0f669"}

    response = requests.get(url, headers=header)
    print(response.status_code)


