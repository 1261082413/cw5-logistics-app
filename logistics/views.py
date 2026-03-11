from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import Http404
from .models import Order, Profile
from .order_forms import OrderCreateForm

from .forms import SignUpForm, LoginForm
from .models import Profile
from django.http import Http404
from django.contrib.auth.models import User
from .models import Profile, Order


def home_view(request):
    return render(request, "home.html")


def signup_view(request):
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = User.objects.create_user(
            username=form.cleaned_data["username"],
            email=form.cleaned_data["email"],
            password=form.cleaned_data["password1"],
            first_name=form.cleaned_data["first_name"],
            last_name=form.cleaned_data["last_name"],
        )
        Profile.objects.create(user=user, role=form.cleaned_data["role"])
        return redirect("login")
    return render(request, "signup.html", {"form": form})


def login_view(request):
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.cleaned_data["user"]
        login(request, user)
        return redirect("dashboard")
    return render(request, "login.html", {"form": form})


@login_required
@login_required
@login_required
def dashboard_view(request):
    role = request.user.profile.role
    if role == "admin":
        return redirect("admin_dashboard")
    return redirect("customer_dashboard")


def _require_customer(request):
    if request.user.profile.role != "customer":
        raise Http404()

@login_required
def customer_dashboard_view(request):
    _require_customer(request)
    return render(request, "customer/dashboard.html")

@login_required
def customer_order_create_view(request):
    _require_customer(request)

    form = OrderCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        order = form.save(commit=False)
        order.customer = request.user
        order.save()
        return redirect("customer_order_history")

    return render(request, "customer/new_order.html", {"form": form})

@login_required
def customer_order_history_view(request):
    _require_customer(request)
    orders = Order.objects.filter(customer=request.user).order_by("-created_at")
    return render(request, "customer/order_history.html", {"orders": orders})

@login_required
def customer_order_detail_view(request, order_id: int):
    _require_customer(request)
    try:
        order = Order.objects.get(id=order_id, customer=request.user)
    except Order.DoesNotExist:
        raise Http404()
    return render(request, "customer/order_detail.html", {"order": order})

def _require_admin(request):
    if request.user.profile.role != "admin":
        raise Http404()


@login_required
def admin_dashboard_view(request):
    _require_admin(request)
    return render(request, "admin/dashboard.html")


@login_required
def admin_user_management_view(request):
    _require_admin(request)
    users = User.objects.all().order_by("id")
    return render(request, "admin/user_management.html", {"users": users})


@login_required
def admin_ship_management_view(request):
    _require_admin(request)
    orders = Order.objects.all().order_by("-created_at")
    return render(request, "admin/ship_management.html", {"orders": orders})


@login_required
def admin_ship_detail_view(request, order_id: int):
    _require_admin(request)
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        raise Http404()
    return render(request, "admin/tracking_detail.html", {"order": order})


def logout_view(request):
    logout(request)
    return redirect("home")


# Create your views here.
