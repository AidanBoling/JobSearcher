from pathlib import Path
from flask import Flask, render_template, request, abort, redirect, url_for
from models.job_posts import db
from db_control import JobDbControl, DbFilterGroup
from filters_db import JobDbFilter
from filters_control import JobFiltersControl
import job_searcher 

# from data.table import job_fields
from user_settings import SearchSettings, DataDisplay, DataFilters, SettingsControl, SavedViews

ROOT_DIR = Path(__file__).parent

app = Flask(__name__)
app.secret_key = 'a super secret key'

search_settings_controller = SettingsControl(SearchSettings, 'search_settings')
search_settings = search_settings_controller.get_as_dataclass()

display_settings_controller = SettingsControl(DataDisplay, 'data_display')
display_settings = display_settings_controller.get_as_dataclass()
table_settings = display_settings.table

global_data_filters_controller = SettingsControl(DataFilters, 'global_data_filters')
global_data_filters = global_data_filters_controller.get_as_dataclass()

saved_views_controller = SettingsControl(SavedViews, 'saved_views')
saved_views = saved_views_controller.get_as_dataclass()

# # Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:////{ROOT_DIR / "instance/jobs.db"}'
db.init_app(app)

with app.app_context():
    db.create_all()
    db_control = JobDbControl(db)

    filters_control = JobFiltersControl(db_control, saved_views.job_filters)


def main():
    @app.route('/')
    def home():
        #later -> if table_settings.view == 'table', redirect to table-view. else, redirect to list view.
        default_view=display_settings.settings.default_view
        default_view_type=display_settings.settings.default_display_type
        if default_view_type == 'table':
            return redirect(url_for('table_view', view=default_view))
        else:
            return redirect(url_for('table_view', view=default_view))


    @app.get('/table/views/<view>')
    def table_view(view):
        jobs=''
        # if error...
        #     # Q: make this a redirect (to table_view, view='default') instead?
        #     view_filters = saved_views.filters.default

        if view == 'default':
            jobs=db_control.get_list()
        elif view == 'hidden':
            pass
        elif view == 'favorites':
            pass

        # Test view (temp):
        elif view == 'test':
            # inner_filters = [JobDbFilter('employment_type', 'Full-time', '=='), JobDbFilter('level', 'Entry level', '==')]
            # inner_filter_group = DbFilterGroup('OR', inner_filters)
            # and_filters = [inner_filter_group, JobDbFilter('company_name', 'Patterned Learning Career', '!=')]
            # jobs = db_control.get_list(filter_group=DbFilterGroup('AND', and_filters))
            inner_filters = [JobDbFilter('employment_type', ['Full-time'], 'any'), JobDbFilter('level', ['Entry level'], 'any')]
            inner_filter_group = DbFilterGroup('OR', inner_filters)

            and_filters = [inner_filter_group, JobDbFilter('company_name', 'Patterned Learning Career', 'not_ilike')]
            
            filter_group = DbFilterGroup('AND', and_filters)
            print('manual filter_group: ', filter_group)
        
        filters_control.set_current(view)
        filter_group = filters_control.current_filters_db

        if filter_group:
            jobs = db_control.get_list(filter_group=filter_group)
        else:
            jobs = db_control.get_list()

        filters={'settings': filters_control.frontend_filters,
                 'current': filters_control.current_filters}
        
        views={'current': view, 'all': saved_views.names}
        # print(filters['current'])
        # print(filters['settings'])
        
        return render_template('index.html', jobs=jobs, options=table_settings, views=views, filters=filters)
        

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

        # TODO: redirect to the view it was on
        return redirect(url_for('home'))


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
    
    display_settings_controller.save_to_file(display_settings)


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

    # print(data)
    
    filter_group_dict = filters_control.form_response_to_dict(data)
    print(f'\nUpdating filters for view "{filter}": ', filter_group_dict)
    
    if not filter or filter == 'current':
        filters_control.current_filters = filter_group_dict
    else:
        # Update and save view
        saved_views.job_filters[filter] = filter_group_dict
        saved_views_controller.save_to_file(saved_views)

        # Update filters_control
        filters_control.view_filters = saved_views.job_filters
        filters_control.update_view_db_filter_group(filter)

    # Later TODO (maybe): Allow save view filters separate from "saving" filters -- e.g. update filters temporarily, and user can decide if keep changes


main()


if __name__ == '__main__':
    app.run(debug=True)