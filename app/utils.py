import re
from collections import namedtuple
from price_parser import Price

def update_table_settings(layout_options: dict, data: dict):
    # For job_fields
    fields_to_display = data.getlist('display')
    for field in layout_options['job_fields']:
        if field['name'] in fields_to_display:
            field['hidden'] = False
        else:
            field['hidden'] = True
    
    return layout_options


def update_list_settings(layout_options: dict, data: dict):
    # TODO

    return layout_options


def get_salary_data_from_str(salary: str):
    Salary = namedtuple('Salary', ['text', 'currency', 'range_low', 'range_high'])
    salary_data = [salary]

    salary = re.sub(r'([0-9]+)(\s?(k|K))', r'\1,000', salary) # Replace 'K' with digits
    
    for n in range(2):
        price = Price.fromstring(salary)
        if price.amount:
            if n == 0:
                salary_data.append(price.currency)
            salary_data.append(int(price.amount_float))
            # Remove parsed price from string
            salary = salary.replace(price.currency, '', 1).replace(price.amount_text, '', 1)
        else:
            break

    if len(salary_data) < 4:
        salary_data.append(salary_data[-1])

    s = Salary._make(salary_data)
    print(s)
    
    return s