from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from . import models


class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_published', 'date_published', 'author', 'tags')
    list_display_links = ('title',)
    list_filter = ('is_published',)
    prepopulated_fields = {'slug': ('title',)}
    exclude = ('date_published',)
    search_fields = ('author__username', 'author__first_name', 'title', 'content')
    actions = ('publish_posts', 'recall_posts')

    # post publishing actions

    def publish_posts(self, request, queryset):
        """
        Mark select posts as published and set date_published if it does not
        exist.
        """
        count = queryset.publish()
        self.message_user(request, _("%i post(s) published") % count)
    publish_posts.short_description = _("Publish posts")

    def recall_posts(self, request, queryset):
        """
        Recall published posts, but leave date_published as is.
        """
        count = queryset.recall()
        self.message_user(request, _("%i post(s) recalled") % count)
    recall_posts.short_description = _("Recall published posts")


admin.site.register(models.Post, PostAdmin)
