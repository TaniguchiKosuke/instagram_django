from django.contrib import admin
from .models import CommentToPost, Message, Posts, Tag, PostLikes, PostTagRelation


@admin.register(Posts)
class PostsAdmin(admin.ModelAdmin):
    list_display = ('get_author', 'created_at',)

    def get_author(self, obj):
        return obj.author
    get_author.short_description = 'Author'


@admin.register(PostTagRelation)
class PostTagRelationAdmin(admin.ModelAdmin):
    list_display = ('get_post', 'get_tag')

    def get_post(self, obj):
        return obj.post
    get_post.short_description = 'post'

    def get_tag(self, obj):
        return obj.tag
    get_tag.short_description = 'tag'


admin.site.register(CommentToPost)
admin.site.register(Message)
admin.site.register(Tag)
admin.site.register(PostLikes)