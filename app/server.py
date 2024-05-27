from pathlib import Path
from flask import Flask, render_template, request, abort, redirect, url_for
from models.job_posts import db, job_filters
from db_control import JobDbControl, DbFilterGroup
from filters_db import JobDbFilter, DbFilter
from filters_control import FiltersControl
import job_searcher 

# from data.table import job_fields
from user_settings import SearchSettings, DataDisplay, DataFilters, SettingsControl

ROOT_DIR = Path(__file__).parent

app = Flask(__name__)
app.secret_key = 'a super secret key'

search_settings_controller = SettingsControl(SearchSettings, 'search_settings')
search_settings = search_settings_controller.get_as_dataclass()

table_settings_controller = SettingsControl(DataDisplay, 'data_display')
table_settings = table_settings_controller.get_as_dataclass()

global_data_filters_controller = SettingsControl(DataFilters, 'global_data_filters')
global_data_filters = global_data_filters_controller.get_as_dataclass()


# # Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:////{ROOT_DIR / "instance/jobs.db"}'
db.init_app(app)

test_filter = {'group_op': 'AND',
            'filters': [{'field': 'company_name', 'operator': 'ilike', 'values': 'Patterned Learning Career'}, 
                        {'group_op': 'OR', 
                        'filters': [{'field': 'employment_type', 'operator': 'any', 'values': ['Full-time']}, 
                                    {'field': 'level', 'operator': 'any', 'values': ['Entry level']}]
                        }
                    ]}

with app.app_context():
    db.create_all()
    db_control = JobDbControl(db)

    filters_control = FiltersControl(db_control, job_filters)
    # print(filters_control.frontend_filters)
    filters_control.current_filters = test_filter




def main():
    @app.route('/')
    def home():
        #later -> if table_settings.view == 'table', redirect to table-view. else, redirect to list view.
        #later -> saved_view will be from user settings
        return redirect(url_for('table_view', saved_view='default'))


    # @app.route('/table')
    # def table_view():
    #     return render_template('index.html', jobs=db_control.get_list(), options=table_settings)


    @app.get('/table/views/<saved_view>')
    def table_view(saved_view):
        jobs=''
        
        if saved_view == 'default':
            jobs=db_control.get_list()
        elif saved_view == 'hidden':
            pass
        elif saved_view == 'favorites':
            pass

        # Test view (temp):
        elif saved_view == 'test':
            inner_filters = [JobDbFilter('employment_type', 'Full-time', '=='), JobDbFilter('level', 'Entry level', '==')]
            inner_filter_group = DbFilterGroup('OR', inner_filters)

            and_filters = [inner_filter_group, JobDbFilter('company_name', 'Patterned Learning Career', '!=')]
            jobs = db_control.get_list(filter_group=DbFilterGroup('AND', and_filters))
        
        filters={'settings': filters_control.frontend_filters, 
                 'current': filters_control.current_filters}
        # print(filters['current'])
        # print(filters['settings'])
        
        return render_template('index.html', jobs=jobs, options=table_settings, filters=filters)
        

    @app.post('/table/update/settings/<setting>')
    def update_table_settings(setting):
        settings = list(table_settings.__dict__.keys())
        if request.form and setting in settings:
            if setting == 'job_fields':
                update_fields_displayed(request.form)

        return redirect(url_for('home'))
   

    @app.post('/data/update/filter/<filter>')
    def update_filter(filter):
        # settings = list(table_settings.__dict__.keys())
        if request.form:
            update_view_data_filters(request.form, filter)

        return redirect(url_for('home'))

    # @app.post('/data/filter')
    # def filter_options():
    #     field = request.form['name']
    #     filter = filters_control.frontend_filters[field]
    #     return render_template('data_filters.html')
    



    @app.get('/settings')
    def settings():
        return render_template('settings.html', search_settings=search_settings, global_data_filters=global_data_filters)


    # Later TODO: Add Celery, so can run search in background, and redirect immediately. 
    @app.get('/settings/run-search')
    def run_job_search():
        search_and_save_jobs()
        return redirect(url_for('settings'))
 

    @app.post('/settings/update/<section>')
    def update_settings(section):
        if request.form:
            if section == 'search_settings':
                update_search_settings_obj(request.form)
                search_settings_controller.save_to_file(search_settings)   
            if section == 'global_data_filters':
                update_global_data_filters_obj(request.form)
                global_data_filters_controller.save_to_file(global_data_filters)   
        return redirect(url_for('settings'))
    
    
    # @app.post('/settings/update/global_data_filters')
    # def update_global_data_filters():
    #     if request.form:
    #         update_global_data_filters_obj(request.form)
    #         global_data_filters_controller.save_to_file(global_data_filters)                
    #     return redirect(url_for('settings'))
    

    @app.post('/data/update/job/<int:id>')
    def update_job(id):
        if request.form:
            db_control.update_one(id, request.form)
        return redirect(url_for('home'))
    

    # @app.delete('/data/delete/job/<int:id>')
    # def delete_job(id):
    #     db_control.update_one(id, request.form)
    #     return redirect(url_for('home'))


def search_and_save_jobs():
    jobs = job_searcher.run_search(db_control, search_settings)
    
    if jobs:
        db_control.add_many(jobs)


def update_fields_displayed(data: dict):
    global table_settings

    fields_to_display = data.getlist('display')                   
    for field in table_settings.job_fields:
        if field['name'] in fields_to_display:
            field['hidden'] = False
        else:
            field['hidden'] = True
    
    table_settings_controller.save_to_file(table_settings)


#TODO: Error handling

def update_search_settings_obj(data: dict):
    global search_settings

    search_settings.search_phrases = [phrase.strip() for phrase in data['search_phrases'].split(', ')]
    search_settings.exclude_companies = [company.strip() for company in data['exclude_companies'].split(', ')]


def update_global_data_filters_obj(data: dict):
    global global_data_filters

    global_data_filters.post_title.exclude_keywords = [phrase.strip().lower() for phrase in data['title_exclude_keywords'].split(', ')]
    global_data_filters.post_title.regex = data['title_regex']


def update_view_data_filters(data: dict, filter):
    global filters_control

    print(data)
    
    filter_group_dict = filter_group_dict_from_form(data)
    print('\nf_group_dict: ', filter_group_dict)


    # db_filter_group = filter_group_dict_to_db(filter_group_dict)
    db_group = nested_filter_group_to_db(filter_group_dict, JobDbFilter)
    print('\ndb_group: ', db_group)


    # TODO: Save 

    if not filter or filter == 'current':
        pass


def nested_filter_group_to_db(group: dict, dbFilter: DbFilter) -> DbFilterGroup:
    """
    Takes group of nested filters and filter groups in dictionary form and converts into nested DbFilters
    and DbFilterGroups.
    """
    if group.get('filters'):
        filters = []
        # Check filters list for nested groups and filters. Convert as needed
        for item in group['filters']:
            
            if isinstance(item, dbFilter) or isinstance(item, DbFilterGroup):
                filters.append(item)

            elif item.get('field_name'):
                if item['operator'] in ['any', 'not_in']: 
                    item['value'] = [item['value']]
                # FIXME: added the above lines for testing; remove when fix the frontend input for select multiple (so returns an array)
               
                filter = dbFilter(item['field_name'], item['value'], item['operator'])
                filters.append(filter)

            else:
                # If nested group, call same func to recursively drill down to inner-most group 
                filter_group = nested_filter_group_to_db(item, dbFilter)
                filters.append(filter_group)
        
        print('nested_filters: ', filters)
        return DbFilterGroup(group['group_op'], filters)
    
    return group    


def filter_group_dict_from_form(filter_data: dict):

    def filters_from_form(filter_data: dict):
        filters = {}
        for filter_field in filter_data:
            # Separate path from key, value for each item

            path_list = filter_field.split('.')
            key = path_list.pop(-1)
            value = filter_data[filter_field]
            
            path = '.'.join(path_list)
            
            # Consolidate items into filters
            if not filters.get(path):
                filters[path] = {}
            filters[path][key] = value

        return filters


    # Iterate items into nested filters/group dicts
    def get_group(filter_data: dict):
        group = filter_data.get('group')
        if group:
            filter_data.pop('group')
        
        g_filters = {}
        for path, item in filter_data.items():
            path_start, path = split_path(path)
            g_filters.update({path: item})
        
        group['filters'] = get_group_filters(g_filters)

        return group
                            

    def get_group_filters(filter_data: dict):
        filters = {}

        for path, item in filter_data.items():
            
            path_start, path = split_path(path)
            if path_start not in ['filter', 'group']:
                index = int(path_start)
                filter = ''
                
                if path == 'filter':
                    filter = item
                else:
                    filter = {path: item}

                if not filters.get(index):
                    filters[index] = filter
                else:
                    filters[index].update(filter)

        filters = [item if isinstance(item, JobDbFilter) or item.get('field_name') else get_group(item) for key, item in filters.items()]
        return filters
    

    def split_path(path):
        # Pop off front segment from path, return segment and new path 
        path_list = path.split('.')
        # print('paths: ', path_list)
        
        path_start = path_list.pop(0)
        path = '.'.join(path_list)
        return path_start, path
    

    filters_dict = filters_from_form(filter_data)
    print('\nfilters: ', filters_dict)
    f_group = get_group(filters_dict)

    return f_group



main()


if __name__ == '__main__':
    app.run(debug=True)



#     filters = [{'name': 'employment_type', 'value': 'Full-time', 'operator': '=='}]
# def convert_filters(filters):
#     converted = []
#     for filter in filters:
#         if type(filter) is list:
#             JobDbFilter(filter['name'], filter['value'], filter['operator'])
#     
#     return converted


# def TEMP_test_set_current_fe_filter():
#     filter = {'group_op': 'AND',
#               'filters': [{'field': 'company_name', 'operator': 'ilike', 'values': 'Patterned Learning Career'}, 
#                           {'group_op': 'OR', 
#                            'filters': [{'field': 'employment_type', 'operator': 'any', 'values': ['Full-time']}, 
#                                        {'field': 'level', 'operator': 'any', 'values': ['Entry level']}]
#                             }
#                         ]}
    
#     # inner_filters = [JobDbFilter('employment_type', 'Full-time', '=='), JobDbFilter('level', 'Entry level', '==')]
#     # inner_filter_group = DbFilterGroup('OR', inner_filters)

#     # and_filters = [inner_filter_group, JobDbFilter('company_name', 'Patterned Learning Career', '!=')]

#     return filter


# def dict_to_db_filters(filter_data: dict):
#     # Turn filters into filter objects
#     filters = {}
#     for path, filter in filter_data.items():
#         if filter.get('field_name'):
            # if filter['operator'] in ['any', 'not_in']: 
            #     filter['value'] = [filter['value']]
            # # fixme: added the above lines for testing; remove when fix the frontend input for select multiple (so returns an array)
#             filter = JobDbFilter(filter['field_name'], filter['value'], filter['operator'])
        
#         filters.update({path: filter})
    
#     return filters