from django.contrib.auth import get_user_model
from django.test import TestCase
from ..models import Post
from .factories import post_create, group_create, clean_counter

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user('author')
        cls.group = group_create()
        cls.post = post_create(cls.author, cls.group)
        cls.long_post = Post.objects.create(
            author=cls.author,
            text='Не более 15 символов может уместиться в превью'
        )

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        clean_counter()

    def test_models_have_correct_post_names(self):
        """
        У модели Post метод __str__ выводит текст поста сокращённый до
        15 символов.
        """
        self.assertEqual(str(self.post), 'post1')
        self.assertEqual(str(self.long_post), 'Не более 15 сим')

    def test_models_have_correct_group_names(self):
        """У модели Post метод __str__ выводит наименование группы."""
        self.assertEqual(str(self.group), 'Группа1')

    def test_post_verbose_name(self):
        """verbose_name полей модели Post совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                verbose_name = post._meta.get_field(value).verbose_name
                self.assertEqual(verbose_name, expected)

    def test_post_help_text(self):
        """help_text полей модели Post совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относится пост'
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                help_text = post._meta.get_field(value).help_text
                self.assertEqual(help_text, expected)
