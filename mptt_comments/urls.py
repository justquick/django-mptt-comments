from django.conf.urls.defaults import *
from django.contrib.comments.urls import urlpatterns as contrib_comments_urlpatterns
from django.conf import settings

urlpatterns = patterns('mptt_comments.views',
    url(r'^initial_form/$',
        'post_comment',
        kwargs={'get_initial_form': True},
        name='comments-initial_form'
    ),
    url(r'^post/$',
        'post_comment',
        name='comments-post-comment'
    )
)

urlpatterns += contrib_comments_urlpatterns
