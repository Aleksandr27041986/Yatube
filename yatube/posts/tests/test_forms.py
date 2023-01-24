import shutil
import tempfile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from posts.forms import PostForm
from posts.models import Post, Group, Comment


User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.TEST_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='Группа',
            slug='slug',
            description='Описание группы',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Первоначальный текс',
            group=cls.group
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        self.authurized_client = Client()
        self.authurized_client.force_login(self.user)

    def test_create_post(self):
        """
        При отправке валидной формы на странице нового поста,
        количество записей в БД увеличивается, создаётся пост с указанными
        значениями, происходит переадресация на страницу профиля автора.
        """
        # создаём байт-последовательность картинки
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Созданный пост',
            'author': self.user,
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authurized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        redirect_url = reverse('posts:profile', kwargs={'username': self.user})
        self.assertRedirects(response, redirect_url)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(
            text='Созданный пост',
            image='posts/small.gif'
        ).exists())

    def test_edit_post(self):
        """
        При отправке валидной формы на странице редактирования
        поста(созданного в SetUp) запись в БД обновляется и
        происходит переадресация на страницу поста.
        """
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Изменённый текст',
            'author': self.user,
            'group': self.group.id
        }
        response = self.authurized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        redirect_url = reverse('posts:post_detail',
                               kwargs={'post_id': self.post.id})
        self.assertRedirects(response, redirect_url)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(Post.objects.filter(text=form_data['text']).exists())

    def test_comment_to_post(self):
        """
        При отправке авторизованным пользователем валидной формы комментария
        к посту(созданному в SetUp), создаётся запись в БД и комментарий
        появляется на странице поста.
        """
        url = reverse('posts:add_comment', kwargs={'post_id': self.post.id})
        redirect_url = reverse('posts:post_detail',
                               kwargs={'post_id': self.post.id})
        form_data = {
            'post': self.post.id,
            'author': self.user,
            'text': 'Комментарий к посту',
        }
        comments_count = Comment.objects.filter(post=self.post.id).count()
        response = self.authurized_client.post(
            url,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, redirect_url)
        self.assertEqual(Comment.objects.filter(post=self.post.id).count(),
                         comments_count + 1)
        self.assertTrue(Comment.objects.filter(
            text='Комментарий к посту',
        ).exists())
        self.assertTrue(Post.objects.filter(
            comments__text='Комментарий к посту'
        ))
