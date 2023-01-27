from django.urls import reverse
from posts.models import Post, Group

_counter_post = 0
_counter_group = 0


def unique_string(is_post, prefix=""):
    if is_post:
        global _counter_post
        _counter_post += 1
        return prefix + str(_counter_post)
    else:
        global _counter_group
        _counter_group += 1
        return prefix + str(_counter_group)


def post_create(user, group, image=None):
    is_post = True
    text = unique_string(is_post, 'post')
    return Post.objects.create(
        text=text,
        author=user,
        group=group,
        image=image
    )


def group_create():
    is_post = False
    title = unique_string(is_post, 'Группа')
    slug = unique_string(is_post, 'slug')
    description = unique_string(is_post, 'Описание группы')
    return Group.objects.create(
        title=title,
        slug=slug,
        description=description
    )


def url_rev(url, **args):
    return reverse(url, args=args)


def clean_counter():
    global _counter_group, _counter_post
    _counter_post = 0
    _counter_group = 0
