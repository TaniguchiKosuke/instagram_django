from django.contrib import admin
from .models import CommentToPost, Message, Posts, Tag, PostLikes


@admin.register(Posts)
class PostsAdmin(admin.ModelAdmin):
    list_display = ('get_author', 'created_at',)

    def get_author(self, obj):
        return obj.author
    get_author.short_description = 'Author'


admin.site.register(CommentToPost)
admin.site.register(Message)
admin.site.register(Tag)
admin.site.register(PostLikes)