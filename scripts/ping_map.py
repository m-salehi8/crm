from core.models import Proclamation, User

#pings = Proclamation.objects.filter(id=479)
#p = Proclamation.objects.all()
#import json
#print(p.count())
#pt = pings.first().type
#for ping in p:
#    if ping.type == pt:
#        print(ping)
#        print("22222222")
#        f = {"user": ping.user.id, "title": ping.title, "body": ping.body, "poster": ping.poster_url, "thumbnail": ping.thumbnail_url, "display_duration": ping.display_duration, }
#       j = json.dumps(f, indent=4, ensure_ascii=False)


import json
from video.models import Video, VideoCategory, VideoCategoryRelation
cat = VideoCategory.objects.get(pk=2)

with open("pings.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for d in data:
    print(d)
    user = User.objects.get(pk=d['user'])
    v= Video()
    v.user = user
    v.title = d['title']
    v.description = d['body']
    v.save()

    vc = VideoCategoryRelation.objects.create(video=v, category=cat)




