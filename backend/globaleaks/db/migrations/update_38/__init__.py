# -*- coding: utf-8
from globaleaks import models
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models.properties import *


old_keys = ["%NodeName%", "%HiddenService%", "%PublicSite%", "%ContextName%", "%RecipientName%", "%TipID%", "%TipNum%", "%TipLabel%", "%EventTime%", "%SubmissionDate%", "%ExpirationDate%", "%ExpirationWatch%", "%QuestionnaireAnswers%", "%Comments%", "%Messages%", "%TorURL%", "%T2WURL%", "%FileName%", "%FileSize%", "%Content%", "%ExpiringSubmissionCount%", "%EarliestExpirationDate%", "%PGPKeyInfoList%", "%PGPKeyInfo%", "%AnomalyDetailDisk%", "%AnomalyDetailActivities%", "%ActivityAlarmLevel%", "%ActivityDump%", "%NodeName%", "%FreeMemory%", "%TotalMemory%", "%ExpirationDate%", "%TipTorURL", "TipT2WURL"]


new_keys = ["{NodeName}", "{HiddenService}", "{PublicSite}", "{ContextName}", "{RecipientName}", "{TipID}", "{TipNum}", "{TipLabel}", "{EventTime}", "{SubmissionDate}", "{ExpirationDate}", "{ExpirationWatch}", "{QuestionnaireAnswers}", "{Comments}", "{Messages}", "{TorUrl}", "{HTTPSUrl}", "{FileName}", "{FileSize}", "{Content}", "{ExpiringSubmissionCount}", "{EarliestExpirationDate}", "{PGPKeyInfoList}", "{PGPKeyInfo}", "{AnomalyDetailDisk}", "{AnomalyDetailActivities}", "{ActivityAlarmLevel}", "{ActivityDump}", "{NodeName}", "{FreeMemory}", "{TotalMemory}", "{ExpirationDate}", "{TorUrl}", "{HTTPSUrl}"]


class Field_v_37(models.ModelWithID):
    __tablename__ = 'field'
    x = Column(Integer, default=0)
    y = Column(Integer, default=0)
    width = Column(Integer, default=0)
    key = Column(String, default=u'')
    label = Column(JSON)
    description = Column(JSON)
    hint = Column(JSON)
    required = Column(BOOLEAN, default=False)
    preview = Column(BOOLEAN, default=False)
    multi_entry = Column(BOOLEAN, default=False)
    multi_entry_hint = Column(JSON)
    stats_enabled = Column(BOOLEAN, default=False)
    triggered_by_score = Column(Integer, default=0)
    fieldgroup_id = Column(String)
    step_id = Column(String)
    template_id = Column(String)
    type = Column(String, default=u'inputbox')
    instance = Column(String, default=u'instance')
    editable = Column(BOOLEAN, default=True)


class Questionnaire_v_37(models.ModelWithID):
    __tablename__ = 'questionnaire'
    key = Column(String, default=u'')
    name = Column(String, default=u'')
    show_steps_navigation_bar = Column(BOOLEAN, default=False)
    steps_navigation_requires_completion = Column(BOOLEAN, default=False)
    enable_whistleblower_identity = Column(BOOLEAN, default=False)
    editable = Column(BOOLEAN, default=True)


def replace_templates_variables(value):
    for elem in enumerate(old_keys):
        value = value.replace(elem[1], new_keys[elem[0]])

    return value


class MigrationScript(MigrationBase):
    def migrate_ConfigL10N(self):
        old_objs = self.store_old.query(self.model_from['ConfigL10N'])
        for old_obj in old_objs:
            new_obj = self.model_to['ConfigL10N']()
            for key in [c.key for c in new_obj.__table__.columns]:
                value = getattr(old_obj, key)
                if key == 'value':
                    value = replace_templates_variables(value)

                setattr(new_obj, key, value)

            self.store_new.add(new_obj)

    def migrate_Context(self):
        questionnaire_default = self.store_old.query(self.model_from['Questionnaire']).filter(self.model_from['Questionnaire'].key == u'default').one_or_none()
        questionnaire_default_id = questionnaire_default.id if questionnaire_default is not None else 'hack'

        old_objs = self.store_old.query(self.model_from['Context'])
        for old_obj in old_objs:
            new_obj = self.model_to['Context']()
            for key in [c.key for c in new_obj.__table__.columns]:
                if key == 'questionnaire_id':
                    if old_obj.questionnaire_id is None or old_obj.questionnaire_id == questionnaire_default_id:
                        setattr(new_obj, 'questionnaire_id', u'default')
                    else:
                        setattr(new_obj, key, getattr(old_obj, key))
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.store_new.add(new_obj)

    def migrate_Field(self):
        field_wbi = self.store_old.query(self.model_from['Field']).filter(self.model_from['Field'].key == u'whistleblower_identity').one()
        field_wbi_id = field_wbi.id if field_wbi is not None else 'hack'

        old_objs = self.store_old.query(self.model_from['Field'])
        for old_obj in old_objs:
            new_obj = self.model_to['Field']()
            for key in [c.key for c in new_obj.__table__.columns]:
                setattr(new_obj, key, getattr(old_obj, key))

            if old_obj.key == 'whistleblower_identity':
                setattr(new_obj, 'id', 'whistleblower_identity')

            if old_obj.fieldgroup_id == field_wbi_id:
                setattr(new_obj, 'fieldgroup_id', 'whistleblower_identity')

            if old_obj.template_id == field_wbi_id:
                setattr(new_obj, 'template_id', 'whistleblower_identity')

            self.store_new.add(new_obj)

    def migrate_Questionnaire(self):
        old_objs = self.store_old.query(self.model_from['Questionnaire'])
        for old_obj in old_objs:
            new_obj = self.model_to['Questionnaire']()
            for key in [c.key for c in new_obj.__table__.columns]:
                setattr(new_obj, key, getattr(old_obj, key))

            if old_obj.key == 'default':
                setattr(new_obj, 'id', 'default')

            self.store_new.add(new_obj)
