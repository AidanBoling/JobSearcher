from pathlib import Path
from flask import Flask, render_template, request, abort, redirect, url_for
from models.job_posts import db
from db_control import JobDbControl
from views_control import ViewsControl
import job_searcher 
from utils import update_table_settings, update_list_settings


from user_settings import SearchSettings, DataDisplayDefaults, DataFilters, SettingsControl, SavedViews

ROOT_DIR = Path(__file__).parent

app = Flask(__name__)
app.secret_key = 'a super secret key'

search_settings_controller = SettingsControl(SearchSettings, 'search_settings')
search_settings = search_settings_controller.get_as_dataclass()

default_settings_controller = SettingsControl(DataDisplayDefaults, 'display_defaults')
display_settings = default_settings_controller.get_as_dataclass()
default_table_settings = display_settings.table

global_data_filters_controller = SettingsControl(DataFilters, 'global_data_filters')
global_data_filters = global_data_filters_controller.get_as_dataclass()


# # Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:////{ROOT_DIR / "instance/jobs.db"}'
db.init_app(app)

with app.app_context():
    db.create_all()
    db_control = JobDbControl(db)

    views_ctrl = ViewsControl(db_control, display_settings)
    
    filter_options = views_ctrl.filters_control.frontend_filters


def main():
    @app.route('/',)
    def dataview():        
        return redirect(url_for('get_view', view=views_ctrl.current_view['name']))


    @app.post('/view')
    def change_view():
        view = views_ctrl.current_view['name']
       
        if request.form:
            selected_view = request.form['view'].lower().strip()
            if selected_view in views_ctrl.saved_views.names:
                # print('request form view: ', request.form['view'])
                view = selected_view

        views_ctrl.set_current(view)
        jobs, options, views, filters, filter_options, sort_options = get_template_variables(view)
        
        return render_template('dataview.html', jobs=jobs, options=options, views=views, filters=filters, filter_options=filter_options, sort_options=sort_options)


    @app.get('/views/<view>')
    def get_view(view):
        # if error...
        #     # Q: make this a redirect (to table_layout, view='default') instead?
        #     view_filters = all_view_filters.default
        
        views_ctrl.set_current(view)

        jobs, options, views, filters, filter_options, sort_options = get_template_variables(view)

        return render_template('index.html', jobs=jobs, options=options, views=views, filters=filters, filter_options=filter_options, sort_options=sort_options)


    @app.post('/views/<view>/update/basics')
    def update_view_basics(view):
        if request.form:
            view = views_ctrl.update_view_name(view, request.form['name'])
            views_ctrl.update_view_layout(view, request.form['view_layout'])
            # print('new view name: ', view)
        return redirect(url_for('get_view', view=view))
    

    @app.post('/views/<view>/update/layout-options/<layout>')
    def update_layout_options(view, layout):
        if request.form:
            views_ctrl.update_view_layout_settings(view, layout, request.form)
        return redirect(request.referrer)


    @app.post('/views/<view>/update/filters')
    def update_filters(view):
        if request.form:
            views_ctrl.update_view_data_filters(view, request.form)

        return redirect(request.referrer)
    

    @app.post('/views/<view>/update/sort')
    def update_sort(view):
        data = {}
        if request.form:
            data = request.form

        views_ctrl.update_view_sort(view, data)
        return redirect(request.referrer)

    
    @app.post('/create-view')
    def create_view():
        if request.form:
            view = views_ctrl.create_view(request.form['name'])
            if view:
                return redirect(url_for('get_view', view=view))
        
        return redirect(url_for('dataview'))


    @app.post('/delete-view/<view>')
    def delete_view(view):
        view = views_ctrl.delete_view(view)
        if view:
            return redirect(url_for('get_view', view=views_ctrl.default_view))
        
        return redirect(url_for('dataview'))
        # Later TODO: Send message notifying of failure + reason (or success + reason)


    @app.post('/data/update/job/<int:id>')
    def update_job(id):
        if request.form:
            db_control.update_one(id, request.form)
        return redirect(url_for('dataview'))
    

    # @app.delete('/data/delete/job/<int:id>')
    # def delete_job(id):
    #     db_control.update_one(id, request.form)
    #     return redirect(url_for('dataview'))


    # APP SETTINGS
    @app.get('/settings')
    def settings():
        return render_template('settings.html', search_settings=search_settings, global_data_filters=global_data_filters)


    # Later TODO: Add Celery, so can run search in background, and redirect immediately. 
    @app.get('/settings/run-search')
    def run_job_search():
        search_and_save_jobs()
        return redirect(url_for('settings'))
 

    @app.post('/settings/update/defaults/<setting>')
    def update_view_defaults(setting):
        if request.form and setting in settings:
            settings = list(default_table_settings.__dict__.keys())

            if setting == 'table_job_fields':
                update_default_table_fields_displayed(request.form)
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
    

    


def search_and_save_jobs():
    jobs = job_searcher.run_search(db_control, search_settings)
    
    if jobs:
        db_control.add_many(jobs)


def update_default_table_fields_displayed(data: dict):
    global default_table_settings
    
    default_table_settings = update_table_settings(default_table_settings, data)    
    default_settings_controller.save_to_file(display_settings)


#TODO: Error handling

def update_search_settings_obj(data: dict):
    global search_settings

    search_settings.search_phrases = [phrase.strip() for phrase in data['search_phrases'].split(', ')]
    search_settings.exclude_companies = [company.strip() for company in data['exclude_companies'].split(', ')]


def update_global_data_filters_obj(data: dict):
    global global_data_filters

    global_data_filters.post_title.exclude_keywords = [phrase.strip().lower() for phrase in data['title_exclude_keywords'].split(', ')]
    global_data_filters.post_title.regex = data['title_regex']


def get_job_data(view):
    jobs=''

    if not views_ctrl.view_exists(view):
        print('View doesn\'t exist -- using default.')
        view = views_ctrl.default_view

    filter_group = views_ctrl.filters_control.db_filter_groups[view]
    sort = views_ctrl.saved_views.views[view]['sort']
    
    if filter_group:
        jobs = db_control.get_list(filter_group=filter_group, sort_by=sort)
    else:
        jobs = db_control.get_list(sort_by=sort)
    
    return jobs


def get_template_variables(view):

    jobs = get_job_data(view)

    # TODO: Delete filters (now not used)
    filters={'settings': filter_options}

    views={'current': views_ctrl.current_view, 
        'names': views_ctrl.saved_views.names
        }
    
    options = views_ctrl.current_view['layout_options']

    fields = views_ctrl.default_settings.table.job_fields
    field_options = [(field['name'], field['label']) for field in fields] # -> Can probably move to top of doc (startup vars)
    field_options.insert(0, ('', 'Select field'))

    sort_options = {'fields': field_options, 'order': [('asc', 'Ascending'), ('desc', 'Descending')]}

    # Later TODO (maybe): Combine layout_options and filter_options into options

    return jobs, options, views, filters, filter_options, sort_options



main()


if __name__ == '__main__':
    app.run(debug=True)