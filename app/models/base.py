from sqlalchemy.orm import DeclarativeBase

# CREATE DB
class Base(DeclarativeBase):
    def as_dict(self):
        return {col.name: str(getattr(self, col.name)) for col in self.__table__.columns}
    def get_field_names(self):
        return [col.name for col in self.__table__.columns]
    # def get_field_types(self):
    #     return [col.type for col in self.__table__.columns]
    def update_cols(self, updates: dict):
        updated = {}
        for name, value in updates.items():
            for col in self.__table__.columns:
                if col.name == name:
                    setattr(self, col.name, value)
                    updated[col.name] = str(getattr(self, col.name))
                    break
        return updated


