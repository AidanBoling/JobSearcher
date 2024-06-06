from dateparser import parse
from sqlalchemy.exc import IntegrityError
from models.job_posts import JobPost, db
from filters_db import DbFilterGroup
from models.base import Base

       
DEFAULT_SORT = 'id'



class DbControl:

    def __init__(self, db, db_model: Base):
        self.db = db
        self.model = db_model
        self.col_map = db_model.get_column_map(db_model)
    

    def get_one(self, id):
        return db.get_or_404(self.model, id)
    


class JobDbControl(DbControl):

    def __init__(self, db):
        super().__init__(db=db, db_model=JobPost)


    def get_list(self, filter_group: DbFilterGroup=None, sort_by: str=DEFAULT_SORT):   

        query = ''
        if filter_group is not None and filter_group:
            query = db.select(self.model).where(filter_group.op_expression()).order_by(self.col_map[sort_by])
        else:
            query = db.select(self.model).order_by(self.col_map[sort_by])
        
        jobs = db.session.execute(query).scalars().all()
        return jobs


    def get_post_ids(self, job_board):
        # Later TODO: Change this to use 'self.get_from_col(...)' instead
        query = self.db.select(JobPost.post_id).where(JobPost.job_board == job_board).order_by(JobPost.id)
        ids = self.db.session.execute(query).scalars().all()
        return ids
    

    def get_from_col(self, column: str, unique: bool=False, filter_group: DbFilterGroup=None, sort_by: str=DEFAULT_SORT):
        query = ''
        if filter_group is None:
            query = self.db.select(self.col_map[column]).order_by(self.col_map[sort_by])
        else:
            query = self.db.select(self.col_map[column]).where(filter_group.op_expression()).order_by(self.col_map[sort_by])
        
        if unique:
            return self.db.session.execute(query).unique().scalars().all()
        else:
            return self.db.session.execute(query).scalars().all()


    def add_one(self, job: dict):
        #Create new entry and add to db
        new_job_post = JobPost(**job)

        # TODO: Add more error handling...
        try:
            self.db.session.add(new_job_post)
            self.db.session.commit()
        except IntegrityError:
            # TODO: add logging
            # and make specific to NOT NULL constraint...
            pass

        # print(new_post.as_dict())

        return new_job_post


    def add_many(self, jobs: list):
        # TODO: Catch sqlalchemy.exc.IntegrityError -- log jobs that went wrong, and what data was missing/incorrectly formatted.
        
        for job in jobs:
            try:
                if type(job['posted_date']) is str:
                    job['posted_date'] = parse(job['posted_date'], settings={'RETURN_AS_TIMEZONE_AWARE': True})
            except KeyError:
                pass
        
            self.add_one(job)
        
    
    def update_one(self, id: int, updated_data: dict):
        job = self.get_one(id)
        
        data = {key: value for (key, value) in updated_data.items() if key not in ['id', 'created', 'post_id', 'post_link', 'posted_date']}
        
        if updated_data['posted_date']:
            # Date fixing -- probably not necessary, but implementing for now just in case keeping the time becomes relevant
            
            if job.posted_date:
                # get time from original date, add to data[posted_date] string, then str_to_obj
                date = updated_data['posted_date'].split(' ')[0]
                time = job.posted_date.strftime('%H:%M:%S')
                date_str = f'{date} {time}'
            else:
                date_str = updated_data['posted_date']

            data['posted_date'] = self.str_date_to_obj(date_str)
        
            # Note: With current implementation, can't update posted_date to be empty value (e.g. if wanted to clear it for some reason)

        print(data)
        job.update_cols(data)
        self.db.session.commit()


    def delete_one(self, id):
        job = self.get_one(id)
        self.db.session.delete(job)
        self.db.session.commit()


    def str_date_to_obj(self, date):
        try:
            if type(date) is str:
               return parse(date, settings={'RETURN_AS_TIMEZONE_AWARE': True})
        except KeyError:
            pass
        




#------- Trash (temp) -------


# def filter_jobs(filters: dict = {}):
#     # allowed_filters = ['id']

#     filter_data = {key: value for (key, value) in filters.items() if value}
#     query = db.select(JobPost).filter_by(**filter_data).order_by(JobPost.id)
#     cafes = db.session.execute(query).scalars().all()
    
#     # if not filter_data or not cafes:
#     #     raise NotFound(description='No results found with the given parameters.')
#     # return cafes



# def filter_jobs(self, filters: dict ={}, sort_by: str ='id'):
        
    #     filter_data = {key: value for (key, value) in filters.items() if value}
    #     query = db.select(JobPost).filter_by(**filter_data).order_by(self.col_map[sort_by])

    #     jobs = db.session.execute(query).scalars().all()
        
    #     # if not filter_data or not jobs:
    #     #     raise NotFound(description='No results found with the given parameters.')
    #     return jobs
    


        # filters = [JobDbFilter('employment_type', 'Full-time', '=='), JobDbFilter('job_board', 'LinkedIn', '==')]
        # # group_with_nested = DbFilterGroup([JobDbFilter(), filters], 'AND')   
        
        # operator = 'AND'
        # top_filter_group = DbFilterGroup(filters, operator)
        

        # filter_data = {key: value for (key, value) in filters.items() if value}
        # jobs = db.session.execute(query).scalars().all()
        
        
        # filter_group = { 'AND': [nested_filter_group], ('job_board', 'LinkedIn')],
        #     'OR': [],
        #     'NOT': []
        #     }

        # nested_filter_group = {'OR': [('employment_type', 'Remote'), ('employment_type', 'Remote')]}
        
        

        # def filter_group(method: str, filters: dict):
        # #     filter_stmts = []

        # #     for key, value in filters.items():
        # #         filter_stmts.append(key == value)

        #     if method == 'and':
        #         args = [mapped[filter_key] == filter_value, ????????]
        #         args = [filter, filter]
        #         filter.get().join(', ')
        #         stmt = select(JobPost).where(and_(mapped[filter_key] == filter_value, ????????))

        #     return stmnt


        # if not filter_data or not jobs:
        #     raise NotFound(description='No results found with the given parameters.')
        
        # return jobs


    # def get_all(self):
    #     # order_by_field
    #     query = db.select(JobPost).order_by(JobPost.id)
    #     all_posts = db.session.execute(query).scalars().all()
    #     return all_posts