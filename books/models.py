from django.core.validators import RegexValidator
from django.db import models

# ISBN-10 or ISBN-13, digits only with an optional trailing 'X' check digit
# for ISBN-10 (hyphens/spaces are rejected here; the serializer normalises
# input before it reaches the model).
isbn_validator = RegexValidator(
    regex=r'^(?:\d{9}[\dX]|\d{13})$',
    message="ISBN must be a valid ISBN-10 or ISBN-13 (digits only, optional trailing X).",
)


class Book(models.Model):
    """A single book in the catalog."""

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    isbn = models.CharField(
        max_length=13,
        unique=True,
        validators=[isbn_validator],
        help_text="ISBN-10 or ISBN-13, digits only.",
    )
    published_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return f"{self.title} by {self.author}"
