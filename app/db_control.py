from dateparser import parse
from sqlalchemy.exc import IntegrityError
from models.job_posts import JobPost, db
from filters_db import DbFilterGroup
from models.base import Base
from utils import get_salary_data_from_str
       
DEFAULT_SORT = [('id', 'asc')]


class DbControl:

    def __init__(self, db, db_model: Base):
        self.db = db
        self.model = db_model
        self.col_map = db_model.get_column_map(db_model)
    

    def get_one(self, id) -> JobPost:
        return db.get_or_404(self.model, id)
    


class JobDbControl(DbControl):

    def __init__(self, db):
        super().__init__(db=db, db_model=JobPost)


    def get_list(self, filter_group: DbFilterGroup=None, sort_by: list[list]=DEFAULT_SORT):           
        sort_by_list = self.sort_to_db_sort(sort_by)

        query = ''
        if filter_group is not None and filter_group:
            query = db.select(self.model).where(filter_group.op_expression()).order_by(*sort_by_list)

        else:
            query = db.select(self.model).order_by(*sort_by_list)

        jobs = db.session.execute(query).scalars().all()
        return jobs


    def get_post_ids(self, job_board):
        # Later TODO: Change this to use 'self.get_from_col(...)' instead
        query = self.db.select(JobPost.post_id).where(JobPost.job_board == job_board).order_by(JobPost.id)
        ids = self.db.session.execute(query).scalars().all()
        return ids
    

    def get_from_col(self, column: str, unique: bool=False, filter_group: DbFilterGroup=None, sort_by: list[tuple]=DEFAULT_SORT):
        sort_by_list = self.sort_to_db_sort(sort_by)

        query = ''
        if filter_group is None:
            query = self.db.select(self.col_map[column]).order_by(*sort_by_list)
        else:
            query = self.db.select(self.col_map[column]).where(filter_group.op_expression()).order_by(*sort_by_list)
        
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
            self.parse_and_format_fields(job)
        
            self.add_one(job)
        

    def update_one(self, id: int, updated_data: dict):
        job = self.get_one(id)
        
        data = {key: value for (key, value) in updated_data.items() if key not in ['id', 'created', 'post_id', 'post_link', 'posted_date']}
        
        if updated_data.get('posted_date'):
            # Date fixing -- probably not necessary, but implementing for now just in case keeping the time becomes relevant
            if job.posted_date:
                date = updated_data['posted_date'].split(' ')[0]
                time = job.posted_date.strftime('%H:%M:%S')
                date_str = f'{date} {time}'
            else:
                date_str = updated_data['posted_date']

            data['posted_date'] = self.str_date_to_obj(date_str)
        
            # Note: With current implementation, can't update posted_date to be empty value (e.g. if wanted to clear it for some reason)
        data = self.parse_and_format_fields(data)
        print('Updated data:\n', data)

        job.update_cols(data)
        self.db.session.commit()
        job = self.get_one(id)

        return job


    def delete_one(self, id: int):
        job = self.get_one(id)
        self.db.session.delete(job)
        self.db.session.commit()
        
        return job


    def str_date_to_obj(self, date):
        if type(date) is str:
            return parse(date, settings={'RETURN_AS_TIMEZONE_AWARE': True})
        return
    

    def sort_to_db_sort(self, sort: list[list]):
        # Later TODO (prob): Move this to a separate class (like did for filters in DBFilterGroups)
        db_sort_list = []
        for col_name, order in sort:
            order = order.lower().strip()
            
            if not order or order == 'asc':
                db_sort_list.append(self.col_map[col_name].asc())
            elif order == 'desc':
                db_sort_list.append(self.col_map[col_name].desc())
        
        return db_sort_list   


    def job_exists_where(self, job_id: str, filter_group: DbFilterGroup=None) -> bool:
        ''' 
        Checks whether a specific job, by id, matches a given group of filters. Useful for checking if a
        job that has been modified still belongs in a given view.
        '''

        exists_criteria = self.db.exists(JobPost.id).where(JobPost.id == job_id).where(filter_group.op_expression()).select()

        return self.db.session.execute(exists_criteria).scalar()


    def parse_and_format_fields(self, job: dict):
        posted_date = job.get('posted_date')
        if posted_date and type(posted_date) is str:
            job['posted_date'] = parse(posted_date, settings={'RETURN_AS_TIMEZONE_AWARE': True})

        salary = job.get('salary')
        if salary and not job.get('salary_low'):
            salary_data = get_salary_data_from_str(str(salary))
            new_fields = {
                'salary_currency': salary_data.currency,
                'salary_low': salary_data.range_low,
                'salary_high': salary_data.range_high
                }
            job.update(new_fields)
        
        return job


#------- Trash (temp) -------


# def filter_jobs(filters: dict = {}):
#     # allowed_filters = ['id']

#     filter_data = {key: value for (key, value) in filters.items() if value}
#     query = db.select(JobPost).filter_by(**filter_data).order_by(JobPost.id)
#     cafes = db.session.execute(query).scalars().all()
    
#     # if not filter_data or not cafes:
#     #     raise NotFound(description='No results found with the given parameters.')
#     # return cafes



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


    # def toggle_bool_field(self, id: int, field_name: str, value: bool):
    # # fields_types = self.model().get_field_types()

    # # boolean_fields = [field for field in fields_types.keys() if isinstance(fields_types[field], Boolean)]
    # # if field_name in boolean_fields:
    # job = self.get_one(id)

    # job.update_cols({field_name: value})
    
    # self.db.session.commit()
    # job = self.get_one(id)

    # return job
    # # self.update_one()