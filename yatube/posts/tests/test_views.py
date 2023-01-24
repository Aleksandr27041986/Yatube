import shutil
import tempfile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django import forms
from posts.forms import PostForm

from posts.models import Post, Group, Follow

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.TEST_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='автор')
        cls.user_2 = User.objects.create_user(username='пользователь')
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Просто группа',
            slug='prosto-slug',
            description='Описание просто группы',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Новый пост',
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_2)
        self.author = Client()
        self.author.force_login(self.user)
        self.user_unfollowed = User.objects.create_user(username='Безподписки')
        self.unfollowed_client = Client()
        self.unfollowed_client.force_login(self.user_unfollowed)
        self.group_2 = Group.objects.create(
            title='Вторая группа',
            slug='slug_2',
            description='Группа без постов',
        )
        self.guest_client = Client()

    def comparing_responsed_and_expected_quantity(self, client, url, quantity):
        """Функция сравнения количество постов из запроса с ожидаемым
        количеством"""
        response = client.get(url)
        self.assertEqual(len(response.context['page_obj']), quantity)

    def test_index_group_list_profile_page_contains_post_group_author(self):
        """
        На главной странице, на странице группы и на странице профиля автора
        пользователь увидет пост (созданный в setUp) содержащий информацию
        о тексте поста, группе, картинке и авторе поста.
        """
        reverses_names = [
            reverse('posts:index'),
            reverse('posts:group_list', args=(self.post.group.slug,)),
            reverse('posts:profile', kwargs={'username': self.user}),
        ]
        for reverse_name in reverses_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.author.get(reverse_name)
                post = response.context['page_obj'][0]
                self.assertEqual(post.author.username, 'автор')
                self.assertEqual(post.text, 'Новый пост')
                self.assertEqual(post.group.title, 'Просто группа')
                self.assertEqual(post.image, 'posts/small.gif')

    def test_post_detail_page_contains_post_group_author(self):
        """
        На странице поста пользователь увидит пост (созданный в `setUp`),
        содержащий информацию о тексте поста, группе, картинке
        и авторе поста.
        """
        url = reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        response = self.authorized_client.get(url)
        post = response.context.get('post')
        self.assertEqual(post.author.username, 'автор')
        self.assertEqual(post.text, 'Новый пост')
        self.assertEqual(post.group.title, 'Просто группа')
        self.assertEqual(post.image, 'posts/small.gif')

    def create_post_contains_fields_required_type(self, response):
        """
        Функция для сравнивания типа полей формы на указанной странице
        с заданным типом полей для формы PostFrom.
        """
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_edit_and_create_page_contains_fields_required_type(self):
        """
        На страницу создания и редактирования поста передаётся форма
        с типом полей соответствующих форме PostForm.
        """
        reverse_pages_name = [
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            reverse('posts:post_create')
        ]
        # Перебираем страницы создания и редактирования поста в цикле,
        # вызывая функцию для сравнивания типов полей формы.
        for reverse_name in reverse_pages_name:
            with self.subTest(reverse_name=reverse_name):
                response = self.author.get(reverse_name)
                self.create_post_contains_fields_required_type(response)
                self.assertIsInstance(response.context['form'], PostForm)

    def test_created_post_add_to_desired_group(self):
        """
        Создав пост (см `setUp`), увидем его на главной странице,
        на странице профиля автора, а также в группе, которая указана
        при создании, во второй группе посты отсутствуют.
        """
        # задаём словарь страницу профиля, главной, а также двух групп,
        # где в одной присутствует пост, в другой постов нет.
        responses_list = {
            reverse('posts:group_list', kwargs={'slug': self.group.slug}): 1,
            reverse('posts:group_list', kwargs={'slug': self.group_2.slug}): 0,
            reverse('posts:index'): 1,
            reverse('posts:profile', kwargs={'username': self.user}): 1,
        }
        for reverse_name, quentity_post in responses_list.items():
            with self.subTest(reverse_name=reverse_name):
                self.comparing_responsed_and_expected_quantity(
                    self.author,
                    reverse_name,
                    quentity_post
                )

    def test_follow_creation_and_deletion(self):
        """
        Авторизованный пользователь может подписываться на других
        пользователей и удалять их из подписок.
        """
        create_url = reverse('posts:profile_follow',
                             kwargs={'username': self.post.author})
        delete_url = reverse('posts:profile_unfollow',
                             kwargs={'username': self.post.author})
        # проверяем наличие фолловера автора после подписки,
        # и отсутствие после отписки
        self.authorized_client.get(create_url)
        self.assertTrue(
            User.objects.filter(follower__author__username='автор')
        )
        self.authorized_client.get(delete_url)
        self.assertFalse(
            User.objects.filter(follower__author__username='автор')
        )

    def test_new_post_add_in_follower_page(self):
        """
        Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех,
        кто не подписан.
        """
        url = reverse('posts:follow_index')
        Follow.objects.create(user=self.user_2, author=self.post.author)
        user_with_fol = self.authorized_client
        user_unfol = self.unfollowed_client
        # сравниваем количество до добавления нового поста
        self.comparing_responsed_and_expected_quantity(user_with_fol, url, 1)
        self.comparing_responsed_and_expected_quantity(user_unfol, url, 0)
        Post.objects.create(
            author=self.user,
            text='Второй пост',
            group=self.group,
        )
        # сравниваем количество записей после добавления нового поста
        self.comparing_responsed_and_expected_quantity(user_with_fol, url, 2)
        self.comparing_responsed_and_expected_quantity(user_unfol, url, 0)
        response = self.authorized_client.get(url)
        post = response.context['page_obj'][0]
        self.assertEqual(post.text, 'Второй пост')

    def test_follow_page_contains_post_group_author(self):
        """"
        Пользователь после подписки на автора видит в избранном информацию
        о тексте поста, группе, картинке и авторе поста.
        """
        create_url = reverse('posts:profile_follow',
                             kwargs={'username': self.post.author})
        self.authorized_client.get(create_url)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        post = response.context['page_obj'][0]
        self.assertEqual(post.author.username, 'автор')
        self.assertEqual(post.text, 'Новый пост')
        self.assertEqual(post.group.title, 'Просто группа')
        self.assertEqual(post.image, 'posts/small.gif')


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='автор')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Просто группа',
            slug='prosto_slug',
            description='Описание просто группы',
        )
        cls.post = []
        for i in range(13):
            cls.post.append(Post(
                text=f'Пост {i}',
                group=cls.group,
                author=cls.user,
            ))
        Post.objects.bulk_create(cls.post)

    def test_first_page_contains_ten_records(self):
        """
        На первой главное странице, странице группы, странице профиля автора
        посетитель увидит 10 постов из 13(созданы в `setUp`).
        """
        reverses_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user}),
        ]
        for reverse_name in reverses_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name + "")
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        """
       На первой главное странице, странице группы, странице профиля автора
        посетитель увидит 3 поста и 13(созданы в `setUp`).
        """
        reverses_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user}),
        ]
        for reverse_name in reverses_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)
