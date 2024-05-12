from dateparser import parse
from models.job_posts import JobPost, db


class JobDbControl:

    def __init__(self, db: db):
        self.db = db


    def get_one(id):
        post = db.get_or_404(JobPost, id)
        return post


    def get_all(self):
        # order_by_field
        query = db.select(JobPost).order_by(JobPost.id)
        all_posts = db.session.execute(query).scalars().all()
        return all_posts
    

    def get_post_ids(self, job_board):
        query = self.db.select(JobPost.post_id).where(JobPost.job_board == job_board).order_by(JobPost.id)
        ids = self.db.session.execute(query).scalars().all()
        return ids
    

    def add_one(self, job: dict):
        #Create new entry and add to db
        new_job_post = JobPost(**job)

        # TODO: add error handling...
        self.db.session.add(new_job_post)
        self.db.session.commit()
        # print(new_post.as_dict())

        return new_job_post


    def add_many(self, jobs: list):
        # TODO: Catch sqlalchemy.exc.IntegrityError -- log jobs that went wrong, and what data was missing/incorrectly formatted.
        
        for job in jobs:
            if job['posted_date'] and type('posted_date') is str:
                job['posted_date'] = parse(job['posted_date'], settings={'RETURN_AS_TIMEZONE_AWARE': True})

            self.add_one(job)
        
    
    




# def filter_jobs(filters: dict = {}):
#     # allowed_filters = ['id']

#     filter_data = {key: value for (key, value) in filters.items() if value}
#     query = db.select(JobPost).filter_by(**filter_data).order_by(JobPost.id)
#     cafes = db.session.execute(query).scalars().all()
    
#     # if not filter_data or not cafes:
#     #     raise NotFound(description='No results found with the given parameters.')
#     # return cafes


