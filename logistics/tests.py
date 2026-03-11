from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .forms import SignUpForm, LoginForm
from .models import Profile, Order
from .order_forms import OrderCreateForm


class BaseTestDataMixin:
    def create_user_with_role(
        self,
        username,
        password="testpass123",
        role="customer",
        email=None,
        first_name="Test",
        last_name="User",
    ):
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email or f"{username}@example.com",
            first_name=first_name,
            last_name=last_name,
        )
        Profile.objects.create(user=user, role=role)
        return user


class SignUpFormTests(BaseTestDataMixin, TestCase):
    def test_signup_form_valid_data(self):
        form = SignUpForm(
            data={
                "role": "customer",
                "username": "alice",
                "email": "alice@example.com",
                "first_name": "Alice",
                "last_name": "Smith",
                "password1": "strongpass123",
                "password2": "strongpass123",
            }
        )
        self.assertTrue(form.is_valid())

    def test_signup_form_rejects_password_mismatch(self):
        form = SignUpForm(
            data={
                "role": "customer",
                "username": "alice",
                "email": "alice@example.com",
                "first_name": "Alice",
                "last_name": "Smith",
                "password1": "strongpass123",
                "password2": "wrongpass123",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Passwords do not match.", form.errors["__all__"])

    def test_signup_form_rejects_existing_username(self):
        self.create_user_with_role(username="alice")

        form = SignUpForm(
            data={
                "role": "customer",
                "username": "alice",
                "email": "alice2@example.com",
                "first_name": "Alice",
                "last_name": "Smith",
                "password1": "strongpass123",
                "password2": "strongpass123",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Username already exists.", form.errors["__all__"])

    def test_signup_form_rejects_numeric_first_name(self):
        form = SignUpForm(
            data={
                "role": "customer",
                "username": "alice",
                "email": "alice@example.com",
                "first_name": "12345",
                "last_name": "Smith",
                "password1": "strongpass123",
                "password2": "strongpass123",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Name cannot be numbers.", form.errors["first_name"])


class LoginFormTests(BaseTestDataMixin, TestCase):
    def setUp(self):
        self.customer_user = self.create_user_with_role(
            username="customer1",
            password="testpass123",
            role="customer",
        )

    def test_login_form_valid_data(self):
        form = LoginForm(
            data={
                "role": "customer",
                "username": "customer1",
                "password": "testpass123",
            }
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["user"], self.customer_user)

    def test_login_form_rejects_wrong_password(self):
        form = LoginForm(
            data={
                "role": "customer",
                "username": "customer1",
                "password": "wrongpass",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Invalid username or password.", form.errors["__all__"])

    def test_login_form_rejects_role_mismatch(self):
        form = LoginForm(
            data={
                "role": "admin",
                "username": "customer1",
                "password": "testpass123",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Role mismatch.", form.errors["__all__"])


class OrderCreateFormTests(TestCase):
    def test_order_form_accepts_valid_weight(self):
        form = OrderCreateForm(
            data={
                "address": "123 Test Street",
                "destination": "London",
                "weight": "10.50",
                "description": "Books",
            }
        )
        self.assertTrue(form.is_valid())

    def test_order_form_rejects_zero_weight(self):
        form = OrderCreateForm(
            data={
                "address": "123 Test Street",
                "destination": "London",
                "weight": "0",
                "description": "Books",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Weight must be greater than 0.", form.errors["weight"])

    def test_order_form_rejects_weight_too_large(self):
        form = OrderCreateForm(
            data={
                "address": "123 Test Street",
                "destination": "London",
                "weight": "100001",
                "description": "Books",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Weight is too large.", form.errors["weight"])


class CustomerOrderViewTests(BaseTestDataMixin, TestCase):
    def setUp(self):
        self.customer_user = self.create_user_with_role(
            username="customer1",
            password="testpass123",
            role="customer",
        )
        self.admin_user = self.create_user_with_role(
            username="admin1",
            password="adminpass123",
            role="admin",
        )

    def test_customer_can_create_order(self):
        self.client.login(username="customer1", password="testpass123")

        response = self.client.post(
            reverse("customer_order_new"),
            data={
                "address": "123 Test Street",
                "destination": "Manchester",
                "weight": "12.50",
                "description": "Electronics",
            },
        )

        self.assertRedirects(response, reverse("customer_order_history"))
        self.assertEqual(Order.objects.count(), 1)

        order = Order.objects.first()
        self.assertEqual(order.customer, self.customer_user)
        self.assertEqual(order.address, "123 Test Street")
        self.assertEqual(order.destination, "Manchester")
        self.assertEqual(order.weight, Decimal("12.50"))
        self.assertEqual(order.status, "in_progress")

    def test_admin_cannot_access_customer_dashboard(self):
        self.client.login(username="admin1", password="adminpass123")
        response = self.client.get(reverse("customer_dashboard"))
        self.assertEqual(response.status_code, 404)

    def test_customer_cannot_access_admin_dashboard(self):
        self.client.login(username="customer1", password="testpass123")
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 404)

    def test_customer_only_sees_own_orders(self):
        other_customer = self.create_user_with_role(
            username="customer2",
            password="testpass123",
            role="customer",
        )

        own_order = Order.objects.create(
            customer=self.customer_user,
            address="1 My Street",
            destination="Glasgow",
            weight=5.00,
            description="My package",
        )
        Order.objects.create(
            customer=other_customer,
            address="2 Other Street",
            destination="Edinburgh",
            weight=8.00,
            description="Other package",
        )

        self.client.login(username="customer1", password="testpass123")
        response = self.client.get(reverse("customer_order_detail", args=[own_order.id]))
        self.assertEqual(response.status_code, 200)

        other_order = Order.objects.exclude(customer=self.customer_user).first()
        response = self.client.get(reverse("customer_order_detail", args=[other_order.id]))
        self.assertEqual(response.status_code, 404)


class DashboardRoutingTests(BaseTestDataMixin, TestCase):
    def setUp(self):
        self.customer_user = self.create_user_with_role(
            username="customer1",
            password="testpass123",
            role="customer",
        )
        self.admin_user = self.create_user_with_role(
            username="admin1",
            password="adminpass123",
            role="admin",
        )

    def test_dashboard_redirects_customer_to_customer_dashboard(self):
        self.client.login(username="customer1", password="testpass123")
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, reverse("customer_dashboard"))

    def test_dashboard_redirects_admin_to_admin_dashboard(self):
        self.client.login(username="admin1", password="adminpass123")
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, reverse("admin_dashboard"))
