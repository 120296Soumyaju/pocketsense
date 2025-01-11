from rest_framework import serializers
from .models import Expense, Student, Group, Settlement, Category

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['id', 'username', 'college', 'semester', 'default_payment_methods']

class GroupSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Student.objects.all()
    )  # Allow posting members as IDs, but still retrieve them as objects

    class Meta:
        model = Group
        fields = ['id', 'name', 'group_type', 'members']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class ExpenseSerializer(serializers.ModelSerializer):
    group_id = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(),
        source='group',  # Maps to the `group` field in the model
        write_only=True
    )
    payer_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(),
        source='payer',  # Maps to the `payer` field in the model
        write_only=True
    )
    members_split = serializers.JSONField(write_only=True)  # Used for input only

    # Read-only fields
    group = GroupSerializer(read_only=True)
    payer = StudentSerializer(read_only=True)
    category = serializers.SlugRelatedField(
        slug_field='name',
        queryset=Category.objects.all()
    )

    class Meta:
        model = Expense
        fields = ['id', 'group_id', 'payer_id', 'amount', 'category', 'split_type', 'members_split', 'group', 'payer']

    def create(self, validated_data):
        """
        Custom create method to handle members_split for settlements creation.
        """
        members_split = validated_data.pop('members_split', None)
        expense = super().create(validated_data)

        # Create settlements based on members_split
        if members_split:
            for member_id, amount in members_split.items():
                try:
                    receiver  = Student.objects.get(id=member_id)
                except Student.DoesNotExist:
                    continue  # Optionally handle this case

                Settlement.objects.create(
                    expense=expense,
                    group=validated_data['group'],
                    payer=validated_data['payer'],
                    receiver=receiver,  # 'receiver' instead of 'payee'
                    amount=amount,
                    payment_status= False,
                    settlement_method='UPI'  # Default or based on logic
                )
        return expense

class SettlementSerializer(serializers.ModelSerializer):
    group = GroupSerializer(read_only=True)  # Nested serializer for better representation
    expense = ExpenseSerializer(read_only=True)  # Nested serializer for expense details
    payer = StudentSerializer(read_only=True)  # Nested serializer for payer details
    receiver = StudentSerializer(read_only=True)  # Nested serializer for payee details

    class Meta:
        model = Settlement
        fields = ['id', 'group', 'expense', 'payer', 'receiver', 'amount', 'payment_status']
