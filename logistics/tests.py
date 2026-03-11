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


class ModelTests(BaseTestDataMixin, TestCase):
    def test_profile_str(self):
        user = self.create_user_with_role(username="alice", role="customer")
        self.assertEqual(str(user.profile), "alice - customer")

    def test_order_str(self):
        user = self.create_user_with_role(username="bob", role="customer")
        order = Order.objects.create(
            customer=user,
            address="123 Street",
            destination="London",
            weight=Decimal("10.50"),
            description="Books",
        )
        self.assertEqual(str(order), f"Order #{order.id} (in_progress)")

    def test_order_default_status_is_in_progress(self):
        user = self.create_user_with_role(username="carol", role="customer")
        order = Order.objects.create(
            customer=user,
            address="456 Street",
            destination="Glasgow",
            weight=Decimal("5.00"),
            description="Clothes",
        )
        self.assertEqual(order.status, "in_progress")

    def test_order_depart_from_default_is_blank_string(self):
        user = self.create_user_with_role(username="david", role="customer")
        order = Order.objects.create(
            customer=user,
            address="789 Street",
            destination="Edinburgh",
            weight=Decimal("3.00"),
            description="Food",
        )
        self.assertEqual(order.depart_from, "")


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

    def test_signup_form_rejects_numeric_last_name(self):
        form = SignUpForm(
            data={
                "role": "customer",
                "username": "alice",
                "email": "alice@example.com",
                "first_name": "Alice",
                "last_name": "12345",
                "password1": "strongpass123",
                "password2": "strongpass123",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Name cannot be numbers.", form.errors["last_name"])


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

    def test_order_form_rejects_negative_weight(self):
        form = OrderCreateForm(
            data={
                "address": "123 Test Street",
                "destination": "London",
                "weight": "-5",
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


class PublicViewTests(BaseTestDataMixin, TestCase):
    def test_home_page_loads(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")

    def test_signup_page_loads(self):
        response = self.client.get(reverse("signup"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "signup.html")

    def test_login_page_loads(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "login.html")

    def test_signup_view_creates_user_and_profile(self):
        response = self.client.post(
            reverse("signup"),
            data={
                "role": "customer",
                "username": "newuser",
                "email": "newuser@example.com",
                "first_name": "New",
                "last_name": "User",
                "password1": "strongpass123",
                "password2": "strongpass123",
            },
        )
        self.assertRedirects(response, reverse("login"))
        self.assertTrue(User.objects.filter(username="newuser").exists())

        user = User.objects.get(username="newuser")
        self.assertEqual(user.email, "newuser@example.com")
        self.assertEqual(user.first_name, "New")
        self.assertEqual(user.last_name, "User")
        self.assertEqual(user.profile.role, "customer")

    def test_login_view_logs_user_in_and_redirects(self):
        self.create_user_with_role(
            username="customer1",
            password="testpass123",
            role="customer",
        )
        response = self.client.post(
            reverse("login"),
            data={
                "role": "customer",
                "username": "customer1",
                "password": "testpass123",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard"))

        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, reverse("customer_dashboard"))

    def test_logout_view_logs_user_out(self):
        self.create_user_with_role(
            username="customer1",
            password="testpass123",
            role="customer",
        )
        self.client.login(username="customer1", password="testpass123")
        response = self.client.get(reverse("logout"))
        self.assertRedirects(response, reverse("home"))

        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)


class AuthenticationRequiredTests(BaseTestDataMixin, TestCase):
    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_customer_dashboard_requires_login(self):
        response = self.client.get(reverse("customer_dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_customer_order_new_requires_login(self):
        response = self.client.get(reverse("customer_order_new"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_customer_order_history_requires_login(self):
        response = self.client.get(reverse("customer_order_history"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_admin_dashboard_requires_login(self):
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_admin_user_management_requires_login(self):
        response = self.client.get(reverse("admin_user_management"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_admin_ship_management_requires_login(self):
        response = self.client.get(reverse("admin_ship_management"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)


class CustomerViewTests(BaseTestDataMixin, TestCase):
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

    def test_customer_dashboard_loads(self):
        self.client.login(username="customer1", password="testpass123")
        response = self.client.get(reverse("customer_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "customer/dashboard.html")

    def test_customer_can_open_new_order_page(self):
        self.client.login(username="customer1", password="testpass123")
        response = self.client.get(reverse("customer_order_new"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "customer/new_order.html")

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

    def test_customer_order_create_invalid_post_does_not_create_order(self):
        self.client.login(username="customer1", password="testpass123")
        response = self.client.post(
            reverse("customer_order_new"),
            data={
                "address": "123 Test Street",
                "destination": "Manchester",
                "weight": "0",
                "description": "Electronics",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "customer/new_order.html")
        self.assertEqual(Order.objects.count(), 0)

    def test_customer_order_history_shows_only_own_orders(self):
        other_customer = self.create_user_with_role(
            username="customer2",
            password="testpass123",
            role="customer",
        )
        own_order = Order.objects.create(
            customer=self.customer_user,
            address="1 My Street",
            destination="Glasgow",
            weight=Decimal("5.00"),
            description="My package",
        )
        other_order = Order.objects.create(
            customer=other_customer,
            address="2 Other Street",
            destination="Edinburgh",
            weight=Decimal("8.00"),
            description="Other package",
        )

        self.client.login(username="customer1", password="testpass123")
        response = self.client.get(reverse("customer_order_history"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "customer/order_history.html")
        self.assertContains(response, f"#{own_order.id}")
        self.assertNotContains(response, f"#{other_order.id}")

    def test_customer_can_view_own_order_detail(self):
        order = Order.objects.create(
            customer=self.customer_user,
            address="1 My Street",
            destination="Glasgow",
            weight=Decimal("5.00"),
            description="My package",
        )

        self.client.login(username="customer1", password="testpass123")
        response = self.client.get(reverse("customer_order_detail", args=[order.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "customer/order_detail.html")

    def test_customer_cannot_view_other_users_order_detail(self):
        other_customer = self.create_user_with_role(
            username="customer2",
            password="testpass123",
            role="customer",
        )
        other_order = Order.objects.create(
            customer=other_customer,
            address="2 Other Street",
            destination="Edinburgh",
            weight=Decimal("8.00"),
            description="Other package",
        )

        self.client.login(username="customer1", password="testpass123")
        response = self.client.get(reverse("customer_order_detail", args=[other_order.id]))
        self.assertEqual(response.status_code, 404)

    def test_customer_order_detail_returns_404_for_nonexistent_order(self):
        self.client.login(username="customer1", password="testpass123")
        response = self.client.get(reverse("customer_order_detail", args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_admin_cannot_access_customer_dashboard(self):
        self.client.login(username="admin1", password="adminpass123")
        response = self.client.get(reverse("customer_dashboard"))
        self.assertEqual(response.status_code, 404)

    def test_admin_cannot_access_customer_order_pages(self):
        self.client.login(username="admin1", password="adminpass123")
        response = self.client.get(reverse("customer_order_new"))
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse("customer_order_history"))
        self.assertEqual(response.status_code, 404)


class AdminViewTests(BaseTestDataMixin, TestCase):
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

    def test_admin_dashboard_loads(self):
        self.client.login(username="admin1", password="adminpass123")
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/dashboard.html")

    def test_admin_user_management_loads(self):
        self.client.login(username="admin1", password="adminpass123")
        response = self.client.get(reverse("admin_user_management"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/user_management.html")
        self.assertContains(response, "customer1")
        self.assertContains(response, "admin1")

    def test_admin_ship_management_loads(self):
        Order.objects.create(
            customer=self.customer_user,
            address="1 My Street",
            destination="Glasgow",
            weight=Decimal("5.00"),
            description="My package",
        )

        self.client.login(username="admin1", password="adminpass123")
        response = self.client.get(reverse("admin_ship_management"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/ship_management.html")
        self.assertContains(response, "#1")
        self.assertContains(response, "In progress")

    def test_admin_can_view_ship_detail(self):
        order = Order.objects.create(
            customer=self.customer_user,
            address="1 My Street",
            destination="Glasgow",
            weight=Decimal("5.00"),
            description="My package",
        )

        self.client.login(username="admin1", password="adminpass123")
        response = self.client.get(reverse("admin_ship_detail", args=[order.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/tracking_detail.html")

    def test_admin_ship_detail_returns_404_for_nonexistent_order(self):
        self.client.login(username="admin1", password="adminpass123")
        response = self.client.get(reverse("admin_ship_detail", args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_customer_cannot_access_admin_pages(self):
        self.client.login(username="customer1", password="testpass123")

        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse("admin_user_management"))
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse("admin_ship_management"))
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