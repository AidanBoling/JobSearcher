from pathlib import Path
from flask import Flask, render_template, request, abort, redirect, url_for
from models.job_posts import db, job_filters
from db_control import JobDbControl, DbFilterGroup
from filters_db import JobDbFilter
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

with app.app_context():
    db.create_all()
    db_control = JobDbControl(db)

    filters_control = FiltersControl(db_control, job_filters)
    print(filters_control.frontend_filters)


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
        if saved_view == 'hidden':
            pass
        if saved_view == 'favorites':
            pass
        # Test view (temp):
        if saved_view == 'test':
            inner_filters = [JobDbFilter('employment_type', 'Full-time', '=='), JobDbFilter('level', 'Entry level', '==')]
            inner_filter_group = DbFilterGroup('OR', inner_filters)

            and_filters = [inner_filter_group, JobDbFilter('company_name', 'Patterned Learning Career', '!=')]
            jobs = db_control.get_list(filter_group=DbFilterGroup('AND', and_filters))

        return render_template('index.html', jobs=jobs, options=table_settings, filters=filters_control.frontend_filters)
        

    @app.post('/table/update/settings/<setting>')
    def update_table_settings(setting):
        settings = list(table_settings.__dict__.keys())
        if request.form and setting in settings:
            if setting == 'job_fields':
                update_fields_displayed(request.form)

        return redirect(url_for('home'))
   

    @app.post('/data/update/filter/')
    def update_current_filter():
        # settings = list(table_settings.__dict__.keys())
        if request.form:
            update_fields_displayed(request.form)

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


def update_view_data_filters(data: dict):
    global filters_control

    for filter in data:
        print(filter)
        # filters_control.current_filters.append(filter)



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