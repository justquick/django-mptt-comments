from django.contrib.comments.templatetags.comments import BaseCommentNode, CommentListNode
from django import template
from django.utils.safestring import mark_safe
import mptt_comments

register = template.Library()

class BaseMpttCommentNode(BaseCommentNode):
    
    def __init__(self, ctype=None, object_pk_expr=None, object_expr=None, as_varname=None, comment=None):
        super(BaseMpttCommentNode, self). __init__(ctype=ctype, object_pk_expr=object_pk_expr, object_expr=object_expr, as_varname=as_varname, comment=comment)
        self.comment_model = mptt_comments.get_model()
    
    def get_root_node(self, context):
        ctype, object_pk = self.get_target_ctype_pk(context)
        return self.comment_model.objects.get_root_comment(ctype, object_pk)
        
class MpttCommentFormNode(BaseMpttCommentNode):
    """Insert a form for the comment model into the context."""
            
    def get_form(self, context):
        ctype, object_pk = self.get_target_ctype_pk(context)
        if object_pk:
            return mptt_comments.get_form()(ctype.get_object_for_this_type(pk=object_pk), parent_comment=self.get_root_node(context))
        else:
            return None

    def render(self, context):
        context[self.as_varname] = self.get_form(context)
        return ''

class MpttCommentListNode(BaseMpttCommentNode):
    

    def get_query_set(self, context):
        qs = super(MpttCommentListNode, self).get_query_set(context)
        root_node = self.get_root_node(context)
        return qs.filter(tree_id=root_node.tree_id, level__gte=1, level__lte=3).order_by('tree_id', 'lft')[:50]
        
    def get_context_value_from_queryset(self, context, qs):
        return list(qs)    
        
def get_mptt_comment_list(parser, token):
    """
    Gets the list of comments for the given params and populates the template
    context with a variable containing that value, whose name is defined by the
    'as' clause.

    Syntax::

        {% get_comment_list for [object] as [varname]  %}
        {% get_comment_list for [app].[model] [object_id] as [varname]  %}

    Example usage::

        {% get_comment_list for event as comment_list %}
        {% for comment in comment_list %}
            ...
        {% endfor %}

    """
    return MpttCommentListNode.handle_token(parser, token)


def get_mptt_comment_form(parser, token):
    """
    Get a (new) form object to post a new comment.

    Syntax::

        {% get_comment_form for [object] as [varname] %}
        {% get_comment_form for [app].[model] [object_id] as [varname] %}
    """
    return MpttCommentFormNode.handle_token(parser, token)


def mptt_comment_form_target():
    """
    Get the target URL for the comment form.

    Example::

        <form action="{% comment_form_target %}" method="POST">
    """
    return mptt_comments.get_form_target()

def children_count(comment):
    return (comment.rght - comment.lft) / 2

def mptt_comments_media():
    jquery = '<script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.2.6/jquery.min.js"></script>'
    jscode = '''
    <script type="text/javascript">
    
    var comments = {}
    $(document).ready(function(){
            
        $('.comment_reply').each(function() {
            var post_data = comments[this.id]
            var reply_link = $(this)
            $(this).bind("click", function(e) {
                $('.comment form').remove()
                $.post('/comments/initial_form/', post_data, function(data, textStatus){
                    var parent = reply_link.parent()
                    parent.after(data)
                }, "html")
            })
        })
    })
    </script>
    '''
    css = '''
    <style type="text/css">
        .comment_reply { text-decoration: underline; cursor: hand; }
        .comment { margin-left: 0.5em; padding-left: 0.5em; border-left: solid 4px #dddddd; }
    </style>
    '''
    return mark_safe(u'%s%s%s' % (jquery, jscode, css))
    
register.filter(children_count)
register.tag(get_mptt_comment_form)
register.simple_tag(mptt_comment_form_target)
register.simple_tag(mptt_comments_media)
register.tag(get_mptt_comment_list)
