====================
Django Mptt Comments
====================

Django Mptt Comments is a simple way to display threaded comments instead of the django contrib comments.
Currently, there is only support for openlayers with a google baselayer, but should be easy to extend.

If you have ideas for this app tell me or make a fork.

Installation
============

#. Add the `mptt_comments` directory to your Python path.

#. Add `mptt_comments` to INSTALLED_APPS

#. Add the required code to the objects detail page

#. Copy the templates to adapt them for your site

#. Style the forms using css

Usage
=====

In any detail template that wants to use `mptt_comments` ::
        
        {% block extrahead %}
        
        {% load mptt_comments_tags %}
        {% get_mptt_comments_media %}
        
        {% endblock extrahead %}

To display the tree in templates: ::


        {% load comments %}
        {% load mptt_comments_tags %}    
            
        {% get_mptt_comment_list for object as comments %}
        
        {% if comments %}<h2>Comments</h2>{% endif %}
        
        {% include "comments/display_comments_tree.html" %}    
            
        <h2>Post a comment</h2>
        
        {% get_mptt_comment_form for object as form %}
        <form action="{% comment_form_target %}" method="POST">
            <fieldset>
                <ol>
                {% for field in form %}
                    {% if not field.is_hidden %}
                    <li class="{% if not field.field.required %}not{% endif %}required{% if field.errors %} errors{% endif %}{% ifequal field.name "honeypot" %} hidden{% endifequal %}">
                        {{ field.label_tag }}
                        {{ field }}
                        {{ field.errors }}
                    </li>
                    {% endif %}
                {% endfor %}
                    {% if form.non_field_errors %}
                    <li class="errors">{{ form.non_field_errors }}</li>
                    {% endif %}
                    <li>
                    {% for field in form %}
                        {% if field.is_hidden %}
                            {{ field }}
                        {% endif %}
                    {% endfor %}
                    <input type="submit" name="preview" value="Preview" />
                    <input type="reset" />
                    </li>
                </ol>
            </fieldset>
        </form>
        

TODO
====
- Make restful views work more seamless
- Add slashdot style pagination