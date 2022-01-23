from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):

    class Meta:

        model = Post
        verbose_name = 'Новый пост'
        verbose_name_plural = 'Новые посты'
        fields = ('text', 'group', 'image')
        help_texts = {'text': 'Текст нового поста',
                      'group': 'Группа', }
        localized_fields = ('__all__',)


class CommentForm(forms.ModelForm):

    class Meta:

        model = Comment
        verbose_name = 'Новый комментарий'
        verbose_name_plural = 'Новые комментарии'
        fields = ('text',)
        help_texts = {'text': 'Текст нового комментария'}
        localized_fields = ('__all__',)
