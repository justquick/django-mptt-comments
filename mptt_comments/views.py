from django import http
from django.conf import settings
from django.contrib.comments.views.utils import next_redirect, confirmation_view
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.html import escape
import mptt_comments
from django.contrib.comments import signals
from django.contrib.comments.models import Comment
from django.utils import datastructures

class CommentPostBadRequest(http.HttpResponseBadRequest):
    """
    Response returned when a comment post is invalid. If ``DEBUG`` is on a
    nice-ish error message will be displayed (for debugging purposes), but in
    production mode a simple opaque 400 page will be displayed.
    """
    def __init__(self, why):
        super(CommentPostBadRequest, self).__init__()
        if settings.DEBUG:
            self.content = render_to_string("comments/400-debug.html", {"why": why})

def post_comment(request, next=None, get_initial_form=None):
    """
    Post a comment.

    HTTP POST is required unless a initial form is requested. If ``POST['submit'] == "preview"`` or if there are
    errors a preview template, ``comments/preview.html``, will be rendered.
    """

    # Require POST
    if request.method != 'POST' and not get_initial_form:
        return http.HttpResponseNotAllowed(["POST"])

    # Fill out some initial data fields from an authenticated user, if present
    data = datastructures.MultiValueDict()
    data.update(request.REQUEST)
    if request.user.is_authenticated():
        if not data.get('name', ''):
            data["name"] = request.user.get_full_name()
        if not data.get('email', ''):
            data["email"] = request.user.email

    # Look up the object we're trying to comment about
    ctype = data.get("content_type")
    object_pk = data.get("object_pk")
    parent_pk = data.get("parent_pk")
    parent_comment = None
    if ctype is None or object_pk is None:
        return CommentPostBadRequest("Missing content_type or object_pk field.")
    try:
        model = models.get_model(*ctype.split(".", 1))
        target = model._default_manager.get(pk=object_pk)
        if parent_pk:
            parent_comment = Comment.objects.get(pk=parent_pk)
    except TypeError:
        return CommentPostBadRequest(
            "Invalid content_type value: %r" % escape(ctype))
    except AttributeError:
        return CommentPostBadRequest(
            "The given content-type %r does not resolve to a valid model." % \
                escape(ctype))
    except Comment.DoesNotExist:
        return CommentPostBadRequest(
            "Parent comment with PK %r does not exist." % \
                escape(parent_pk))
    except ObjectDoesNotExist:
        return CommentPostBadRequest(
            "No object matching content-type %r and object PK %r exists." % \
                (escape(ctype), escape(object_pk)))

    # Do we want to preview the comment?
    preview = data.get("submit", "").lower() == "preview" or \
              data.get("preview", None) is not None

    # Get a initial form with content_type, object_pk and parent_pk filled
    if get_initial_form:
        
        # Construct the initial comment form
        form = mptt_comments.get_form()(target, parent_comment=parent_comment)
        
        template_list = [
            "comments/%s_%s_initial_form.html" % tuple(str(model._meta).split(".")),
            "comments/%s_initial_form.html" % model._meta.app_label,
            "comments/initial_form.html",
        ]
        return render_to_response(
            template_list, {
                "form" : form,
            }, 
            RequestContext(request, {})
        )
        
    # Construct the comment form 
    form = mptt_comments.get_form()(target, parent_comment=parent_comment, data=data)
            
    # Check security information
    if form.security_errors():
        return CommentPostBadRequest(
            "The comment form failed security verification: %s" % \
                escape(str(form.security_errors())))

    # If there are errors or if we requested a preview show the comment
    if form.errors or preview:
        template_list = [
            "comments/%s_%s_preview.html" % tuple(str(model._meta).split(".")),
            "comments/%s_preview.html" % model._meta.app_label,
            "comments/preview.html",
        ]
        return render_to_response(
            template_list, {
                "comment" : form.data.get("comment", ""),
                "form" : form,
            }, 
            RequestContext(request, {})
        )

    # Otherwise create the comment
    comment = form.get_comment_object()
    comment.ip_address = request.META.get("REMOTE_ADDR", None)
    if request.user.is_authenticated():
        comment.user = request.user

    # Signal that the comment is about to be saved
    responses = signals.comment_will_be_posted.send(
        sender  = comment.__class__,
        comment = comment,
        request = request
    )

    for (receiver, response) in responses:
        if response == False:
            return CommentPostBadRequest(
                "comment_will_be_posted receiver %r killed the comment" % receiver.__name__)

    # Save the comment and signal that it was saved
    comment.save()
    signals.comment_was_posted.send(
        sender  = comment.__class__,
        comment = comment,
        request = request
    )

    return next_redirect(data, next, 'comments-comment-done', c=comment._get_pk_val())

comment_done = confirmation_view(
    template = "comments/posted.html",
    doc = """Display a "comment was posted" success page."""
)

def get_comment_tree(request, object_list):

    json_comments = {'end_level': object_list[-1].level, 'end_pk': object_list[-1].pk}
    
    template_list = [
        "comments/display_comments_tree.html",
    ]
    json_comments['html'] = render_to_string(
        template_list, {
            "comments" : object_list
        }, 
        RequestContext(request, {})
    )
    
    return json_comments

def get_comment_offset(request):
    
    offset = int(request.GET.get('offset', 10))
    c_pk = request.GET.get('c_id')
    
    comment = MpttComment.objects.select_related('content_type').get(pk=c_pk)    
    qs = MpttComment.objects.filter(tree_id=tree_id, lft__gte=comment.lft+1)[:offset]
    
    until_toplelvel = []
    remaining = []
    toplevel_reached = False
    for comment in qs:
        if comment.level == 0:
            toplevel_reached = True
        if toplevel_reached:
            remaining.append(comment)
        else:
            until_toplevel.append(comment)
    
    json_data = {'comments_for_update': [], 'comment_tree': {} }
    
    for comment in until_toplevel:    
        json_comment = {'level': comment.level, 'pk': comment.pk}
        template_list = [
            "comments/display_comment.html",
        ]
        json_comment['html'] = render_to_string(
            template_list, {
                "comment" : comment
            }, 
            RequestContext(request, {})
        )
        json_data['comments_for_update'].append(json_comment)
        
    json_data['comment_tree'] = get_comment_tree(request, remaining)
    
    return HttpResponse(simplejson.dumps(json_data), mimetype='text/javascript')
    
        
