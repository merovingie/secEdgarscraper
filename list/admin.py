from django.contrib import admin
from .models import Company, Statement, Statment_element_headers, Statement_element_section, Statement_element_data

admin.site.register(Company)
admin.site.register(Statement)
admin.site.register(Statment_element_headers)
admin.site.register(Statement_element_section)
admin.site.register(Statement_element_data)



# Register your models here.
