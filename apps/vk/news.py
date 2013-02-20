from django.conf import settings
from utils.django import get_object_or_none
from apps.news import models

from . import security

__all__ = [
    'RECENT_NEWS_POSTS_COUNT',
    'create_post',
    'delete_post',
    'get_latest_published',
    'get_post_by_id',
    'get_post_data',
    'get_posts_for_user',
    'make_post_data',
    'save_post',
    'update_post',
]


RECENT_NEWS_POSTS_COUNT = getattr(settings, 'RECENT_NEWS_POSTS_COUNT', 10)


def make_post_data(**data):
    """ Construct the composite Transfer Object for ``Post`` model class
        and fill its fields with data passed in arguments.

        Fields not presented in ``Post`` class will be ignored.
    """
    from utils.django import make_model_dto
    return make_model_dto(models.Post, **data)


def get_post_data(val):
    """ Construct the composite Transfer Object for ``Post`` model object.

        :param val: ``Post`` object instance or primary key
    """
    post = val
    if isinstance(post, (int, long, basestring)):
        post = get_object_or_none(models.Post, pk=post)
    from utils.django import get_object_dto
    return get_object_dto(post)


def get_post_by_id(val):
    """ Get news post by its id. """
    if isinstance(val, (int, long, basestring)):
        return get_object_or_none(models.Post, pk=val)


def update_post(val, data):
    """ Update existing ``Post`` object with data passed in Transfer Object and
        validate instance values.
        This function does not call ``save`` method on the object.

        :param val: ``Post`` object instance or primary key
    """
    from utils.django import update_object_from_dto
    post = val
    if isinstance(post, (int, long, basestring)):
        post = get_object_or_none(models.Post, pk=post)
    if isinstance(post, models.Post):
        update_object_from_dto(post, data, partial=True)
        # TODO(sprymak): validate new instance values
        return post


def create_post(data=None):
    """ Create new ``Post`` object with data passed in `data` argument.
        This function does not call ``save`` method on resulting object.

        :param data: data transfer object for ``Post`` object
    """
    if data is None:
        data = make_post_data()
    instance = models.Post()
    return update_post(instance, data)


def save_post(val):
    """ Save ``Post`` object and all its' descendants. Update cache and
        permissions if necessary.
    """
    if isinstance(val, models.Post):
        val.save()
    return val


def delete_post(val):
    """ Delete news post.

        :param val: ``Post`` object instance or primary key
    """
    post = val
    if isinstance(post, (int, long, basestring)):
        post = get_object_or_none(models.Post, pk=post)
    if isinstance(post, models.Post):
        post.delete()


def publish_post(val):
    """ Publish news post.
        Note: ``save`` method will be called first if post has not been
            saved yet.
        :param val: ``Post`` object instance or primary key
    """
    post = val
    if isinstance(post, (int, long, basestring)):
        post = get_object_or_none(models.Post, pk=post)
    if isinstance(post, models.Post):
        post.publish()


def recall_post(val):
    """ Recall published news post.
        Note: ``save`` method will be called first if post has not been
            saved yet.
        :param val: ``Post`` object instance or primary key
    """
    post = val
    if isinstance(post, (int, long, basestring)):
        post = get_object_or_none(models.Post, pk=post)
    if isinstance(post, models.Post):
        post.recall()


def get_latest_published(user, count=None):
    """ Get recently published news posts indexable by user.

        :param user: user id or User object.
        :param count: maximum number of posts to return. Defaults to
          ``django.conf.settings.RECENT_NEWS_POSTS_COUNT``.
    """
    if not count:
        count = RECENT_NEWS_POSTS_COUNT
    operation = models.Operations.INDEX_POST
    qs = models.Post.objects.published()
    return [post for post in qs if security.has_permissions(post, operation,
        security.get_user_roles(user, post))][:count]


def get_posts_for_user(user, operation=None):
    """ Get news posts indexable by user (including not published).

        :param user: user id or User object.
        :param operation: required permission. Defaults to 'news.get_post'
    """
    if not operation:
        operation = models.Operations.INDEX_POST

    qs = models.Post.objects.all()
    return [post for post in qs if security.has_permissions(post, operation,
        security.get_user_roles(user, post))]
