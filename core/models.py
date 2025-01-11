import json
from django.core.exceptions import ValidationError
from django.db import models

from django.contrib.auth.models import AbstractUser, Group as AuthGroup, Permission

def validate_json(value):
    try:
        json.loads(value)
    except json.JSONDecodeError:
        raise ValidationError("Invalid JSON format.")

class Student(AbstractUser):
    college = models.CharField(max_length=255)
    semester = models.IntegerField()
    default_payment_methods = models.JSONField(default=dict, validators=[validate_json])

    # Avoid clashes with reverse accessors by specifying unique related_name
    groups = models.ManyToManyField(
        AuthGroup,
        related_name="students", # Renamed to avoid conflict
        blank=True,
        help_text="The groups this user belongs to.",
        verbose_name="groups",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="student_set",
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions",
    )

class Group(models.Model):
    name = models.CharField(max_length=255)
    GROUP_TYPE_CHOICES = [
        ('study', 'Study'),
        ('sports', 'Sports'),
        ('friends', 'Friends'),
    ]
    group_type = models.CharField(max_length=50, choices=GROUP_TYPE_CHOICES)
    members = models.ManyToManyField(
        Student,
        related_name="groups_set", # Renamed to avoid conflict
    )

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Expense(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="expenses")
    split_type = models.CharField(max_length=50, choices=[('equal', 'Equal'), ('proportional', 'Proportional')]) # E.g., "equal", "proportional"
    date = models.DateField(auto_now_add=True)
    receipt_image = models.ImageField(upload_to="receipts/", blank=True, null=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="expenses")
    payer = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="paid_expenses")
    members_split = models.JSONField(default=dict)

    def __str__(self):
        return f"{self.group.name} - {self.amount} - {self.date}"

class Settlement(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='settlements', null=True, blank=True,
                                default=None)  # Add default=None
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='settlements', null=True, blank=True,
                              default=None)  # Add default=None
    payer = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payer_settlements')
    receiver = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='receiver_settlements')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.BooleanField(default=False)
    SETTLEMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('upi', 'UPI'),
        ('card', 'Card'),
    ]
    settlement_method = models.CharField(max_length=50, choices=SETTLEMENT_METHOD_CHOICES) # E.g., "Cash", "UPI", etc.
    due_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.payer.username} owes {self.receiver.username} - {self.amount}"

    def clean(self):
        if self.payer == self.receiver:
            raise ValidationError("Payer and receiver cannot be the same person.")

    def payment_status_display(self):
        return "Pending" if not self.payment_status else "Settled"

    payment_status_display.short_description = 'Payment Status'
