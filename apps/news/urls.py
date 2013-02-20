from django.conf.urls.defaults import *
from . import feeds

default_feeds = {
    'latest': feeds.LatestPosts,
}

urlpatterns = patterns('news.views',
    url(r'^$', 'index', name='news_index'),
    url(r'^add$', 'add', name='news_post_add'),
    url(r'^(?P<slug>[\w-]+)$', 'detail', name='news_post_detail'),
    url(r'^(?P<slug>[\w-]+)/edit$', 'edit', name='news_post_edit'),
    url(r'^(?P<slug>[\w-]+)/preview$', 'preview', name='news_post_preview'),
    url(r'^(?P<slug>[\w-]+)/delete$', 'delete', name='news_post_delete'),
    url(r'^(?P<slug>[\w-]+)/publish$', 'publish', name='news_post_publish'),
    url(r'^(?P<slug>[\w-]+)/recall$', 'recall', name='news_post_recall'),
)
urlpatterns += patterns('django.contrib.syndication.views',
    url(r'^feeds/(?P<url>.*)/$', 'feed', {'feed_dict': default_feeds}, name="news_feeds"),
)
