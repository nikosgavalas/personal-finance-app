from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import auth
from django.db.models import Sum, Min, Max
from django.forms import ModelForm

import datetime
from calendar import monthrange
from collections import OrderedDict

from .models import *


class IncomeTransactionForm(ModelForm):
    class Meta:
        model = IncomeTransaction
        fields = ['date', 'value', 'comment', 'account', 'subcategory']


class ExpenseTransactionForm(ModelForm):
    class Meta:
        model = ExpenseTransaction
        fields = ['date', 'value', 'comment', 'account', 'subcategory']


class TransferTransactionForm(ModelForm):
    class Meta:
        model = TransferTransaction
        fields = ['date', 'value', 'comment', 'from_account', 'to_account']


def _clean_value(res):
    return 0.0 if res is None else round(res, 2)


def _get_account_value(account, start_date=datetime.date(1995, 8, 19), end_date=datetime.date(2100, 1, 1)):
    init = account.init_balance
    transactions_in = IncomeTransaction.objects.filter(account=account, date__gte=start_date, date__lte=end_date).aggregate(Sum('value'))['value__sum']
    transactions_out = ExpenseTransaction.objects.filter(account=account, date__gte=start_date, date__lte=end_date).aggregate(Sum('value'))['value__sum']
    transfers_in = TransferTransaction.objects.filter(to_account=account, date__gte=start_date, date__lte=end_date).aggregate(Sum('value'))['value__sum']
    transfers_out = TransferTransaction.objects.filter(from_account=account, date__gte=start_date, date__lte=end_date).aggregate(Sum('value'))['value__sum']
    return round(init
                + _clean_value(transactions_in)
                - _clean_value(transactions_out)
                + _clean_value(transfers_in)
                - _clean_value(transfers_out), 2)


@login_required
def index(req):
    income_date_min = IncomeTransaction.objects.aggregate(Min('date'))['date__min']
    income_date_max = IncomeTransaction.objects.aggregate(Max('date'))['date__max']
    expense_date_min = ExpenseTransaction.objects.aggregate(Min('date'))['date__min']
    expense_date_max = ExpenseTransaction.objects.aggregate(Max('date'))['date__max']

    min_date = min(income_date_min, expense_date_min)
    max_date = max(income_date_max, expense_date_max)

    months_available_raw = OrderedDict(((min_date + datetime.timedelta(_)).strftime(r"%Y-%m"), None) for _ in range((max_date - min_date).days)).keys()
    months_available = list(map(lambda x: (x.split('-')[0], x.split('-')[1]), list(months_available_raw)))

    return render(req, 'app/index.html', {
        'username': req.user.username,
        'months_available': months_available
    })


@login_required
def accounts(req):
    accounts = {account.name: _get_account_value(account) for account in Account.objects.all()}
    return render(req, 'app/accounts.html', {
        'accounts': accounts,
        'total_balance': sum(accounts.values())
    })


@login_required
def month(req, year, month):
    start_date = datetime.date(year, month, 1)
    end_of_target_month = monthrange(year, month)[1]
    end_date = datetime.date(year, month, end_of_target_month)

    income = {category.name: {subcategory.name: _clean_value(IncomeTransaction.objects.filter(subcategory=subcategory, date__gte=start_date, date__lte=end_date).aggregate(Sum('value'))['value__sum']) for subcategory in category.incomesubcategory_set.all()} for category in IncomeCategory.objects.all()}
    expenses = {category.name: {subcategory.name: _clean_value(ExpenseTransaction.objects.filter(subcategory=subcategory, date__gte=start_date, date__lte=end_date).aggregate(Sum('value'))['value__sum'])  for subcategory in category.expensesubcategory_set.all()} for category in ExpenseCategory.objects.all()}

    status_of_accounts = {account.name: (_get_account_value(account, end_date=start_date), _get_account_value(account, end_date=end_date)) for account in Account.objects.all()}

    return render(req, 'app/month.html', {
        'income': income,
        'total_income': _clean_value(sum([item for sublist in [value.values() for value in income.values()] for item in sublist])),
        'expenses': expenses,
        'total_expenses': _clean_value(sum([item for sublist in [value.values() for value in expenses.values()] for item in sublist])),
        'status_of_accounts': status_of_accounts,
        'income_transactions': IncomeTransaction.objects.filter(date__gte=start_date, date__lte=end_date),
        'expense_transactions': ExpenseTransaction.objects.filter(date__gte=start_date, date__lte=end_date),
        'transfers': TransferTransaction.objects.filter(date__gte=start_date, date__lte=end_date),
    })


@login_required
def add_expense_transaction(req):
    form = IncomeTransactionForm(req.POST or None)
    if form.is_valid():
        form.save()
        return redirect('app:index')
    return render(req, 'app/form.html', {'form': form})


@login_required
def add_income_transaction(req):
    form = IncomeTransactionForm(req.POST or None)
    if form.is_valid():
        form.save()
        return redirect('app:index')
    return render(req, 'app/form.html', {'form': form})


@login_required
def add_transfer_transaction(req):
    form = TransferTransactionForm(req.POST or None)
    if form.is_valid():
        form.save()
        return redirect('app:index')
    return render(req, 'app/form.html', {'form': form})


@login_required
def edit_expense_transaction(req, pk):
    transaction = get_object_or_404(ExpenseTransaction, pk=pk)
    form = ExpenseTransactionForm(req.POST or None, instance=transaction)
    if form.is_valid():
        form.save()
        return redirect('app:index')
    return render(req, 'app/form.html', {'form':form})


@login_required
def edit_income_transaction(req, pk):
    transaction = get_object_or_404(IncomeTransaction, pk=pk)
    form = IncomeTransactionForm(req.POST or None, instance=transaction)
    if form.is_valid():
        form.save()
        return redirect('app:index')
    return render(req, 'app/form.html', {'form':form})


@login_required
def edit_transfer_transaction(req, pk):
    transaction = get_object_or_404(TransferTransaction, pk=pk)
    form = TransferTransactionForm(req.POST or None, instance=transaction)
    if form.is_valid():
        form.save()
        return redirect('app:index')
    return render(req, 'app/form.html', {'form':form})


@login_required
def delete_expense_transaction(req, pk):
    transaction = get_object_or_404(ExpenseTransaction, pk=pk)
    if req.method == 'POST':
        transaction.delete()
        return redirect('app:index')
    return render(req, 'app/confirm_delete.html', {'object': transaction})


@login_required
def delete_income_transaction(req, pk):
    transaction = get_object_or_404(IncomeTransaction, pk=pk)
    if req.method == 'POST':
        transaction.delete()
        return redirect('app:index')
    return render(req, 'app/confirm_delete.html', {'object': transaction})


@login_required
def delete_transfer_transaction(req, pk):
    transaction = get_object_or_404(TransferTransaction, pk=pk)
    if req.method == 'POST':
        transaction.delete()
        return redirect('app:index')
    return render(req, 'app/confirm_delete.html', {'object': transaction})


def test(req):
    return render(req, 'app/test.html', {})


@login_required
def year(req, year):
    return HttpResponse('yearly aggregates - not yet implemented')


@login_required
def current(req):
    return month(req, year=datetime.datetime.now().year, month=datetime.datetime.now().month)


def login(req):
    if req.user.is_authenticated:
        return redirect('app:index')

    if 'username' not in req.POST or 'password' not in req.POST: # TODO replace this with if req.method==POST see above
        return render(req, 'app/login.html', {'error': 'Log in to continue.'})

    username = req.POST['username']
    password = req.POST['password']

    user = auth.authenticate(req, username=username, password=password)
    if user is not None:
        auth.login(req, user)
        return redirect('app:index')
    return render(req, 'app/login.html', {'error': 'Wrong login.'})


def logout(req):
    auth.logout(req)
    return redirect('app:index')
