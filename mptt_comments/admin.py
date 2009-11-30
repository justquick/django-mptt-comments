from django.contrib import admin
from django.conf import settings
from mptt_comments.models import MpttComment
from django.utils.translation import ugettext_lazy as _
from django.contrib.comments.models import Comment

class MpttCommentsAdmin(admin.ModelAdmin):
    fieldsets = (
        (None,
           {'fields': ('content_type', 'object_pk', 'parent', 'site')}
        ),
        (_('Content'),
           {'fields': ('user', 'user_name', 'user_email', 'user_url', 'title', 'comment')}
        ),
        (_('Metadata'),
           {'fields': ('submit_date', 'ip_address', 'is_public', 'is_removed')}
        )
     )

    list_display = ('name', 'content_type', 'object_pk', 'ip_address', 'comment', 'submit_date', 'is_public')
    list_filter = ('submit_date', 'parent', 'site', 'is_public', 'is_removed')
    date_hierarchy = 'submit_date'
    ordering = ('-submit_date',)
    search_fields = ('comment', 'user__username', 'user_name', 'user_email', 'user_url', 'ip_address')

    def queryset(self, request):
        return MpttComment.objects.filter(parent__isnull=False)

admin.site.unregister(Comment)
admin.site.register(MpttComment, MpttCommentsAdmin)