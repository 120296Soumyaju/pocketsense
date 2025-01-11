from django.core.mail import send_mail
from django.conf import settings
from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
import json
from .models import Student, Group, Expense, Category, Settlement


# Custom form for the Expense model with enhanced validation
class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = '__all__'

    # Adding a custom field for members_split
    members_split = forms.JSONField(required=False, widget=forms.Textarea, initial={})

    def clean_members_split(self):
        members_split = self.cleaned_data.get('members_split')

        # Check if members_split is a valid JSON object
        if members_split:
            try:
                # Ensure it's a dictionary
                if not isinstance(members_split, dict):
                    raise forms.ValidationError("members_split should be a dictionary.")

                # Check if all amounts are positive numbers
                for member_id, amount in members_split.items():
                    if not isinstance(amount, (int, float)) or amount <= 0:
                        raise forms.ValidationError(f"Amount for member {member_id} must be a positive number.")

            except ValueError:
                raise forms.ValidationError("Invalid JSON format in members_split.")
        return members_split


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'college', 'semester')
    list_filter = ('college', 'semester')
    search_fields = ('username', 'email', 'college')


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'group_type')
    list_filter = ('group_type',)
    search_fields = ('name',)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    form = ExpenseForm  # Use the custom form
    list_display = ('group', 'payer', 'amount', 'category', 'split_type', 'date', 'members_split')  # Add members_split
    list_filter = ('split_type', 'date', 'category')
    search_fields = ('group__name', 'payer__username', 'category__name')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    list_display = ('payer', 'receiver', 'amount', 'payment_status_display', 'due_date', 'settlement_method')
    list_filter = ('payment_status', 'due_date', 'settlement_method')
    search_fields = ('payer__username', 'receiver__username', 'settlement_method')

    # Action to send reminder email
    actions = ['send_reminder']

    def send_reminder(self, request, queryset):
        for settlement in queryset:
            if not settlement.payment_status:  # Only send reminder if payment is pending
                subject = 'Payment Reminder from PocketSense'
                message = f"""
                    Hi {settlement.receiver.username},

                    This is a reminder to settle the amount of ₹{settlement.amount} owed to {settlement.payer.username} for the expense in group "{settlement.group.name}".
                    Please make the payment by {settlement.due_date} using your preferred method.
                    """
                recipient_list = [settlement.receiver.email]
                try:
                    send_mail(
                        subject,
                        message,
                        settings.EMAIL_HOST_USER,
                        recipient_list,
                        fail_silently=False,
                    )
                    self.message_user(request, f"Reminder sent to {settlement.receiver.username}.")
                except Exception as e:
                    self.message_user(request, f"Error sending reminder: {str(e)}")
        return None
