from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

User = get_user_model()


class UserPagesTests(TestCase):
    def setUp(self) -> None:
        self.guest_client = Client()

    def test_signup_page_show_correct_context(self):
        """
        На странице регистрации пользователя передаётся форма
        с типом полей соответствующих форме UserCreationForm.
        """
        form_fields = {
            'first_name': forms.fields.CharField,
            'last_name': forms.fields.CharField,
            'username': forms.fields.CharField,
            'email': forms.fields.EmailField,
            'password1': forms.fields.CharField,
            'password2': forms.fields.CharField,
        }
        response = self.guest_client.get(reverse('users:signup'))
        for field, expected in form_fields.items():
            with self.subTest(field=field):
                form_field = response.context['form'].fields[field]
                self.assertIsInstance(form_field, expected)
