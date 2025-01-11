from django.db.models import Sum
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from django.core.mail import send_mail
from django.conf import settings
from .models import Expense, Student, Group, Settlement, Category
from .serializers import (
    ExpenseSerializer,
    StudentSerializer,
    GroupSerializer,
    SettlementSerializer,
    CategorySerializer,
)

class StudentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing students.
    """
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email', 'college']
    ordering_fields = ['username', 'college', 'semester']

class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing groups.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'group_type']
    ordering_fields = ['name', 'group_type']

    @action(detail=True, methods=['get'])
    def expenses(self, request, pk=None):
        """
        Get all expenses for a group.
        """
        group = self.get_object()
        expenses = Expense.objects.filter(group=group)
        serializer = ExpenseSerializer(expenses, many=True)
        return Response(serializer.data)

class ExpenseViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing expenses.
    """
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['category__name', 'payer__username']
    ordering_fields = ['date', 'amount']

    def create(self, request, *args, **kwargs):
        """
        Custom logic for expense creation with settlements.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        expense = serializer.save()

        headers = self.get_success_headers(serializer.data)

        # After creating an expense, you may want to handle splitting or settlement creation
        # Here you can add custom logic to calculate the split and generate settlements
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class SettlementViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing settlements.
    """
    queryset = Settlement.objects.all()
    serializer_class = SettlementSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['payer__username', 'payee__username', 'payment_status']
    ordering_fields = ['due_date', 'amount']

    def get_queryset(self):
        """
        Filter settlements based on query parameters.
        """
        queryset = self.queryset
        group_id = self.request.query_params.get('group')
        payer_id = self.request.query_params.get('payer')
        status_filter = self.request.query_params.get('status')

        if group_id:
            queryset = queryset.filter(group_id=group_id)
        if payer_id:
            queryset = queryset.filter(payer_id=payer_id)
        if status_filter:
            queryset = queryset.filter(payment_status=status_filter)

        return queryset

    @action(detail=True, methods=['post'])
    def reminder(self, request, pk=None):
        """
        Send a payment reminder for a specific settlement.
        """
        settlement = self.get_object()
        if not settlement.payment_status:  # Only send a reminder if payment is pending
            subject = 'Payment Reminder from PocketSense'
            message = f"""
                    Hi {settlement.receiver.username},

                    This is a reminder to settle the amount of ₹{settlement.amount} owed to {settlement.payer.username} for the expense in group "{settlement.group.name}".
                    Please make the payment by {settlement.due_date} using your preferred payment method.
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
                return Response({"message": "Reminder sent successfully."}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": f"Failed to send reminder: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({"error": "Settlement is already settled."}, status=status.HTTP_400_BAD_REQUEST)

class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing categories.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name']

class MonthlyAnalysisViewSet(viewsets.ViewSet):
    """
    API endpoint for monthly analysis.
    """
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['category__name']
    ordering_fields = ['total_amount']

    def list(self, request):
        """
        Return aggregated expenses grouped by category with optional filters.
        """
        category_name = request.query_params.get('category')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # Filter expenses based on the query parameters
        expenses = Expense.objects.all()
        if category_name:
            expenses = expenses.filter(category__name__icontains=category_name)
        if start_date and end_date:
            expenses = expenses.filter(date__range=[start_date, end_date])

        # Aggregate data grouped by category
        aggregated_data = (
            expenses.values('category__name')
            .annotate(total_amount=Sum('amount'))
            .order_by('-total_amount')
        )

        # Paginate the data
        paginator = PageNumberPagination()
        paginator.page_size = 10  # Adjust page size as needed
        paginated_data = paginator.paginate_queryset(aggregated_data, request)

        if paginated_data is not None:
            return paginator.get_paginated_response(paginated_data)

        # If no pagination is applied, return all data
        return Response(aggregated_data)

