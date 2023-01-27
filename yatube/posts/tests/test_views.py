import shutil
import tempfile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django import forms
from posts.forms import PostForm
from .factories import post_create, group_create, clean_counter

from posts.models import Follow

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.TEST_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.author_user = User.objects.create_user('author')
        cls.subscrib_user = User.objects.create_user('subscriber')
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
        cls.group = group_create()
        cls.post = post_create(cls.author_user, cls.group, cls.uploaded)

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        clean_counter()

    def setUp(self) -> None:
        self.subscriber = Client()
        self.subscriber.force_login(self.subscrib_user)
        self.author = Client()
        self.author.force_login(self.author_user)
        self.unfollowed_user = User.objects.create_user('Unfollowed')
        self.unfollowed = Client()
        self.unfollowed.force_login(self.unfollowed_user)
        self.group_2 = group_create()
        self.guest = Client()

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
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.author_user}),
        ]
        for reverse_name in reverses_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.author.get(reverse_name)
                post = response.context['page_obj'][0]
                self.assertEqual(post.author.username, 'author')
                self.assertEqual(post.text, 'post1')
                self.assertEqual(post.group.title, 'Группа1')
                self.assertEqual(post.image, 'posts/small.gif')

    def test_post_detail_page_contains_post_group_author(self):
        """
        На странице поста пользователь увидит пост (созданный в `setUp`),
        содержащий информацию о тексте поста, группе, картинке
        и авторе поста.
        """
        url = reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        response = self.subscriber.get(url)
        post = response.context.get('post')
        self.assertEqual(post.author.username, 'author')
        self.assertEqual(post.text, 'post1')
        self.assertEqual(post.group.title, 'Группа1')
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
            reverse('posts:profile', kwargs={'username': self.author_user}): 1,
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
        self.subscriber.get(create_url)
        self.assertTrue(
            User.objects.filter(follower__author__username='author')
        )
        self.subscriber.get(delete_url)
        self.assertFalse(
            User.objects.filter(follower__author__username='author')
        )

    def test_new_post_add_in_follower_page(self):
        """
        Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех,
        кто не подписан.
        """
        url = reverse('posts:follow_index')
        Follow.objects.create(user=self.subscrib_user, author=self.post.author)
        user_with_fol = self.subscriber
        user_unfol = self.unfollowed
        # сравниваем количество до добавления нового поста
        self.comparing_responsed_and_expected_quantity(user_with_fol, url, 1)
        self.comparing_responsed_and_expected_quantity(user_unfol, url, 0)
        post_create(self.author_user, self.group)
        # сравниваем количество записей после добавления нового поста
        self.comparing_responsed_and_expected_quantity(user_with_fol, url, 2)
        self.comparing_responsed_and_expected_quantity(user_unfol, url, 0)
        response = self.subscriber.get(url)
        post = response.context['page_obj'][0]
        self.assertEqual(post.text, 'post2')

    def test_follow_page_contains_post_group_author(self):
        """"
        Пользователь после подписки на автора видит в избранном информацию
        о тексте поста, группе, картинке и авторе поста.
        """
        create_url = reverse('posts:profile_follow',
                             kwargs={'username': self.post.author})
        self.subscriber.get(create_url)
        response = self.subscriber.get(reverse('posts:follow_index'))
        post = response.context['page_obj'][0]
        self.assertEqual(post.author.username, 'author')
        self.assertEqual(post.text, 'post1')
        self.assertEqual(post.group.title, 'Группа1')
        self.assertEqual(post.image, 'posts/small.gif')


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.author_user = User.objects.create_user('author')
        cls.author = Client()
        cls.author.force_login(cls.author_user)
        cls.group = group_create()
        for i in range(13):
            post_create(cls.author_user, cls.group)
        clean_counter()

    def test_first_page_contains_ten_records(self):
        """
        На первой главное странице, странице группы, странице профиля автора
        посетитель увидит 10 постов из 13(созданы в `setUp`).
        """
        reverses_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.author_user}),
        ]
        for reverse_name in reverses_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.author.get(reverse_name + "")
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        """
       На первой главное странице, странице группы, странице профиля автора
        посетитель увидит 3 поста и 13(созданы в `setUp`).
        """
        reverses_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.author_user}),
        ]
        for reverse_name in reverses_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.author.get(reverse_name + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)
