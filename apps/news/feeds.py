from django.conf import settings
from django.contrib.syndication.feeds import Feed
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from . import models

RECENT_NEWS_POSTS_COUNT = getattr(settings, "RECENT_NEWS_POSTS_COUNT", 10)
ITEMS_PER_FEED = getattr(settings, 'NEWS_ITEMS_PER_FEED', 10)
FEED_TTL = getattr(settings, 'NEWS_FEED_TTL', 120)


class NewsFeed(Feed):
    description_template = 'news/feed_post_description.html'

    def link(self):
        return reverse('news_index')

    def ttl(self):
        return str(FEED_TTL)


class LatestPosts(NewsFeed):
    title = _("Latest news posts")
    description = title

    def items(self):
        return models.Post.objects.published()[:ITEMS_PER_FEED]

    def item_author_name(self, post):
        if post.author:
            return post.author.get_full_name()
        return _("Anonymous")

    def item_pubdate(self, post):
        return post.date_published
