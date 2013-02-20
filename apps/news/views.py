from django.conf import settings
from django.core.urlresolvers import reverse
from django.forms.models import modelform_factory
from django.utils.translation import ugettext_lazy as _
from django.views import generic
from django.views.decorators.csrf import csrf_protect
from utils.django import reverse_lazy
from utils.django.decorators import ajax_only, render_to_json

from . import models

__all__ = [
    'add',
    'delete',
    'detail',
    'edit',
    'index',
    'preview',
    'publish',
    'recall'
]

POSTS_PER_PAGE = getattr(settings, "NEWS_POSTS_PER_PAGE", 10)

PostForm = modelform_factory(models.Post,
    fields=('title', 'teaser', 'content', 'tags'))


class CreatePostView(generic.CreateView):
    model = models.Post
    form_class = PostForm

    def form_valid(self, form):
        from pytils.translit import slugify
        from django.contrib import messages
        self.object = form.save(commit=False)
        self.object.author = self.request.user
        # FIX: get_unique_slug(models.Post, form.cleaned_data["title"])
        self.object.slug = slugify(form.cleaned_data["title"])
        messages.success(self.request, _("News post successfully created."))
        return super(self.__class__, self).form_valid(form)


class UserPostsListView(generic.ListView):
    model = models.Post
    paginate_by = POSTS_PER_PAGE
    template_name = 'news/post_list.html'
    context_object_name = 'post_list'

    def get_queryset(self):
        import vk
        return vk.news.get_posts_for_user(self.request.user,
            'news.index_post')


add = CreatePostView.as_view()
delete = generic.DeleteView.as_view(model=models.Post,
    success_url=reverse_lazy('news_index'))
detail = generic.DetailView.as_view(model=models.Post,
    context_object_name='post',
    queryset=models.Post.objects.published())
edit = generic.UpdateView.as_view(model=models.Post, form_class=PostForm)
index = UserPostsListView.as_view()
preview = generic.DetailView.as_view(model=models.Post,
    context_object_name='post')


@ajax_only
@csrf_protect
@render_to_json
def publish(request, slug, is_published=True):
    """Toggle post published state."""
    from django.shortcuts import get_object_or_404
    post = get_object_or_404(models.Post, slug=slug)
    if post.is_published != is_published:
        post.is_published = is_published
        post.save()
    view_name = ('news_post_publish', 'news_post_recall')[post.is_published]
    return {
        'success': True,
        'new_label': ('Publish', 'Recall')[post.is_published],
        'new_href': reverse(view_name, args=[post.slug]),
    }


@ajax_only
@csrf_protect
@render_to_json
def recall(request, slug):
    return publish(request, slug, False)


from vk.security import permission_required

GET_POST_BY_SLUG = (models.Post, 'slug', 'slug')

add = permission_required('news.add_post')(add)
delete = permission_required('news.delete_post', GET_POST_BY_SLUG)(delete)
edit = permission_required('news.change_post', GET_POST_BY_SLUG)(edit)
preview = permission_required('news.change_post', GET_POST_BY_SLUG)(preview)
publish = permission_required('news.publish_post', GET_POST_BY_SLUG)(publish)
recall = permission_required('news.recall_post', GET_POST_BY_SLUG)(recall)
