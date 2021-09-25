# Generated by Django 3.2.5 on 2021-09-25 10:29

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('instagram', '0002_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PostCommentRelation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('comment_to_comment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='instagram.commenttocomment')),
                ('comment_to_post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='instagram.commenttopost')),
            ],
            options={
                'unique_together': {('comment_to_comment', 'comment_to_post')},
            },
        ),
    ]
