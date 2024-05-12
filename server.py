from pathlib import Path
from flask import Flask, render_template, request, abort, redirect, url_for
from models.job_posts import db
from job_db_control import JobDbControl
import job_searcher 

from data.table import job_fields

ROOT_DIR = Path(__file__).parent

app = Flask(__name__)
app.secret_key = 'a super secret key'
# bootstrap = Bootstrap5(app)

# # Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:////{ROOT_DIR / "instance/jobs.db"}'
db.init_app(app)

with app.app_context():
    db.create_all()
    db_control = JobDbControl(db)


def main():
    @app.route("/")
    def home():
        return render_template('index.html', jobs=db_control.get_all(), display_fields=display_fields())
    
    @app.get("/run-search")
    def run_job_search():
        search_and_save_jobs()
        return redirect(url_for('home'))


def search_and_save_jobs():
    
    db_control = JobDbControl(db)
    jobs = job_searcher.run_search(db_control)
    
    if jobs:
        db_control.add_many(jobs)

def display_fields():
    return [field for field in job_fields if not field['disabled']]


main()



if __name__ == '__main__':
    app.run(debug=True)