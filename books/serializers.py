import datetime

from rest_framework import serializers

from .models import Book


class BookSerializer(serializers.ModelSerializer):
    """Serializes Book instances and validates incoming data for CRUD ops."""

    class Meta:
        model = Book
        fields = [
            'id',
            'title',
            'author',
            'isbn',
            'published_date',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_isbn(self, value):
        # Normalise by stripping hyphens/spaces some clients send, e.g. "978-0-13-468599-1"
        cleaned = value.replace('-', '').replace(' ', '')
        if len(cleaned) not in (10, 13):
            raise serializers.ValidationError(
                "ISBN must be 10 or 13 characters long (excluding hyphens/spaces)."
            )
        if not (cleaned[:-1].isdigit() and (cleaned[-1].isdigit() or cleaned[-1].upper() == 'X')):
            raise serializers.ValidationError(
                "ISBN must contain only digits (with an optional trailing 'X' for ISBN-10)."
            )
        return cleaned.upper()

    def validate_published_date(self, value):
        if value > datetime.date.today():
            raise serializers.ValidationError("Published date cannot be in the future.")
        return value

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Title cannot be blank.")
        return value.strip()

    def validate_author(self, value):
        if not value.strip():
            raise serializers.ValidationError("Author cannot be blank.")
        return value.strip()
