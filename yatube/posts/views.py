from django.shortcuts import redirect, render, get_object_or_404
from .models import Post, Group, Follow
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required

User = get_user_model()
SELECT_LIMIT = 10  # лимит количества записей на странице


def paginator(request, posts):
    paginator = Paginator(posts, SELECT_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


def index(request):
    # Главная страница
    post_list = Post.objects.select_related('author', 'group').all()
    page_obj = paginator(request, post_list)
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    # Страница сообществ
    group = get_object_or_404(Group, slug=slug)
    group_list = group.posts.select_related('author', 'group').all()
    page_obj = paginator(request, group_list)
    title = str(group)
    context = {
        'group': group,
        'page_obj': page_obj,
        'title': title
    }
    template = 'posts/group_list.html'
    return render(request, template, context)


def profile(request, username):
    # Профиль пользователя
    is_profile = True
    author = get_object_or_404(User, username=username)
    user = request.user
    post_list = Post.objects.filter(author=author).select_related(
        'group',
        'author',
    )
    count = post_list.count()
    page_obj = paginator(request, post_list)
    following = (
        author.following.filter(user_id=user.id)
    ).exists()
    context = {
        'page_obj': page_obj,
        'author': author,
        'count': count,
        'is_profile': is_profile,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    # Старица поста
    post = get_object_or_404(
        Post.objects.select_related('author', 'group'),
        pk=post_id
    )
    count = post.author.posts.count()
    comments = post.comments.select_related('author', 'post').all()
    form = CommentForm()
    context = {
        'post': post,
        'count': count,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    # Страница создания поста
    if request.method == 'POST':
        form = PostForm(request.POST or None,
                        files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', post.author)
        return render(request, 'posts/create_post.html', {"form": form})
    form = PostForm()
    return render(request, 'posts/create_post.html', {"form": form})


@login_required
def post_edit(request, post_id):
    # Страница редактирования поста.
    is_edit = True
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post.id)
    if request.method == "POST":
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
            instance=post
        )
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post.id)
        return render(request, 'posts/create_post.html', {"form": form})
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    context = {
        'form': form,
        'post': post,
        'is_edit': is_edit
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.select_related('author', 'group').filter(
        author__following__user=request.user)
    page_obj = paginator(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:follow_index')
