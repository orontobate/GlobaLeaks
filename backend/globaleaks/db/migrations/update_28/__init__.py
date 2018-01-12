# -*- coding: utf-8 -*-
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import ModelWithID, Model
from globaleaks.models.properties import *


class Field_v_27(ModelWithID):
    __tablename__ = 'field'
    x = Column(Integer)
    y = Column(Integer)
    width = Column(Integer)
    key = Column(String)
    label = Column(JSON)
    description = Column(JSON)
    hint = Column(JSON)
    required = Column(BOOLEAN)
    preview = Column(BOOLEAN)
    multi_entry = Column(BOOLEAN)
    multi_entry_hint = Column(JSON)
    stats_enabled = Column(BOOLEAN)
    activated_by_score = Column(Integer)
    template_id = Column(String)
    type = Column(String)
    instance = Column(String)
    editable = Column(BOOLEAN)


class Step_v_27(ModelWithID):
    __tablename__ = 'step'
    context_id = Column(String)
    label = Column(JSON)
    description = Column(JSON)
    presentation_order = Column(Integer)


class FieldOption_v_27(ModelWithID):
    __tablename__ = 'fieldoption'
    field_id = Column(String)
    presentation_order = Column(Integer)
    label = Column(JSON)
    score_points = Column(Integer)


class FieldField_v_27(Model):
    __tablename__ = 'field_field'

    parent_id = Column(String, primary_key=True)
    child_id = Column(String, primary_key=True)


class StepField_v_27(Model):
    __tablename__ = 'step_field'

    step_id = Column(String, primary_key=True)
    field_id = Column(String, primary_key=True)


class MigrationScript(MigrationBase):
    def migrate_Step(self):
        old_objs = self.store_old.query(self.model_from['Step'])
        for old_obj in old_objs:
            new_obj = self.model_to['Step']()
            for key in [c.key for c in new_obj.__table__.columns]:
                if key == 'triggered_by_score':
                    new_obj.triggered_by_score = 0
                    continue

                setattr(new_obj, key, getattr(old_obj, key))

            self.store_new.add(new_obj)

    def migrate_Field(self):
        old_objs = self.store_old.query(self.model_from['Field'])
        for old_obj in old_objs:
            new_obj = self.model_to['Field']()
            for key in [c.key for c in new_obj.__table__.columns]:
                if key == 'preview':
                    if old_obj.preview is None:
                        new_obj.preview = False
                    else:
                        new_obj.preview = old_obj.preview

                elif key == 'step_id':
                    sf = self.store_old.query(self.model_from['StepField']).filter(self.model_from['StepField'].field_id == old_obj.id).one_or_none()
                    if sf is not None:
                        new_obj.step_id = sf.step_id

                elif key == 'fieldgroup_id':
                    ff = self.store_old.query(self.model_from['FieldField']).filter(self.model_from['FieldField'].child_id == old_obj.id).one_or_none()
                    if ff is not None:
                        new_obj.fieldgroup_id = ff.parent_id

                elif key == 'triggered_by_score':
                    new_obj.triggered_by_score = 0

                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.store_new.add(new_obj)

    def migrate_FieldOption(self):
        old_objs = self.store_old.query(self.model_from['FieldOption'])
        for old_obj in old_objs:
            new_obj = self.model_to['FieldOption']()
            for key in [c.key for c in new_obj.__table__.columns]:
                if key not in ['trigger_field', 'trigger_step']:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.store_new.add(new_obj)
