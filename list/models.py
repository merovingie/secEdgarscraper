from django.db import models
from django.contrib.auth.models import User

class Company(models.Model):
    name = models.CharField(max_length=100)
    ticker =  models.CharField(max_length=10)
    cik = models.IntegerField(default=0000)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Statement(models.Model):
    year = models.IntegerField(default=2019)
    type = models.CharField(max_length=255)
    url = models.URLField()
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    def __str__(self):
        return self.type

class Statment_element_headers(models.Model):
    field = models.CharField(max_length=255)
    statement = models.ForeignKey(Statement, on_delete=models.CASCADE)

    def __str__(self):
        return self.field

class Statement_element_section(models.Model):
    fieldName = models.CharField(max_length=255)
    statement = models.ForeignKey(Statement, on_delete=models.CASCADE)

    def __str__(self):
        return self.fieldName

class Statement_element_data(models.Model):
    key = models.CharField(max_length=455)
    value = models.FloatField()
    statement = models.ForeignKey(Statement, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    header = models.ForeignKey(Statment_element_headers, on_delete=models.CASCADE)

    def __str__(self):
        return self.key
