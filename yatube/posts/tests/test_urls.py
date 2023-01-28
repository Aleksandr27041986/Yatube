from http import HTTPStatus
from django.test import Client, TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from posts.models import Post
from django.core.cache import cache
from .factories import post_create, group_create, clean_counter

User = get_user_model()


class StaticURLTests(TestCase):
    """Проверяем главную страницу."""
    def test_homepage(self):
        guest = Client()
        response = guest.get('/')
        self.assertEqual(response.status_code, 200)


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.subscrib_user = User.objects.create_user('subscriber')
        cls.author_user = User.objects.create_user('author')
        cls.group = group_create()
        cls.post = post_create(cls.author_user, cls.group)

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        clean_counter()

    def setUp(self):
        self.subscriber = Client()
        self.subscriber.force_login(self.subscrib_user)
        self.author = Client()
        self.author.force_login(self.author_user)
        self.guest = Client()
        self.reverse_pages_name = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.subscrib_user}),
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            reverse('posts:post_create'),
            reverse('posts:follow_index'),
        ]
        self.templates = [
            'posts/index.html',
            'posts/group_list.html',
            'posts/profile.html',
            'posts/post_detail.html',
            'posts/create_post.html',
            'posts/create_post.html',
            'posts/follow.html',
        ]
        cache.clear()

    def test_url_available_anonymous_exists_at_desired_location(self):
        """
        Неавторизованному пользователю доступны главная страница,
        страница группы, страница профиля автора и страница поста, а
        со страниц создания поста, редактирования поста и добавления
        комментария идёт переадресация на страницу авторизации.
        """
        for address in self.reverse_pages_name:
            with self.subTest(address=address):
                response = self.guest.get(address)
                if response.status_code == HTTPStatus.FOUND.value:
                    redirect_url = f'/auth/login/?next={address}'
                    self.assertRedirects(response, redirect_url)
                else:
                    self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_url_available_authorized_exists_at_desired_location(self):
        """
        Авторизованному пользователю доступны главная страница,
        страница группы, страница профиля автора, страница поста и
        страница создания поста и добавление комментария, а со страницы
        редактирования поста идёт переадресация на сам пост.
        """
        for address in self.reverse_pages_name:
            with self.subTest(address=address):
                response = self.subscriber.get(address)
                if response.status_code == HTTPStatus.FOUND.value:
                    redirect_url = reverse('posts:post_detail',
                                           kwargs={'post_id': self.post.id})
                    self.assertRedirects(response, redirect_url)
                else:
                    self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_url_available_author_exists_at_desired_location(self):
        """Автору доступны все страницы."""
        for address in self.reverse_pages_name:
            with self.subTest(address=address):
                response = self.author.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_unexisting_page_return_error(self):
        """Запрос к несуществующей странице возвращает ошибку 404 и
        обрабатывает кастомный шаблон."""
        response = self.guest.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND.value)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_reverse(self):
        """
        Ссылки полученные через reverse(name) соответствуют
        прямым ссылкам.
        """
        url = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.subscrib_user}/',
            f'/posts/{self.post.id}/',
            f'/posts/{self.post.id}/edit/',
            '/create/',
            '/follow/',
        ]
        for reverse_name, address in zip(self.reverse_pages_name, url):
            with self.subTest(reverse_name=reverse_name):
                self.assertEqual(reverse_name, address)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Из setUp берём списки адресов и шаблонов,
        # и перебираем их в цикле проверяя соответствие
        for address, template in zip(self.reverse_pages_name, self.templates):
            with self.subTest(address=address):
                response = self.author.get(address)
                self.assertTemplateUsed(response, template)

    def test_comment_avaliable_authorized_client(self):
        """
        Страница создания комментария недоступна неавторизованному
        пользователю, он будет переадресован на страницу авторизации.
        """
        url = reverse('posts:add_comment', kwargs={'post_id': self.post.id})
        response_guest = self.guest.get(url)
        redirect_url = f'/auth/login/?next={url}'
        self.assertRedirects(response_guest, redirect_url)

    def test_index_page_cache(self):
        """
        При запросе к главной страницы информация загружается из БД и
        сохраняется в кэш, при повторном запросе инфомация загружается из кэша.
        """
        def response(page):
            return self.guest.get(page)
        index = reverse('posts:index')
        response_1 = response(index)
        Post.objects.all().delete()
        response_with_cache = response(index)
        self.assertEqual(response_1.content, response_with_cache.content)
        cache.clear()
        response_without_cache = response(index)
        self.assertNotEqual(response_1.content, response_without_cache.content)
