from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus

from posts.models import Post, Group

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='username')
        cls.group = Group.objects.create(
            title='test group',
            slug='test-slug',
            description='test group desc'
        )

        cls.post = Post.objects.create(
            text='test text',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_exists_at_desired_location(self):
        code_url_names = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.user.username}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/': HTTPStatus.OK,
            '/create/': HTTPStatus.FOUND,
            f'/posts/{self.post.id}/edit/': HTTPStatus.FOUND,
            '/unknownpage/': HTTPStatus.NOT_FOUND,
        }
        for adress, code in code_url_names.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, code)

    def test_urls_exists_at_desired_location_for_user(self):
        code_url_names = {
            '/create/': HTTPStatus.OK,
            f'/posts/{self.post.id}/edit/': HTTPStatus.FOUND,
            '/unknownpage/': HTTPStatus.NOT_FOUND,
        }
        for adress, code in code_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertEqual(response.status_code, code)

    def test_posts_edit_author_list_url_exists_at_desired_location(self):
        """Страница /posts/<int:post_id>/edit/ доступна автору пользователю."""
        if self.post.author == self.authorized_client:
            response = self.authorized_client.get(
                f'/posts/{self.post.id}/edit/'
            )
            self.assertEqual(response.status_code, HTTPStatus.OK)
            raise

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_posts_edit_author_uses_correct_template(self):
        if self.post.author == self.authorized_client:
            response = self.authorized_client.get(
                f'/posts/{self.post.id}/edit/'
            )
            self.assertTemplateUsed(response, 'posts/create_post.html')
