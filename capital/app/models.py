import datetime

from django.db import models
from django.utils import timezone


class Account(models.Model):
    name = models.CharField(max_length=30)
    init_balance = models.IntegerField()

    def __str__(self):
        return self.name


class IncomeCategory(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name


class ExpenseCategory(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name


class IncomeSubcategory(models.Model):
    category = models.ForeignKey(IncomeCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)

    def __str__(self):
        return '{}-{}'.format(self.category, self.name)


class ExpenseSubcategory(models.Model):
    category = models.ForeignKey(ExpenseCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)

    def __str__(self):
        return '{}-{}'.format(self.category, self.name)


class IncomeTransaction(models.Model):
    date = models.DateField('transaction date')
    value = models.FloatField(default=0)
    comment = models.CharField(max_length=100, blank=True)
    subcategory = models.ForeignKey(IncomeSubcategory,
                            default=1,
                            on_delete=models.CASCADE,
                            related_name='income_transaction_subcategory')
    account = models.ForeignKey(Account,
                            default=1,
                            on_delete=models.CASCADE,
                            related_name='income_transaction_account')

    def __str__(self):
        return '{} | {} | {} > {} | {}'.format(self.date, self.value,
                                               self.subcategory, self.account,
                                               self.comment)


class ExpenseTransaction(models.Model):
    date = models.DateField('transaction date')
    value = models.FloatField(default=0)
    comment = models.CharField(max_length=100, blank=True)
    account = models.ForeignKey(Account,
                            default=1,
                            on_delete=models.CASCADE,
                            related_name='expense_transaction_account')
    subcategory = models.ForeignKey(ExpenseSubcategory,
                            default=1,
                            on_delete=models.CASCADE,
                            related_name='expense_transaction_subcategory')

    def __str__(self):
        return '{} | {} | {} > {} | {}'.format(self.date, self.value,
                                               self.account, self.subcategory,
                                               self.comment)


class TransferTransaction(models.Model):
    date = models.DateField('transaction date')
    value = models.FloatField(default=0)
    comment = models.CharField(max_length=100, blank=True)
    from_account = models.ForeignKey(Account,
                            default=1,
                            on_delete=models.CASCADE,
                            related_name='transfer_transaction_from_account')
    to_account = models.ForeignKey(Account,
                            default=1,
                            on_delete=models.CASCADE,
                            related_name='transfer_transaction_to_account')

    def __str__(self):
        return '{} | {} | {} > {} | {}'.format(self.date, self.value,
                                               self.from_account, self.to_account,
                                               self.comment)
