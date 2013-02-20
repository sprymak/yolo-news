import datetime
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db import models
from django.utils.translation import ugettext, ugettext_lazy as _
from markupfield.fields import MarkupField
from tagging.fields import TagField

import utils


DEFAULT_MARKUP = getattr(settings, "NEWS_DEFAULT_MARKUP", "markdown")

# it should be enough to hold UUID hash
MAX_UID_LENGTH = max(getattr(settings, 'MAX_UID_LENGTH', 0), 36)


class Operations:
    ADD_POST = 'news.add_post'
    CHANGE_POST = 'news.change_post'
    DELETE_POST = 'news.delete_post'
    GET_DRAFT_POST = 'news.get_draft_post'
    GET_POST = 'news.get_post'
    INDEX_POST = 'news.index_post'
    PUBLISH_POST = 'news.publish_post'
    REVOKE_POST = 'news.revoke_post'


class Roles:
    READER = 'news.reader'
    AUTHOR = 'news.author'
    MODERATOR = 'news.moderator'


class PostQuerySet(models.query.QuerySet):

    def publish(self):
        now = datetime.datetime.now()
        # force update permissions for posts with date_published set
        rs = self.filter(date_published__isnull=False)
        count = rs.update(is_published=True)
        [p.publish() for p in rs]
        # update permissions and date for posts with empty date_published
        rs = self.filter(date_published__isnull=True)
        count += rs.update(is_published=True, date_published=now)
        [p.publish() for p in rs]
        return count

    def recall(self):
        count = self.update(is_published=False)
        [p.recall() for p in self]
        return count


class PostManager(models.Manager):
    use_for_related_fields = True

    def published(self):
        return Post.objects.filter(is_published=True)

    def get_query_set(self):
        return PostQuerySet(self.model)


class Post(models.Model):
    uid = models.CharField(max_length=MAX_UID_LENGTH, unique=True,
        default=lambda: utils.get_unique_id_str(Post.is_key_unique))
    site = models.ForeignKey(Site, editable=False, default=settings.SITE_ID,
        verbose_name=_('Site'))
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    slug = models.SlugField(max_length=64, db_index=True,
        verbose_name=_('Slug'))
    author = models.ForeignKey(User, related_name='news',
        verbose_name=_('Author'))
    content = MarkupField(default_markup_type=DEFAULT_MARKUP,
        verbose_name=_('Content'))
    teaser = MarkupField(markup_type='plain', blank=True, null=True,
        verbose_name=_('Teaser'))
    date_created = models.DateTimeField(auto_now_add=True,
        verbose_name=_('Date Created'))
    date_updated = models.DateTimeField(auto_now=True, auto_now_add=True,
        verbose_name=_('Date Modified'))
    date_published = models.DateTimeField(blank=True, null=True,
        verbose_name=_('Date Published'))
    is_published = models.BooleanField(default=False,
        verbose_name=_('Published'))
    tags = TagField(verbose_name=_('Tags'))

    objects = PostManager()

    class Security:
        roles = (
            (Roles.READER, ugettext("Can read posts only")),
            (Roles.AUTHOR, ugettext("Can add, change, delete and recall post. "
                    "Can not publish posts")),
            (Roles.MODERATOR, ugettext("News moderator. Can publish posts")),
        )
        permissions = (
            ('add_post', [Roles.AUTHOR]),
            ('change_post', [Roles.AUTHOR, Roles.MODERATOR]),
            ('delete_post', [Roles.AUTHOR, Roles.MODERATOR]),
            ('get_draft_post', [Roles.AUTHOR, Roles.MODERATOR]),
            ('get_post', [Roles.AUTHOR, Roles.MODERATOR, Roles.READER]),
            ('index_post', [Roles.AUTHOR, Roles.MODERATOR, Roles.READER]),
            ('publish_post', [Roles.MODERATOR]),
            ('revoke_post', [Roles.AUTHOR, Roles.MODERATOR]),
        )

    class Meta:
        ordering = ['-date_published', '-date_created']
        permissions = (
            # extend ['add_post', 'change_post', 'delete_post']
            ("index_post", ugettext("Can list post")),
            ("get_post", ugettext("Can get post")),
            ("get_draft_post", ugettext("Can get not published post")),
            ("publish_post", ugettext("Can publish post")),
            ("revoke_post", ugettext("Can revoke post")),
        )
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')

    def __unicode__(self):
        return self.title

    @classmethod
    def is_key_unique(cls, uid):
        return utils.django.get_object_or_none(cls, uid=uid) is None

    @models.permalink
    def get_absolute_url(self):
        view_names = ('news_post_preview', 'news_post_detail')
        return (view_names[self.is_published], (), {'slug': self.slug})

    def save(self, **kwargs):
        self.teaser.markup_type = self.content.markup_type
        if self.is_published and not self.date_published:
            self.date_published = datetime.datetime.now()
        super(Post, self).save(**kwargs)

    def publish(self):
        self.is_published = True
        self.save()
        # TODO(sprymak): get rid of external dependencies
        # we must assign permissions to ANONYMOUS explicitly while there is no
        # way to assign roles to Anonymous user on system-wide level
        # (AnonymousHasNewsReaderRole test should pass).
        import vk
        vk.security.grant_permission(Operations.INDEX_POST,
            [Roles.READER, vk.security.Roles.ANONYMOUS], self)
        vk.security.grant_permission(Operations.GET_POST,
            [Roles.READER, vk.security.Roles.ANONYMOUS], self)

    def recall(self):
        self.is_published = False
        self.save()
        import vk
        vk.security.revoke_permission(Operations.INDEX_POST,
            [Roles.READER, vk.security.Roles.ANONYMOUS], self)
        vk.security.revoke_permission(Operations.GET_POST,
            [Roles.READER, vk.security.Roles.ANONYMOUS], self)


def _news_post_post_save(sender, instance, created, **kwargs):
    import vk
    vk.security.assign_roles(Roles.AUTHOR, instance.author, instance)
    vk.security.grant_permission(Operations.INDEX_POST,
        [Roles.AUTHOR, Roles.MODERATOR], instance)

models.signals.post_save.connect(_news_post_post_save, sender=Post)
