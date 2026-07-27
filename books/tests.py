import datetime

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Book


class BookModelTests(APITestCase):
    """Tests for the Book model itself."""

    def test_create_book_and_string_representation(self):
        book = Book.objects.create(
            title="Clean Code",
            author="Robert C. Martin",
            isbn="9780132350884",
            published_date=datetime.date(2008, 8, 1),
        )
        self.assertEqual(Book.objects.count(), 1)
        self.assertEqual(str(book), "Clean Code by Robert C. Martin")

    def test_isbn_must_be_unique(self):
        Book.objects.create(
            title="Clean Code",
            author="Robert C. Martin",
            isbn="9780132350884",
            published_date=datetime.date(2008, 8, 1),
        )
        with self.assertRaises(Exception):
            Book.objects.create(
                title="Duplicate ISBN Book",
                author="Someone Else",
                isbn="9780132350884",
                published_date=datetime.date(2020, 1, 1),
            )


class BookAPITests(APITestCase):
    """Tests for the /api/books/ CRUD endpoints."""

    def setUp(self):
        self.list_url = reverse('book-list')
        self.book = Book.objects.create(
            title="The Pragmatic Programmer",
            author="Andrew Hunt",
            isbn="9780135957059",
            published_date=datetime.date(2019, 9, 13),
        )
        self.detail_url = reverse('book-detail', args=[self.book.id])

    def test_list_books(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_create_book(self):
        payload = {
            "title": "Domain-Driven Design",
            "author": "Eric Evans",
            "isbn": "9780321125217",
            "published_date": "2003-08-30",
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Book.objects.count(), 2)

    def test_create_book_with_invalid_isbn_fails(self):
        payload = {
            "title": "Bad Book",
            "author": "Nobody",
            "isbn": "not-an-isbn",
            "published_date": "2020-01-01",
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('isbn', response.data)

    def test_create_book_with_future_published_date_fails(self):
        future_date = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
        payload = {
            "title": "Time Traveler's Book",
            "author": "Someone",
            "isbn": "9780321125217",
            "published_date": future_date,
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('published_date', response.data)

    def test_retrieve_book(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "The Pragmatic Programmer")

    def test_update_book(self):
        payload = {
            "title": "The Pragmatic Programmer (20th Anniversary Edition)",
            "author": "Andrew Hunt",
            "isbn": "9780135957059",
            "published_date": "2019-09-13",
        }
        response = self.client.put(self.detail_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.book.refresh_from_db()
        self.assertEqual(self.book.title, "The Pragmatic Programmer (20th Anniversary Edition)")

    def test_partial_update_book(self):
        response = self.client.patch(self.detail_url, {"author": "Andy Hunt"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.book.refresh_from_db()
        self.assertEqual(self.book.author, "Andy Hunt")

    def test_delete_book(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Book.objects.count(), 0)
