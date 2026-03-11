from django.urls import path
from . import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("logout/", views.logout_view, name="logout"),
    
]
urlpatterns += [
    path("customer/", views.customer_dashboard_view, name="customer_dashboard"),
    path("customer/orders/new/", views.customer_order_create_view, name="customer_order_new"),
    path("customer/orders/", views.customer_order_history_view, name="customer_order_history"),
    path("customer/orders/<int:order_id>/", views.customer_order_detail_view, name="customer_order_detail"),
    path("admin-panel/", views.admin_dashboard_view, name="admin_dashboard"),
    path("admin-panel/users/", views.admin_user_management_view, name="admin_user_management"),
    path("admin-panel/ships/", views.admin_ship_management_view, name="admin_ship_management"),
    path("admin-panel/ships/<int:order_id>/", views.admin_ship_detail_view, name="admin_ship_detail"),
]