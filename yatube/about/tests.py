from django.test import TestCase, Client
from http import HTTPStatus

from django.urls import reverse


class AboutURLTests(TestCase):
    def setUp(self):
        self.guest = Client()

    def test_about_url_exists_at_desired_location(self):
        """
        Страница о авторе и о технологиях доступна неаторизованному
        пользователю.
        """
        url_addresses = ['/about/author/', '/about/tech/']
        for url_address in url_addresses:
            with self.subTest(url_address=url_address):
                response = self.guest.get(url_address)
                self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_about_url_uses_correct_template(self):
        """
        URL-адреса страниц о авторе и о технологиях используют
        соответствующий шаблон.
        """
        url_templates = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html'
        }
        for url_address, url_template in url_templates.items():
            with self.subTest(url_address=url_address):
                response = self.guest.get(url_address)
                self.assertTemplateUsed(response, url_template)

    def test_reverse(self):
        """
        Ссылки полученные через reverse(name) соответствуют
        прямым ссылкам.
        """
        reverse_url_names = {
            '/about/author/': reverse('about:author'),
            '/about/tech/': reverse('about:tech'),
        }
        for reverse_name, address in reverse_url_names.items():
            with self.subTest(reverse_name=reverse_name):
                self.assertEqual(reverse_name, address)
