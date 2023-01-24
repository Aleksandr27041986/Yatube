from http import HTTPStatus
from django.test import Client, TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class UserURLTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.guest_client = Client()
        cls.url = [
            '/auth/signup/',
            '/auth/login/',
            '/auth/password_change/',
            '/auth/password_change/done/',
            '/auth/password_reset/',
            '/auth/password_reset/done/',
            '/auth/reset/done/',
            '/auth/logout/',
            '/auth/reset/uidb64/token/',
        ]
        cls.templates = [
            'users/signup.html',
            'users/login.html',
            'users/password_change_form.html',
            'users/password_change_done.html',
            'users/password_reset_form.html',
            'users/password_reset_done.html',
            'users/password_reset_complete.html',
            'users/logged_out.html',
            'users/password_reset_confirm.html',
        ]
        cls.reverses_names = [
            reverse('users:signup'),
            reverse('users:login'),
            reverse('users:password_change'),
            reverse('users:password_change_done'),
            reverse('users:password_reset_form'),
            reverse('users:password_reset_done'),
            reverse('users:password_reset_complete'),
            reverse('users:logout'),
            reverse('users:password_reset_confirm', kwargs={'uidb64': 'uidb64',
                                                            'token': 'token'})
        ]

    def setUp(self) -> None:
        self.user = User.objects.create_user(username='user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_reverse(self):
        """
        Ссылки полученные через reverse(name) соответствуют
        прямым ссылкам.
        """
        # Из setUpClass берём списки reverse и url адресов,
        # и перебираем их в цикле проверяя соответствие
        for reverse_name, address in zip(self.reverses_names, self.url):
            with self.subTest(reverse_name=reverse_name):
                self.assertEqual(reverse_name, address)

    def test_urls_uses_correct_template(self):
        """
        URL-адрес использует соответствующий шаблон.
        """
        # Из setUpClass берём списки reverse и шаблонов,
        # и перебираем их в цикле проверяя соответствие
        for reverse_name, template in zip(self.reverses_names, self.templates):
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_url_available_authorized_exists_at_desired_location(self):
        """
        Авторизированному пользователю доступны все страницы приложения.
        """
        for reverse_name in self.reverses_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_url_available_anonymous_exists_at_desired_location(self):
        """
        Неавторизованному пользователю доступны все страницы,
        кроме страницы изменения пароля и подтверждения изменения пароля,
        с которых идёт переадресация на страницу входа.
        """
        for reverse_name in self.reverses_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                if response.status_code == HTTPStatus.FOUND.value:
                    redirect_url = f'/auth/login/?next={reverse_name}'
                    self.assertRedirects(response, redirect_url)
                else:
                    self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_unexisting_page_return_error(self):
        """Запрос к несуществующей странице возвращает ошибку."""
        response = self.guest_client.get('/auth/unexisting_page/')
        self.assertEqual(response.status_code, 404)
