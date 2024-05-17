from pathlib import Path
from flask import Flask, render_template, request, abort, redirect, url_for
from models.job_posts import db
from job_db_control import JobDbControl
import job_searcher 

from data.table import job_fields
from user_settings import SearchSettings, DataDisplay, SettingsControl

ROOT_DIR = Path(__file__).parent

app = Flask(__name__)
app.secret_key = 'a super secret key'

search_settings_controller = SettingsControl(SearchSettings, 'search_settings')
search_settings = search_settings_controller.get_as_dataclass()

table_settings_controller = SettingsControl(DataDisplay, 'data_display')
table_settings = table_settings_controller.get_as_dataclass()

# # Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:////{ROOT_DIR / "instance/jobs.db"}'
db.init_app(app)

with app.app_context():
    db.create_all()
    db_control = JobDbControl(db)


def main():
    @app.route('/')
    def home():
        #later -> if table_settings.view == 'table', redirect to table-view. else, redirect to list view.
        return redirect(url_for('table_view'))
    

    @app.route('/table-view')
    def table_view():
        return render_template('index.html', jobs=db_control.get_all(), options=table_settings)


    @app.post('/table-view/update/settings/<setting>')
    def update_table_settings(setting):
        settings = list(table_settings.__dict__.keys())
        if request.form and setting in settings:
            if setting == 'job_fields':
                update_fields_displayed(request.form)

        return redirect(url_for('home'))


    @app.get('/settings')
    def settings():
        return render_template('settings.html', search_settings=search_settings)


    # Later TODO: Add Celery, so can run search in background, and redirect immediately. 
    @app.get('/settings/run-search')
    def run_job_search():
        search_and_save_jobs()
        return redirect(url_for('settings'))
    

    @app.post('/settings/update/search_settings')
    def update_search_settings():
        if request.form:
            update_search_settings_obj(request.form)
            search_settings_controller.save_to_file(search_settings)                
        return redirect(url_for('settings'))


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


def update_search_settings_obj(data: dict):
    global search_settings

    # Search phrases
    search_settings.search_phrases = [phrase.strip() for phrase in data['search_phrases'].split(', ')]

    # Exclude companies list
    search_settings.exclude_companies = [company.strip() for company in data['exclude_companies'].split(', ')]

    
main()


if __name__ == '__main__':
    app.run(debug=True)