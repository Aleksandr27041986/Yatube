from django.contrib.auth import get_user_model
from django.test import TestCase
from ..models import Post, Group

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Просто группа',
            slug='prosto_slug',
            description='Описание просто группы',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Короткий пост',
        )
        cls.long_post = Post.objects.create(
            author=cls.user,
            text='Не более 15 символов может уместиться в превью'
        )

    def test_models_have_correct_object_names(self):
        """
        У модели Post метод __str__ выводит текст поста сокращённый до
        15 символов, у модели Group выводится название группы.
        """
        objects_names = {
            PostModelTest.post: 'Короткий пост',
            PostModelTest.long_post: 'Не более 15 сим',
            PostModelTest.group: 'Просто группа',
        }
        for object, object_name in objects_names.items():
            with self.subTest(object=object):
                self.assertEqual(str(object), object_name)

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
