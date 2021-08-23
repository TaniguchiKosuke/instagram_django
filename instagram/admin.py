from django.contrib import admin
from .models import CommentToPost, Posts


@admin.register(Posts)
class PostsAdmin(admin.ModelAdmin):
    list_display = ('get_author', 'post_date',)

    def get_author(self, obj):
        return obj.author
    get_author.short_description = 'Author'


admin.site.register(CommentToPost)