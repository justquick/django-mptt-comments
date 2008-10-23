from django.core import urlresolvers

def get_model():
    from mptt_comments.models import MpttComment
    return MpttComment

def get_form():
    from mptt_comments.forms import MpttCommentForm
    return MpttCommentForm

def get_form_target():
    return urlresolvers.reverse("mptt_comments.views.post_comment")
