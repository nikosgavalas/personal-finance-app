from django.urls import path

from . import views

app_name = 'app'
urlpatterns = [
    path('', views.index, name='index'),

    path('<int:year>/<int:month>', views.month, name='month'),
    path('<int:year>/', views.year, name='year'),
    path('current/', views.current, name='current'),

    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),

    path('accounts/', views.accounts, name='accounts'),

    path('transaction/income/add', views.add_income_transaction, name='income'),
    path('transaction/income/<int:pk>/edit', views.edit_income_transaction, name='edit_income_transaction'),
    path('transaction/income/<int:pk>/delete', views.delete_income_transaction, name='delete_income_transaction'),

    path('transaction/expense/add', views.add_expense_transaction, name='expense'),
    path('transaction/expense/<int:pk>/edit', views.edit_expense_transaction, name='edit_expense_transaction'),
    path('transaction/expense/<int:pk>/delete', views.delete_expense_transaction, name='delete_expense_transaction'),

    path('transaction/transfer/add', views.add_transfer_transaction, name='transfer'),
    path('transaction/transfer/<int:pk>/edit', views.edit_transfer_transaction, name='edit_transfer_transaction'),
    path('transaction/transfer/<int:pk>/delete', views.delete_transfer_transaction, name='delete_transfer_transaction'),

    path('test', views.test, name='test'),
]
