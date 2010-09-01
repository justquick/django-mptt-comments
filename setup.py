from setuptools import setup, find_packages

setup(
    name = "django-mptt-comments",
    version = '0.1.6',
    url = 'http://github.com/justquick/django-mptt-comments/',
    author = 'fivethreeo, justquick',
    description = 'Django Mptt Comments is a simple way to display threaded comments instead of the django contrib comments.',
    packages = find_packages(),
    include_package_data=True,
)
