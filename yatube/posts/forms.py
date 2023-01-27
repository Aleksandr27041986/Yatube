from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['group'].empty_label = "Группа не выбрана"

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        help_texts = {
            'text': 'Текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        labels = {
            'text': 'Текст поста',
            'group': 'Группа',
            'image': 'Картинка'
        }
        widgets = {'text': forms.Textarea(attrs={'cols': 40, 'row': 10}), }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
