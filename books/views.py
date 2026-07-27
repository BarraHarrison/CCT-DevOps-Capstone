from rest_framework import viewsets, filters

from .models import Book
from .serializers import BookSerializer


class BookViewSet(viewsets.ModelViewSet):
    """
    CRUD API for books.

    list:        GET    /api/books/
    create:      POST   /api/books/
    retrieve:    GET    /api/books/{id}/
    update:      PUT    /api/books/{id}/
    partial_update: PATCH /api/books/{id}/
    destroy:     DELETE /api/books/{id}/
    """

    queryset = Book.objects.all()
    serializer_class = BookSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'author', 'isbn']
    ordering_fields = ['title', 'author', 'published_date', 'created_at']
