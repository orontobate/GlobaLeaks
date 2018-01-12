# -*- coding: utf-8 -*-
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import ModelWithID
from globaleaks.models.properties import *


class InternalFile_v_25(ModelWithID):
    __tablename__ = 'internalfile'
    creation_date = Column(DATETIME)
    internaltip_id = Column(String)
    name = Column(String)
    file_path = Column(String)
    content_type = Column(String)
    size = Column(Integer)
    new = Column(Integer)
    processing_attempts = Column(Integer)


class MigrationScript(MigrationBase):
    def migrate_InternalFile(self):
        old_objs = self.store_old.query(self.model_from['InternalFile'])
        for old_obj in old_objs:
            new_obj = self.model_to['InternalFile']()
            for key in [c.key for c in new_obj.__table__.columns]:
                if key == 'submission':
                    new_obj.submission = True
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.store_new.add(new_obj)
