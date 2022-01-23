import tempfile
import shutil

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from http import HTTPStatus
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post, Group, Comment


User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='SomeUser')
        cls.group = Group.objects.create(
            title='test group title',
            slug='test-slug',
            description='test group'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Test text',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.unauthorized_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'test text two',
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
        )
        last_object = Post.objects.latest('id')
        post_text_0 = last_object.text
        post_author_0 = last_object.author.username
        post_group_0 = last_object.group.title
        post_img_0 = last_object.image

        self.assertEqual(HTTPStatus.FOUND.value, 302)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(post_text_0, form_data['text'])
        self.assertEqual(post_author_0, self.user.username)
        self.assertEqual(post_group_0, self.group.title)
        self.assertEqual(post_img_0, 'posts/small.gif')
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_edit_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'post_id': self.post.id,
            'text': 'test text three',
            'group': self.group.pk,
            'author': self.user.username,
        }
        response = self.authorized_client.post(reverse(
            'posts:post_edit', args=[self.post.id]),
            data=form_data, follow=True,
        )
        edited_post = Post.objects.latest('id')

        self.assertRedirects(response, reverse(
            'posts:post_detail', args=[self.post.id])
        )
        self.assertEqual(edited_post.text, form_data['text'])
        self.assertEqual(edited_post.author, self.user)
        self.assertEqual(edited_post.group, self.group)
        self.assertEqual(Post.objects.count(), posts_count)

    def test_guest_create_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'test text two',
            'group': self.group.pk,
        }
        response = self.unauthorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
        )

        self.assertEqual(HTTPStatus.FOUND.value, 302)
        self.assertRedirects(response, reverse(
            'users:login') + '?next=' + reverse('posts:post_create')
        )
        self.assertEqual(Post.objects.count(), posts_count)

    def test_create_comment(self):
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'comment text',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
        )

        self.assertEqual(HTTPStatus.FOUND.value, 302)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Post.objects.count(), comments_count + 1)

    def test_guest_create_comment(self):
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'comment text',
        }
        response = self.unauthorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
        )

        self.assertEqual(HTTPStatus.FOUND.value, 302)
        self.assertRedirects(
            response,
            reverse('users:login') + '?next=' + (
                reverse('posts:add_comment', args={self.post.pk})
            )
        )
        self.assertEqual(Post.objects.count(), comments_count + 1)
