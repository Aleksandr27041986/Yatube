from django.test import TestCase, Client
from django.urls import reverse

from django.contrib.auth import get_user_model

User = get_user_model()


class UserCreateFromTests(TestCase):
    def setUp(self) -> None:
        self.guest = Client()

    def test_create_user(self):
        """
        При заполнении формы регистрации создаётся
        новый пользователь и происходит переадресация на главную страницу.
        """
        users_count = User.objects.count()
        form_data = {
            'first_name': 'Имя пользователя',
            'last_name': 'Фамилия пользователя',
            'username': 'user',
            'email': 'user@yandex.ru',
            'password1': 'Itcnfrjd36',
            'password2': 'Itcnfrjd36'
        }
        response = self.guest.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        self.assertEqual(User.objects.count(), users_count + 1)
        self.assertRedirects(response, reverse('posts:index'))
        self.assertTrue(
            User.objects.filter(username=form_data['username']).exists()
        )
