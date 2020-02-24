from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import auth
from django.db.models import Sum, Min, Max
from django import forms
from django.contrib.admin.widgets import AdminDateWidget
from django.template.defaulttags import register

import datetime
from calendar import monthrange
from collections import OrderedDict

from .models import *


@register.filter
def get_item(dictionary, key):
    ret = dictionary.get(key)
    return 0.0 if not ret else ret


class IncomeTransactionForm(forms.ModelForm):
    class Meta:
        model = IncomeTransaction
        fields = ['date', 'value', 'comment', 'account', 'subcategory']


class ExpenseTransactionForm(forms.ModelForm):
    class Meta:
        model = ExpenseTransaction
        fields = ['date', 'value', 'comment', 'account', 'subcategory']


class TransferTransactionForm(forms.ModelForm):
    class Meta:
        model = TransferTransaction
        fields = ['date', 'value', 'comment', 'from_account', 'to_account']


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name', 'init_balance']


def _clean_value(res):
    return 0.0 if res is None else round(res, 2)


def _get_account_value(user, account, start_date=datetime.date(1995, 8, 19), end_date=datetime.date(2100, 1, 1)):
    init = account.init_balance
    transactions_in = IncomeTransaction.objects.filter(user=user, account=account, date__gte=start_date, date__lte=end_date).aggregate(Sum('value'))['value__sum']
    transactions_out = ExpenseTransaction.objects.filter(user=user, account=account, date__gte=start_date, date__lte=end_date).aggregate(Sum('value'))['value__sum']
    transfers_in = TransferTransaction.objects.filter(user=user, to_account=account, date__gte=start_date, date__lte=end_date).aggregate(Sum('value'))['value__sum']
    transfers_out = TransferTransaction.objects.filter(user=user, from_account=account, date__gte=start_date, date__lte=end_date).aggregate(Sum('value'))['value__sum']
    return round(init
                + _clean_value(transactions_in)
                - _clean_value(transactions_out)
                + _clean_value(transfers_in)
                - _clean_value(transfers_out), 2)


def _get_total_values_for_expense_categories(user, start_date=datetime.date(1995, 8, 19), end_date=datetime.date(2100, 1, 1)):
    queryset = ExpenseTransaction.objects.raw('''
        SELECT c.id, c.name, sum(t.value) AS total
        FROM app_expensetransaction AS t
        INNER JOIN app_expensesubcategory AS s
        ON t.subcategory_id = s.id
        INNER JOIN app_expensecategory AS c
        ON s.category_id = c.id
        WHERE t.date >= %s
        AND t.date <= %s
        AND t.user_id = %s
        GROUP BY c.name;
        ''', [start_date, end_date, user.id])
    ret = {}
    for i in queryset:
        ret[i.name] = _clean_value(i.total)
    return ret


def _get_total_values_for_income_categories(user, start_date=datetime.date(1995, 8, 19), end_date=datetime.date(2100, 1, 1)):
    queryset = IncomeTransaction.objects.raw('''
        SELECT c.id, c.name, sum(t.value) AS total
        FROM app_incometransaction AS t
        INNER JOIN app_incomesubcategory AS s
        ON t.subcategory_id = s.id
        INNER JOIN app_incomecategory AS c
        ON s.category_id = c.id
        WHERE t.date >= %s
        AND t.date <= %s
        AND t.user_id = %s
        GROUP BY c.name;
        ''', [start_date, end_date, user.id])
    ret = {}
    for i in queryset:
        ret[i.name] = _clean_value(i.total)
    return ret


def _get_available_months(user):
    income_date_min = IncomeTransaction.objects.filter(user=user).aggregate(Min('date'))['date__min']
    income_date_max = IncomeTransaction.objects.filter(user=user).aggregate(Max('date'))['date__max']
    expense_date_min = ExpenseTransaction.objects.filter(user=user).aggregate(Min('date'))['date__min']
    expense_date_max = ExpenseTransaction.objects.filter(user=user).aggregate(Max('date'))['date__max']

    months_available = []

    if income_date_min or expense_date_min:
        if income_date_min and expense_date_min:
            min_date = min(income_date_min, expense_date_min)
            max_date = max(income_date_max, expense_date_max)
        elif income_date_min and not expense_date_min:
            min_date = income_date_min
            max_date = income_date_max
        elif not income_date_min and expense_date_min:
            min_date = expense_date_min
            max_date = expense_date_max

        if min_date == max_date:
            months_available = [(str(min_date.year), str(min_date.month))]
        else:
            months_available_raw = OrderedDict(((min_date + datetime.timedelta(_)).strftime('%Y-%m'), None) for _ in range((max_date - min_date).days)).keys()
            months_available = list(map(lambda x: (x.split('-')[0], x.split('-')[1]), list(months_available_raw)))
            months_available.reverse()
    
    return months_available


@login_required
def index(req):
    user = req.user

    accounts = [account for account in Account.objects.filter(user=user)]
    accounts_values = list(map(lambda acc: _get_account_value(user=user, account=acc), accounts))

    return render(req, 'app/index.html', {
        'username': req.user.username,
        'months_available': _get_available_months(user),
        'accounts': list(zip(accounts, accounts_values)),
        'total_balance': sum(accounts_values)
    })


@login_required
def month(req, year, month):
    user = req.user

    start_date = datetime.date(year, month, 1)
    end_of_target_month = monthrange(year, month)[1]
    end_date = datetime.date(year, month, end_of_target_month)

    # TODO replace these with raw query to avoid hitting the database multiple times for a single operation
    income = {
        category.name: {
            subcategory.name: _clean_value(IncomeTransaction.objects.filter(user=user, subcategory=subcategory, date__gte=start_date, date__lte=end_date).aggregate(Sum('value'))['value__sum']) for subcategory in category.incomesubcategory_set.all()
        } for category in IncomeCategory.objects.all()
    }
    expenses = {
        category.name: {
            subcategory.name: _clean_value(ExpenseTransaction.objects.filter(user=user, subcategory=subcategory, date__gte=start_date, date__lte=end_date).aggregate(Sum('value'))['value__sum']) for subcategory in category.expensesubcategory_set.all()
        } for category in ExpenseCategory.objects.all()
    }

    status_of_accounts = {
        account.name: (_get_account_value(user=user, account=account, end_date=start_date), _get_account_value(user=user, account=account, end_date=end_date)) for account in Account.objects.filter(user=user)
    }

    return render(req, 'app/month.html', {
        # TODO add this months_available as context
        'months_available': _get_available_months(user),
        
        'income': income,
        'income_aggregates': _get_total_values_for_income_categories(user, start_date=start_date, end_date=end_date),
        'total_income': _clean_value(sum([item for sublist in [value.values() for value in income.values()] for item in sublist])),
        
        'expenses': expenses,
        'expenses_aggregates': _get_total_values_for_expense_categories(user, start_date=start_date, end_date=end_date),
        'total_expenses': _clean_value(sum([item for sublist in [value.values() for value in expenses.values()] for item in sublist])),

        'income_transactions': IncomeTransaction.objects.filter(user=user, date__gte=start_date, date__lte=end_date).order_by('-date'),
        'expense_transactions': ExpenseTransaction.objects.filter(user=user, date__gte=start_date, date__lte=end_date).order_by('-date'),
        'transfers': TransferTransaction.objects.filter(user=user, date__gte=start_date, date__lte=end_date).order_by('-date'),
        
        'status_of_accounts': status_of_accounts,
    })


@login_required
def add_account(req):
    form = AccountForm(req.POST or None)
    if form.is_valid():
        f = form.save(commit=False)
        f.user = req.user
        f.save()
        return redirect('app:index')
    return render(req, 'app/form.html', {'form': form})


@login_required
def add_expense_transaction(req):
    if req.method == 'POST':
        form = ExpenseTransactionForm(req.POST)
        if form.is_valid():
            f = form.save(commit=False)
            f.user = req.user
            f.save()
            return redirect('app:index')
    form = ExpenseTransactionForm()
    form.fields['account'].queryset = Account.objects.filter(user=req.user)
    return render(req, 'app/form.html', {'form': form})


@login_required
def add_income_transaction(req):
    if req.method == 'POST':
        form = IncomeTransactionForm(req.POST)
        if form.is_valid():
            f = form.save(commit=False)
            f.user = req.user
            f.save()
            return redirect('app:index')
    form = IncomeTransactionForm()
    form.fields['account'].queryset = Account.objects.filter(user=req.user)
    return render(req, 'app/form.html', {'form': form})


@login_required
def add_transfer_transaction(req):
    if req.method == 'POST':
        form = TransferTransactionForm(req.POST)
        if form.is_valid():
            f = form.save(commit=False)
            f.user = req.user
            f.save()
            return redirect('app:index')
    form = TransferTransactionForm()
    form.fields['from_account'].queryset = Account.objects.filter(user=req.user)
    form.fields['to_account'].queryset = Account.objects.filter(user=req.user)
    return render(req, 'app/form.html', {'form': form})


@login_required
def edit_account(req, pk):
    account = get_object_or_404(Account, pk=pk, user=req.user)
    form = AccountForm(req.POST or None, instance=account)
    if form.is_valid():
        form.save()
        return redirect('app:index')
    return render(req, 'app/form.html', {'form':form})


@login_required
def edit_expense_transaction(req, pk):
    # can a user edit another user's transaction? or change transaction's account to an account that belongs to a different user?
    transaction = get_object_or_404(ExpenseTransaction, pk=pk, user=req.user)
    if req.method == 'POST':
        form = ExpenseTransactionForm(req.POST, instance=transaction)
        form.save()
        return redirect('app:index')
    form = ExpenseTransactionForm(instance=transaction)
    form.fields['account'].queryset = Account.objects.filter(user=req.user)
    return render(req, 'app/form.html', {'form':form})


@login_required
def edit_income_transaction(req, pk):
    transaction = get_object_or_404(IncomeTransaction, pk=pk, user=req.user)
    if req.method == 'POST':
        form = IncomeTransactionForm(req.POST, instance=transaction)
        form.save()
        return redirect('app:index')
    form = IncomeTransactionForm(instance=transaction)
    form.fields['account'].queryset = Account.objects.filter(user=req.user)
    return render(req, 'app/form.html', {'form':form})


@login_required
def edit_transfer_transaction(req, pk):
    transaction = get_object_or_404(TransferTransaction, pk=pk, user=req.user)
    if req.method == 'POST':
        form = TransferTransactionForm(req.POST, instance=transaction)
        form.save()
        return redirect('app:index')
    form = TransferTransactionForm(instance=transaction)
    form.fields['from_account'].queryset = Account.objects.filter(user=req.user)
    form.fields['to_account'].queryset = Account.objects.filter(user=req.user)
    return render(req, 'app/form.html', {'form':form})


@login_required
def delete_account(req, pk):
    account = get_object_or_404(Account, pk=pk, user=req.user)
    if req.method == 'POST':
        account.delete()
        return redirect('app:index')
    return render(req, 'app/confirm_delete.html', {'object': account})


@login_required
def delete_expense_transaction(req, pk):
    transaction = get_object_or_404(ExpenseTransaction, pk=pk, user=req.user)
    if req.method == 'POST':
        transaction.delete()
        return redirect('app:index')
    return render(req, 'app/confirm_delete.html', {'object': transaction})


@login_required
def delete_income_transaction(req, pk):
    transaction = get_object_or_404(IncomeTransaction, pk=pk, user=req.user)
    if req.method == 'POST':
        transaction.delete()
        return redirect('app:index')
    return render(req, 'app/confirm_delete.html', {'object': transaction})


@login_required
def delete_transfer_transaction(req, pk):
    transaction = get_object_or_404(TransferTransaction, pk=pk, user=req.user)
    if req.method == 'POST':
        transaction.delete()
        return redirect('app:index')
    return render(req, 'app/confirm_delete.html', {'object': transaction})


@login_required
def test(req):
    ret = {}
    print(ret)
    return render(req, 'app/test.html', {'ret': ret})


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
