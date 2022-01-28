import tempfile
import shutil

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.models import Post, Group, Follow

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user.username}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
            'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_edit_page_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
            'posts/create_post.html',
        }
        post = get_object_or_404(Post, pk=self.post.id)
        if post.author == self.authorized_client:
            for reverse_name, template in templates_pages_names.items():
                with self.subTest(template=template):
                    response = self.authorized_client.get(reverse_name)
                    self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author.username
        post_group_0 = first_object.group.title
        post_img_0 = first_object.image
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_author_0, self.user.username)
        self.assertEqual(post_group_0, self.group.title)
        self.assertEqual(post_img_0, self.post.image)

    def test_group_list_page_show_correct_context(self):
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug})
        )
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author.username
        post_img_0 = first_object.image
        self.assertEqual(post_author_0, self.user.username)
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_img_0, self.post.image)

    def test_profile_pages_show_correct_context(self):
        response = (self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username}))
        )
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author.username
        post_img_0 = first_object.image
        self.assertEqual(post_author_0, self.user.username)
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_img_0, self.post.image)

    def test_post_detail_pages_show_correct_context(self):
        response = (self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        )
        get_post = response.context.get('post')
        self.assertEqual(get_post.text, self.post.text)
        self.assertEqual(get_post.image, self.post.image)
        self.assertEqual(
            get_post.author.username, self.user.username
        )
        self.assertEqual(get_post.group.title, self.group.title)

    def test_creat_post_pages_show_correct_context(self):
        response = (self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        )
        get_post = response.context.get('post')
        self.assertEqual(get_post.text, self.post.text)
        self.assertEqual(
            get_post.author.username, self.user.username
        )
        self.assertEqual(
            get_post.group.title, self.group.title
        )

    def test_cache_work(self):
        response = self.authorized_client.get(reverse('posts:index'))
        posts_amount = len(response.context['page_obj'])
        self.assertEqual(posts_amount, Post.objects.count())
        form_data = {
            'text': 'test text two',
            'group': self.group.pk,
        }
        response_one = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
        )
        posts_amount_one = len(response.context['page_obj'])
        self.assertRedirects(response_one, reverse(
            'posts:profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(posts_amount_one, Post.objects.count() - 1)
        cache.clear()
        response_again = self.authorized_client.get(reverse('posts:index'))
        posts_amount_two = len(response_again.context['page_obj'])
        self.assertEqual(posts_amount_two, Post.objects.count())


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.number_of_posts = 13
        cls.user = User.objects.create_user(username='username')
        cls.group = Group.objects.create(
            title='test group',
            slug='test-slug',
            description='test group desc'
        )

        objs = [
            Post(
                text='test text',
                author=cls.user,
                group=cls.group,
            )
            for pst in range(cls.number_of_posts)
        ]
        cls.post = Post.objects.bulk_create(objs)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(
            response.context['page_obj']), settings.PAGINATOR_CONST
        )

    def test_second_page_contains_three_records(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(
            response.context['page_obj']),
            self.number_of_posts % settings.PAGINATOR_CONST
        )

    def test_group_list_first_page_contains_ten_records(self):
        response = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(len(
            response.context['page_obj']), settings.PAGINATOR_CONST
        )

    def test_group_list__second_page_contains_three_records(self):
        response = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}) + '?page=2'
        )
        self.assertEqual(len(
            response.context['page_obj']),
            self.number_of_posts % settings.PAGINATOR_CONST
        )

    def test_profile__first_page_contains_ten_records(self):
        response = self.client.get(reverse(
            'posts:profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(len(
            response.context['page_obj']), settings.PAGINATOR_CONST
        )

    def test_profile_second_page_contains_three_records(self):
        response = self.client.get(reverse(
            'posts:profile',
            kwargs={'username': self.user.username}) + '?page=2'
        )
        self.assertEqual(len(
            response.context['page_obj']),
            self.number_of_posts % settings.PAGINATOR_CONST
        )


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='username')
        cls.user_2 = User.objects.create_user(username='username_2')
        cls.user_3 = User.objects.create_user(username='username_3')
        cls.group = Group.objects.create(
            title='test group',
            slug='test-slug',
            description='test group desc'
        )

        cls.post = Post.objects.create(
            text='test text',
            author=cls.user_2,
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user_2)
        self.authorized_client_3 = Client()
        self.authorized_client_3.force_login(self.user_3)

    def test_subscribe(self):
        followers_count = Follow.objects.count()
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user_3.username}
            )
        )
        follower = Follow.objects.get(user=self.user)
        self.assertEqual(self.user_3, follower.author)
        self.assertEqual(
            Follow.objects.count(), followers_count + 1
        )

    def test_unsubscribe(self):
        Follow.objects.create(
            user=self.user,
            author=self.user_2,
        )
        followers_count = Follow.objects.count()
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.user_2.username}
            )
        )
        followers_count_again = Follow.objects.count()
        self.assertEqual(
            followers_count_again, followers_count - 1
        )

    def test_subscriber_has_post(self):
        Follow.objects.create(
            user=self.user,
            author=self.user_2,
        )
        authors_post = Post.objects.create(
            text=self.post.text,
            author=self.post.author,
            group=self.group,
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(response.context['page_obj'][0], authors_post)

    def test_unsubscriber_has_not_post(self):
        authors_post = Post.objects.create(
            text=self.post.text,
            author=self.post.author,
            group=self.group,
        )
        response = self.authorized_client_3.get(
            reverse('posts:follow_index')
        )
        self.assertNotEqual(response.context['page_obj'], authors_post)
