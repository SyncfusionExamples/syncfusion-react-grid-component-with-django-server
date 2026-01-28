from django.db import models

class BookLending(models.Model):
    record_id = models.AutoField(primary_key=True)  # Unique identifier
    book_title = models.CharField(max_length=255)
    isbn_number = models.CharField(max_length=32, db_index=True)
    author_name = models.CharField(max_length=255)
    genre = models.CharField(max_length=100)
    borrower_name = models.CharField(max_length=255)
    borrower_email = models.EmailField()
    borrowed_date = models.DateField()
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)  # optional
    lending_status = models.CharField(max_length=20)  # Borrowed, Returned, Overdue

    class Meta:
        indexes = [
            models.Index(fields=["book_title"]),
            models.Index(fields=["author_name"]),
            models.Index(fields=["genre"]),
            models.Index(fields=["lending_status"]),
        ]
        ordering = ["-borrowed_date"]

    def __str__(self):
        return f"{self.book_title} ({self.isbn_number}) - {self.borrower_name}"
