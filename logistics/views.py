from datetime import timedelta

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import Http404
from django.utils import timezone

from .forms import SignUpForm, LoginForm
from .models import Profile, Order
from .order_forms import OrderCreateForm, AdminOrderUpdateForm


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
def dashboard_view(request):
    role = request.user.profile.role
    if role == "admin":
        return redirect("admin_dashboard")
    return redirect("customer_dashboard")


def _require_customer(request):
    if request.user.profile.role != "customer":
        raise Http404()


def _require_admin(request):
    if request.user.profile.role != "admin":
        raise Http404()


def _build_tracking_timeline(order):
    timeline_steps = [
        ("pending", "Order created"),
        ("picked_up", "Parcel picked up"),
        ("in_transit", "In transit"),
        ("out_for_delivery", "Out for delivery"),
        ("delivered", "Delivered"),
    ]

    current_index = -1
    for idx, (code, _) in enumerate(timeline_steps):
        if code == order.status:
            current_index = idx
            break

    timeline = []
    for idx, (code, label) in enumerate(timeline_steps):
        if order.status == "cancelled":
            state = "done" if idx == 0 else "todo"
        elif idx < current_index:
            state = "done"
        elif idx == current_index:
            state = "current"
        else:
            state = "todo"

        timeline.append({
            "code": code,
            "label": label,
            "state": state,
        })

    if order.status == "cancelled":
        timeline.append({
            "code": "cancelled",
            "label": "Cancelled",
            "state": "current",
        })

    return timeline


@login_required
def customer_dashboard_view(request):
    _require_customer(request)
    orders = Order.objects.filter(customer=request.user)

    context = {
        "total_orders": orders.count(),
        "active_orders": orders.exclude(status__in=["delivered", "cancelled"]).count(),
        "delivered_orders": orders.filter(status="delivered").count(),
        "latest_order": orders.order_by("-created_at").first(),
    }
    return render(request, "customer/dashboard.html", context)


@login_required
def customer_order_create_view(request):
    _require_customer(request)

    form = OrderCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        order = form.save(commit=False)
        order.customer = request.user

        # demo route
        order.depart_from = "Bournemouth"

        # Bournemouth
        order.start_lat = 50.7192
        order.start_lng = -1.8808

        # London
        order.dest_lat = 51.5074
        order.dest_lng = -0.1278

        # current location at the beginning
        order.current_lat = 50.7192
        order.current_lng = -1.8808

        order.status = "pending"
        order.estimated_delivery = timezone.now() + timedelta(days=2)
        order.tracking_note = "Order created successfully."

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

    if order.status == "delivered":
        order.current_lat = order.dest_lat
        order.current_lng = order.dest_lng

    timeline = _build_tracking_timeline(order)

    return render(
        request,
        "customer/order_detail.html",
        {
            "order": order,
            "timeline": timeline,
        },
    )


@login_required
def admin_dashboard_view(request):
    _require_admin(request)
    orders = Order.objects.all()

    context = {
        "total_users": User.objects.count(),
        "total_orders": orders.count(),
        "active_shipments": orders.exclude(status__in=["delivered", "cancelled"]).count(),
        "delivered_shipments": orders.filter(status="delivered").count(),
    }
    return render(request, "admin/dashboard.html", context)


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

    # quick status update by button
    if request.method == "POST" and "next_status" in request.POST:
        next_status = request.POST.get("next_status")

        allowed_statuses = [
            "pending",
            "picked_up",
            "in_transit",
            "out_for_delivery",
            "delivered",
            "cancelled",
        ]

        if next_status in allowed_statuses:
            order.status = next_status

            if next_status == "picked_up":
                order.tracking_note = "Parcel has been picked up."
                order.current_lat = order.start_lat
                order.current_lng = order.start_lng

            elif next_status == "in_transit":
                order.tracking_note = "Parcel is in transit."
                order.current_lat = 50.9097
                order.current_lng = -1.4044

            elif next_status == "out_for_delivery":
                order.tracking_note = "Parcel is out for delivery."
                order.current_lat = 51.0629
                order.current_lng = -1.3162

            elif next_status == "delivered":
                order.tracking_note = "Parcel delivered successfully."
                order.current_lat = order.dest_lat
                order.current_lng = order.dest_lng

            elif next_status == "cancelled":
                order.tracking_note = "Shipment was cancelled."

            order.save()
            return redirect("admin_ship_detail", order_id=order.id)

    form = AdminOrderUpdateForm(request.POST or None, instance=order)

    if request.method == "POST" and "save_form" in request.POST and form.is_valid():
        updated_order = form.save(commit=False)

        if updated_order.status == "delivered":
            updated_order.current_lat = updated_order.dest_lat
            updated_order.current_lng = updated_order.dest_lng

        updated_order.save()
        return redirect("admin_ship_detail", order_id=order.id)

    timeline = _build_tracking_timeline(order)

    return render(
        request,
        "admin/tracking_detail.html",
        {
            "order": order,
            "form": form,
            "timeline": timeline,
        },
    )


def logout_view(request):
    logout(request)
    return redirect("home")