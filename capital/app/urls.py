from django.urls import path

from . import views

app_name = 'app'
urlpatterns = [
    path('', views.index, name='index'),

    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),

    path('<int:year>/<int:month>', views.month, name='month'),
    path('<int:year>/', views.year, name='year'),
    path('current/', views.current, name='current'),

    path('account/add', views.add_account, name='add_account'),
    path('account/<int:pk>/edit', views.edit_account, name='edit_account'),
    path('account/<int:pk>/delete', views.delete_account, name='delete_account'),

    path('transaction/income/add', views.add_income_transaction, name='add_income'),
    path('transaction/income/<int:pk>/edit', views.edit_income_transaction, name='edit_income'),
    path('transaction/income/<int:pk>/delete', views.delete_income_transaction, name='delete_income'),

    path('transaction/expense/add', views.add_expense_transaction, name='add_expense'),
    path('transaction/expense/<int:pk>/edit', views.edit_expense_transaction, name='edit_expense'),
    path('transaction/expense/<int:pk>/delete', views.delete_expense_transaction, name='delete_expense'),

    path('transaction/transfer/add', views.add_transfer_transaction, name='add_transfer'),
    path('transaction/transfer/<int:pk>/edit', views.edit_transfer_transaction, name='edit_transfer'),
    path('transaction/transfer/<int:pk>/delete', views.delete_transfer_transaction, name='delete_transfer'),

    path('test', views.test, name='test'),
]
