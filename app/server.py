from pathlib import Path
import os
import json
from datetime import datetime, timezone
from flask import Flask, render_template, request, abort, redirect, url_for, jsonify
from sqlalchemy import Boolean
from models.job_posts import db, job_filters as fe_filter_settings
from db_control import JobDbControl
from views_control import ViewsControl
from filters_control import FrontendFilterOptionsList
from filters_db import DbFilterGroup
import job_searcher 
from logger import LoggingManager
from utils import update_table_settings, update_list_settings
from accounts_manager import AccountsManager
from filters_control import JobFiltersConverter


from user_settings import JobSearch, DataDisplayDefaults, DataFilters, SettingsControl, SavedViews

ROOT_DIR = Path(__file__).parent

app = Flask(__name__)
app.secret_key = 'a super secret key'

logging_manager = LoggingManager()
logger = logging_manager.logger

job_search_settings_controller = SettingsControl(JobSearch, 'job_search')
accounts_manager = AccountsManager(job_search_settings_controller)

job_search_settings = job_search_settings_controller.get_as_dataclass()
search_settings = job_search_settings.search_settings

default_settings_controller = SettingsControl(DataDisplayDefaults, 'display_defaults')
display_settings = default_settings_controller.get_as_dataclass()
default_table_settings = display_settings.table

global_data_filters_controller = SettingsControl(DataFilters, 'global_data_filters')
global_data_filters = global_data_filters_controller.get_as_dataclass()
global_db_filters = None

form_errors={}

# # Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:////{ROOT_DIR / "instance/jobs.db"}'
db.init_app(app)

with app.app_context():
    db.create_all()
    db_control = JobDbControl(db)

    views_ctrl = ViewsControl(display_settings)
    
    filter_options_list = FrontendFilterOptionsList(db_control, fe_filter_settings)
    filter_options = filter_options_list.filters
    job_fields = default_table_settings.job_fields


def main():
    
    # logs = logging_manager.get_recent_logs(filters={'madeupfilter': '0', 'level': ['INFO', 'WARNING'], 'module': 'server'}, from_minutes_ago=2)
    # for log in logs:
    #     print(log)

    # print('logs found:', len(logs))


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
        jobs, options, views, filter_options, sort_options = get_template_variables(view)
        
        return render_template('dataview.html', jobs=jobs, options=options, views=views, filter_options=filter_options, sort_options=sort_options)


    @app.get('/views/<view>')
    def get_view(view):
        # if error...
        #     # Q: make this a redirect (to table_layout, view='default') instead?
        #     view_filters = all_view_filters.default
        
        views_ctrl.set_current(view)

        jobs, options, views, filter_options, sort_options = get_template_variables(view)

        return render_template('index.html', jobs=jobs, options=options, views=views, filter_options=filter_options, sort_options=sort_options)


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
        data = {}
        if request.form:
            data = request.form
        
        views_ctrl.update_view_data_filters(view, data)
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


    @app.post('/data/update/job-field/toggle/')
    def toggle_boolean_field():
        response = {}

        # Validate form data
        fields_types = db_control.model().get_field_types()
        boolean_fields = [field for field in fields_types.keys() if isinstance(fields_types[field], Boolean)]
        
        if not request.form['field_name'].lower() in boolean_fields:
            response = {'status': 'Error', 'message': 'Field submitted not a valid boolean field in the jobs db.'}
            return jsonify(response)
    
        try:
            value = to_bool(request.form['value'])
        except ValueError or KeyError:
            response = {'status': 'Error', 'message': 'Value field missing, or value not an accepted boolean value.'}
            return jsonify(response)
        
        # Update field
        field = request.form['field_name']
        job = db_control.update_one(request.form['id'], {field: value})  # Later todo: Error handling (db)
        job = job.as_dict()
       
        # Set response
        if to_bool(job['bookmarked']) == value:
            response = {'status': 'Success',
                        'message': f'Job field "{field}" field updated.'}
        else:
            response = {'status': 'Error',
                        'message': f'Something went wrong; Job field "{field}" not updated.'}

        response['job'] = job
        response['in_view'] = in_current_view(job['id'])

        return jsonify(response)


    @app.post('/data/delete/job')
    def delete_job():
        if request.form:
            job = json.loads(request.form['job'])
            response = {}

            save_in_deletion_log(job)   # So job won't be grabbed again on next job search
            is_deleted = db_control.delete_one(job['id'])

            if is_deleted:
                response = {'status': 'Success',
                        'message': 'Successfully deleted 1 job.'}
            else:
                response = {'status': 'Error',
                            'message': 'Something went wrong; Job could not be deleted.'}

            return jsonify(response)
        
        return redirect(url_for('dataview'))



    # APP SETTINGS
    @app.get('/settings')
    def settings():
        accounts_data = accounts_manager.get_frontend_data()
        
        data = {'search_settings': search_settings,
                'accounts_settings': accounts_data['accounts'],
                'accounts_summary': accounts_data['summary'],
                'filter_options': filter_options,
                'job_fields': job_fields, 
                'global_data_filters': global_data_filters
            }
        
        sections = ['job_search', 'search_settings', 'accounts', 'global_data_filters']
        section_errors = {section: get_admin_section_errors(section, data) for section in sections}
        section_messages = {} # TODO

        data = {**data, 'section_messages': section_messages, 'section_errors': section_errors}
        
        # print(accounts_data)
        return render_template('settings.html', **data)


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
            logger.debug(f'Form data received:\n    {request.form}')

            if section == 'search_settings':
                update_search_settings_obj(request.form)
                job_search_settings_controller.save_to_file(job_search_settings) 
            if section == 'accounts':
                parsed_data = parse_accounts_form_data(request.form)
                accounts_manager.sort_and_save_form_data(parsed_data)
            if section == 'global_data_filters':
                update_global_filters(request.form)
                global_data_filters_controller.save_to_file(global_data_filters)   
        return redirect(url_for('settings'))
    

    @app.post('/settings/update/accounts/toggle')
    def toggle_account_enabled():
        response = {}
        account_key = request.form['account']

        try:
            value = to_bool(request.form['value'])
        except ValueError or KeyError:
            response = {'status': 'Error', 'message': 'Value field missing, or value not an accepted boolean value.'}
            return jsonify(response)

        try:       
            accounts_manager.update_user_config_for_account(account_key, {'enabled': value})
        except KeyError:
            error_message='Given account identifier (key) is not a valid option'
            response = {'status': 'Error', 'message': error_message}
            logger.error(f'Account not updated: {error_message}')
            return jsonify(response)


        response = {'status': 'Success'}
        response['account'] = accounts_manager.get_frontend_data()['accounts'][account_key]

        account_name = response['account']['name']
        account_status = 'disabled'
        if value:
            account_status = 'enabled'
        
        response['message'] = f'Account "{account_name}" {account_status}.'

        return jsonify(response)


    @app.post('/settings/update/accounts/clear_credentials')
    def unset_credentials():
        response = {}
        account_key = request.form['account']
        try:
            # maybe TODO: if no credentials to remove (accounts_manager says not has_credentials and not username), return message that says not updated, b/c...
            accounts_manager.unset_credentials(account_key)
        except ValueError:
            error_message=f'Given account identifier ({account_key}) is not a valid account option.'
            response = {'status': 'Error', 'message': error_message}
            logger.error(f'Credentials not cleared: {error_message}')
            return jsonify(response)
        
        response = {'status': 'Success'}
        account_name = accounts_manager.base_config[account_key]['name']
        response['message'] = f'Successfully unset the credentials for account: {account_name}'
        
        return jsonify(response)


    # @app.post('/settings/update/global_data_filters')
    # def update_global_data_filters():
    #     if request.form:
    #         update_global_data_filters_obj(request.form)
    #         global_data_filters_controller.save_to_file(global_data_filters)                
    #     return redirect(url_for('settings'))
    

def search_and_save_jobs():
    jobs = job_searcher.run_search(db_control, search_settings)
    # TODO: Check if still need to be able pass through search_settings here^, or if can let run_search handle retrieval
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


def parse_accounts_form_data(data: dict):
    account = ''
    config_dict = {}
    fields_not_updated = []
    # errors = {}

    for field, value in data.items():
        
        fsplit = field.split('_')
        account = fsplit[0]
        field_name = '_'.join(fsplit[1:])
        
        if not value and field_name == 'password':
            fields_not_updated.append(field)
        else:
            if not accounts_manager.is_valid_account(account):
                logger.error(f"Field name error: Valid account not found in '{field}'")
                # log_form_error(field, message)
                fields_not_updated.append(field)

            else:
                if not config_dict.get(account):
                    config_dict[account] = {}
                config_dict[account][field_name] = value

        # else:
        #     fields_not_updated.append(field)

    
    for account in config_dict:
        # print(f'fields to be updated for account "{account}": ', list(config_dict[account].keys()))
        print(f'fields not to be updated for account "{account}": ', fields_not_updated)
    # print('Errors: ', form_errors)
    
    return config_dict


def get_admin_section_errors(section:str, data:dict):
    errors = []
    if section == 'accounts':
        if enabled_not_set_up := data['accounts_summary']['enabled_not_set_up']['names']:
            errors.append(f'Some accounts are enabled but set-up is incomplete: {", ".join(enabled_not_set_up)}')
    # if section == 'job_search':
    #     pass
    # if section == 'search_settings':
    #     pass
    # if section == 'global_data_filters':
    #     pass

    return errors


def update_global_filters(form_data: dict):
    global global_data_filters
    
    filters_converter = JobFiltersConverter()
    filter_group_dict = filters_converter.form_response_to_dict(form_data)
    if not filter_group_dict.get('filters'):
        filter_group_dict = {}
    
    # print(f'\nUpdating global filters: ', filter_group_dict)

    global_data_filters.job_filters = filter_group_dict
    global_data_filters_controller.save_to_file(global_data_filters)

    update_global_filters_db_group()


def update_global_filters_db_group():
    global global_db_filters

    filter_group_dict = global_data_filters.job_filters
    
    if filter_group_dict:
        filters_converter = JobFiltersConverter()
        global_db_filters = filters_converter.convert_saved_filters_to_db(filter_group_dict)
    else:
        global_db_filters = None


def get_job_data(view):
    jobs=''

    if not views_ctrl.view_exists(view):
        print('View doesn\'t exist -- using default.')
        view = views_ctrl.default_view
        #Q: ^Should be moved to route, and result in a redirect to default? 

    sort = views_ctrl.saved_views.views[view]['sort']
    view_filters = views_ctrl.db_filter_groups[view]

    filter_group = view_filters
    if view_filters and global_db_filters:
        filter_group = DbFilterGroup('and', [global_db_filters, view_filters])
    elif global_db_filters:
        filter_group = global_db_filters

    if filter_group:
        jobs = db_control.get_list(filter_group=filter_group, sort_by=sort)
    else:
        jobs = db_control.get_list(sort_by=sort)
    
    return jobs


def get_template_variables(view):

    jobs = get_job_data(view)

    views={'current': views_ctrl.current_view, 
        'names': views_ctrl.saved_views.names
        }
    
    options = views_ctrl.current_view['layout_options']

    fields = views_ctrl.default_settings.table.job_fields
    field_options = [(field['name'], field['label']) for field in fields] # -> Can probably move to top of doc (startup vars)
    field_options.insert(0, ('', 'Select field'))

    sort_options = {'fields': field_options, 'order': [('asc', 'Ascending'), ('desc', 'Descending')]}

    # Later TODO (maybe): Combine layout_options and filter_options into options

    return jobs, options, views, filter_options, sort_options


def to_bool(val):
    true_vals = [True, 'true', 1, '1']
    false_vals = [False, 'false', 0, '0']

    if type(val) == str:
        val = val.lower().strip()
    
    if val in true_vals:
        return True
    if val in false_vals:
        return False
    
    else:
        raise ValueError('Value not an accepted boolean')


def in_current_view(id):
    view = views_ctrl.current_view['name']
    filter_group = views_ctrl.db_filter_groups[view]

    is_in_view = db_control.job_exists_where(id, filter_group)
    print('is in view: ', is_in_view)

    return is_in_view


def save_in_deletion_log(job):
    print('Starting save to deletion log...')

    deleted_logs_dir = ROOT_DIR / 'instance/deletion_logs'
    if not os.path.exists(deleted_logs_dir):
        print('No deletion_log directory found; creating directory...')
        os.mkdir(deleted_logs_dir)
    
    filename = job['job_board'].replace(' ', '_')
    timestamp = datetime.now(timezone.utc)  # ...Or should this be local time?
    log_file = f'{deleted_logs_dir}/{filename}.txt'
    
    deletion_entry = f'{timestamp},{job["post_id"]}\n'
    
    try:
        with open(log_file, 'a') as file:
            file.write(deletion_entry)
    except FileNotFoundError:
        with open(log_file, 'w+') as file:
            file.write(deletion_entry)
    finally:
        print('Entry added to deletion log.')


update_global_filters_db_group()
main()


if __name__ == '__main__':
    app.run(debug=True)





## -------TEMP - Trash -------- ##

# def update_global_data_filters_obj(data: dict):
#     global global_data_filters

#     global_data_filters.post_title.exclude_keywords = [phrase.strip().lower() for phrase in data['title_exclude_keywords'].split(', ')]
#     global_data_filters.post_title.regex = data['title_regex']




# def log_form_error(field:str, message:str, tags:list[str]=[]):
#     global form_errors

#     form_errors[field] = {
#         'error': message,
#         'tags': tags
#         }


# def user_form_messages(form_data, errors):
#     pass
    # Fields updated: number out of number successfully updated -> 
    # validate updates -- 
    #'The following fields had errors and were not updated