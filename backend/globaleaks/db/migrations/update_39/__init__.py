#i -*- coding: UTF-8
import os
import shutil

from globaleaks.db.migrations.update import MigrationBase
from globaleaks.db.migrations.update_37.config_desc import GLConfig
from globaleaks.handlers.admin import tenant
from globaleaks.models import *
from globaleaks.models import config_desc
from globaleaks.models.properties import *
from globaleaks.settings import Settings
from globaleaks.utils.utility import datetime_now, uuid4


class Anomalies_v_38(ModelWithID):
    __tablename__ = 'anomalies'
    date = Column(DATETIME)
    alarm = Column(Integer)
    events = Column(JSON)


class ArchivedSchema_v_38(Model):
    __tablename__ = 'archivedschema'
    hash = Column(String, primary_key=True)
    type = Column(String, primary_key=True)
    schema = Column(JSON)


class Comment_v_38(ModelWithID):
    __tablename__ = 'comment'
    creation_date = Column(DATETIME, default=datetime_now)
    internaltip_id = Column(String)
    author_id = Column(String)
    content = Column(String)
    type = Column(String)
    new = Column(Integer, default=True)


class Config_v_38(Model):
    __tablename__ = 'config'

    cfg_desc = GLConfig
    var_group = Column(String, primary_key=True)
    var_name = Column(String, primary_key=True)
    value = Column(JSON)
    customized = Column(BOOLEAN, default=False)

    def __init__(self, group=None, name=None, value=None, cfg_desc=None, migrate=False):
        if cfg_desc is not None:
            self.cfg_desc = cfg_desc

        if migrate:
            return

        self.var_group = unicode(group)
        self.var_name = unicode(name)

        self.set_v(value)

    @staticmethod
    def find_descriptor(config_desc_root, var_group, var_name):
        d = config_desc_root.get(var_group, {}).get(var_name, None)
        if d is None:
            raise ValueError('%s.%s descriptor cannot be None' % (var_group, var_name))

        return d

    def set_v(self, val):
        desc = self.find_descriptor(self.cfg_desc, self.var_group, self.var_name)
        if val is None:
            val = desc._type()
        if isinstance(desc, config_desc.Unicode) and isinstance(val, str):
            val = unicode(val)
        if not isinstance(val, desc._type):
            raise ValueError("Cannot assign %s with %s" % (self, type(val)))

        if self.value is None:
            self.value = {'v': val}

        elif self.value['v'] != val:
            self.customized = True
            self.value = {'v': val}

    def get_v(self):
        return self.value['v']

    def __repr__(self):
        return "<Config: %s.%s>" % (self.var_group, self.var_name)


class ConfigL10N_v_38(Model):
    __tablename__ = 'config_l10n'

    lang = Column(String, primary_key=True)
    var_group = Column(String, primary_key=True)
    var_name = Column(String, primary_key=True)
    value = Column(String)
    customized = Column(BOOLEAN, default=False)

    def __init__(self, lang_code=None, group=None, var_name=None, value='', migrate=False):
        if migrate:
            return

        self.lang = unicode(lang_code)
        self.var_group = unicode(group)
        self.var_name = unicode(var_name)
        self.value = unicode(value)


    def set_v(self, value):
        value = unicode(value)
        if self.value != value:
            self.value = value
            self.customized = True


class Context_v_38(ModelWithID):
    __tablename__ = 'context'

    show_small_receiver_cards = Column(BOOLEAN, default=False)
    show_context = Column(BOOLEAN, default=True)
    show_recipients_details = Column(BOOLEAN, default=False)
    allow_recipients_selection = Column(BOOLEAN, default=False)
    maximum_selectable_receivers = Column(Integer, default=0)
    select_all_receivers = Column(BOOLEAN, default=True)
    enable_comments = Column(BOOLEAN, default=True)
    enable_messages = Column(BOOLEAN, default=False)
    enable_two_way_comments = Column(BOOLEAN, default=True)
    enable_two_way_messages = Column(BOOLEAN, default=True)
    enable_attachments = Column(BOOLEAN, default=True)
    enable_rc_to_wb_files = Column(BOOLEAN, default=False)
    tip_timetolive = Column(Integer, default=15)
    name = Column(JSON)
    description = Column(JSON)
    recipients_clarification = Column(JSON)
    status_page_message = Column(JSON)
    show_receivers_in_alphabetical_order = Column(BOOLEAN, default=False)
    presentation_order = Column(Integer, default=0)
    questionnaire_id = Column(String)
    img_id = Column(String)

class CustomTexts_v_38(Model):
    __tablename__ = 'customtexts'

    lang = Column(String, primary_key=True)
    texts = Column(JSON)


class Counter_v_38(Model):
    __tablename__ = 'counter'

    key = Column(String, primary_key=True)
    counter = Column(Integer, default=1)
    update_date = Column(DATETIME, default=datetime_now)


class EnabledLanguage_v_38(Model):
    __tablename__ = 'enabledlanguage'

    name = Column(String, primary_key=True)

    def __init__(self, name=None, migrate=False):
        if migrate:
            return

        self.name = unicode(name)

    @classmethod
    def list(cls, session):
        return [name for name in session.query(cls.name)]


class Field_v_38(ModelWithID):
    __tablename__ = 'field'

    x = Column(Integer, default=0)
    y = Column(Integer, default=0)
    width = Column(Integer, default=0)
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


class FieldAttr_v_38(ModelWithID):
    __tablename__ = 'fieldattr'
    field_id = Column(String)
    name = Column(String)
    type = Column(String)
    value = Column(JSON)

    def update(self, values=None):
        """
        Updated ModelWithIDs attributes from dict.
        """
        super(FieldAttr_v_38, self).update(values)

        if values is None:
            return

        if self.type == 'localized':
            value = values['value']
            previous = getattr(self, 'value')

            if previous and isinstance(previous, dict):
                previous.update(value)
            else:
                setattr(self, 'value', value)
        else:
            setattr(self, 'value', unicode(values['value']))


class FieldOption_v_38(ModelWithID):
    __tablename__ = 'fieldoption'
    field_id = Column(String)
    presentation_order = Column(Integer, default=0)
    label = Column(JSON)
    score_points = Column(Integer, default=0)
    trigger_field = Column(String)
    trigger_step = Column(String)


class FieldAnswer_v_38(ModelWithID):
    __tablename__ = 'fieldanswer'

    internaltip_id = Column(String)
    fieldanswergroup_id = Column(String)
    key = Column(String, default=u'')
    is_leaf = Column(BOOLEAN, default=True)
    value = Column(String, default=u'')


class FieldAnswerGroup_v_38(ModelWithID):
    __tablename__ = 'fieldanswergroup'

    number = Column(Integer, default=0)
    fieldanswer_id = Column(String)


class File_v_38(ModelWithID):
    __tablename__ = 'file'

    data = Column(String)


class InternalFile_v_38(ModelWithID):
    __tablename__ = 'internalfile'

    creation_date = Column(DATETIME, default=datetime_now)
    internaltip_id = Column(String)
    name = Column(String)
    file_path = Column(String)
    content_type = Column(String)
    size = Column(Integer)
    new = Column(Integer, default=True)
    submission = Column(Integer, default = False)
    processing_attempts = Column(Integer, default=0)


class InternalTip_v_38(ModelWithID):
    __tablename__ = 'internaltip'

    creation_date = Column(DATETIME, default=datetime_now)
    update_date = Column(DATETIME, default=datetime_now)
    context_id = Column(String)
    questionnaire_hash = Column(String)
    preview = Column(JSON)
    progressive = Column(Integer, default=0)
    tor2web = Column(BOOLEAN, default=False)
    total_score = Column(Integer, default=0)
    expiration_date = Column(DATETIME)
    identity_provided = Column(BOOLEAN, default=False)
    identity_provided_date = Column(DATETIME, default=datetime_null)
    enable_two_way_comments = Column(BOOLEAN, default=True)
    enable_two_way_messages = Column(BOOLEAN, default=True)
    enable_attachments = Column(BOOLEAN, default=True)
    enable_whistleblower_identity = Column(BOOLEAN, default=False)
    wb_last_access = Column(DATETIME, default=datetime_now)
    wb_access_counter = Column(Integer, default=0)


class Mail_v_38(ModelWithID):
    __tablename__ = 'mail'

    creation_date = Column(DATETIME, default=datetime_now)
    address = Column(String)
    subject = Column(String)
    body = Column(String)
    processing_attempts = Column(Integer, default=0)


class ReceiverTip_v_38(ModelWithID):
    __tablename__ = 'receivertip'

    internaltip_id = Column(String)
    receiver_id = Column(String)
    last_access = Column(DATETIME, default=datetime_null)
    access_counter = Column(Integer, default=0)
    label = Column(String, default=u'')
    can_access_whistleblower_identity = Column(BOOLEAN, default=False)
    new = Column(Integer, default=True)
    enable_notifications = Column(BOOLEAN, default=True)


class Receiver_v_38(ModelWithID):
    __tablename__ = 'receiver'

    configuration = Column(String, default=u'default')
    can_delete_submission = Column(BOOLEAN, default=False)
    can_postpone_expiration = Column(BOOLEAN, default=False)
    can_grant_permissions = Column(BOOLEAN, default=False)
    tip_notification = Column(BOOLEAN, default=True)
    presentation_order = Column(Integer, default=0)


class ReceiverContext_v_38(Model):
    __tablename__ = 'receiver_context'

    context_id = Column(String, primary_key=True)
    receiver_id = Column(String, primary_key=True)


class ReceiverFile_v_38(ModelWithID):
    __tablename__ = 'receiverfile'

    internalfile_id = Column(String)
    receivertip_id = Column(String)
    file_path = Column(String)
    size = Column(Integer)
    downloads = Column(Integer, default=0)
    last_access = Column(DATETIME, default=datetime_null)
    new = Column(Integer, default=True)
    status = Column(String)


class ShortURL_v_38(ModelWithID):
    __tablename__ = 'shorturl'

    shorturl = Column(String)
    longurl = Column(String)


class Stats_v_38(ModelWithID):
    __tablename__ = 'stats'

    start = Column(DATETIME)
    summary = Column(JSON)
    free_disk_space = Column(Integer)


class Step_v_38(ModelWithID):
    __tablename__ = 'step'
    questionnaire_id = Column(String)
    label = Column(JSON)
    description = Column(JSON)
    presentation_order = Column(Integer, default=0)
    triggered_by_score = Column(Integer, default=0)


class IdentityAccessRequest_v_38(ModelWithID):
    __tablename__ = 'identityaccessrequest'

    receivertip_id = Column(String)
    request_date = Column(DATETIME, default=datetime_now)
    request_motivation = Column(String, default=u'')
    reply_date = Column(DATETIME, default=datetime_null)
    reply_user_id = Column(String)
    reply_motivation = Column(String, default=u'')
    reply = Column(String, default=u'pending')


class Message_v_38(ModelWithID):
    __tablename__ = 'message'
    creation_date = Column(DATETIME, default=datetime_now)
    receivertip_id = Column(String)
    content = Column(String)
    type = Column(String)
    new = Column(Integer, default=True)


class Questionnaire_v_38(ModelWithID):
    __tablename__ = 'questionnaire'

    name = Column(String)
    show_steps_navigation_bar = Column(BOOLEAN, default=False)
    steps_navigation_requires_completion = Column(BOOLEAN, default=False)
    enable_whistleblower_identity = Column(BOOLEAN, default=False)
    editable = Column(BOOLEAN, default=True)


class User_v_38(ModelWithID):
    __tablename__ = 'user'

    creation_date = Column(DATETIME, default=datetime_now)
    username = Column(String, default=u'')
    password = Column(String, default=u'')
    salt = Column(String)
    deletable = Column(BOOLEAN, default=True)
    name = Column(String, default=u'')
    description = Column(JSON, default=dict)
    public_name = Column(String, default=u'')
    role = Column(String, default=u'receiver')
    state = Column(String, default=u'enabled')
    last_login = Column(DATETIME, default=datetime_null)
    mail_address = Column(String, default=u'')
    language = Column(String)
    password_change_needed = Column(BOOLEAN, default=True)
    password_change_date = Column(DATETIME, default=datetime_null)
    pgp_key_fingerprint = Column(String, default=u'')
    pgp_key_public = Column(String, default=u'')
    pgp_key_expiration = Column(DATETIME, default=datetime_null)
    img_id = Column(String)


class WhistleblowerTip_v_38(ModelWithID):
    __tablename__ = 'whistleblowertip'

    receipt_hash = Column(String)


class WhistleblowerFile_v_38(ModelWithID):
    __tablename__ = 'whistleblowerfile'

    receivertip_id = Column(String)
    name = Column(String)
    file_path = Column(String)
    size = Column(Integer)
    content_type = Column(String)
    downloads = Column(Integer, default=0)
    creation_date = Column(DATETIME, default=datetime_now)
    last_access = Column(DATETIME, default=datetime_null)
    description = Column(String)


class MigrationScript(MigrationBase):
    def migrate_InternalTip(self):
        used_presentation_order = []
        old_objs = self.store_old.query(self.model_from['InternalTip'])
        for old_obj in old_objs:
            new_obj = self.model_to['InternalTip']()
            for key in [c.key for c in new_obj.__table__.columns]:
                if key == 'tid':
                    new_obj.tid = 1
                elif key == 'receipt_hash':
                    wbtip = self.store_old.query(self.model_from['WhistleblowerTip']).filter(self.model_from['WhistleblowerTip'].id == old_obj.id).one()
                    new_obj.receipt_hash = wbtip.receipt_hash if wbtip is not None else u''
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.store_new.add(new_obj)

    def migrate_ReceiverContext(self):
        model_from = self.model_from['Receiver']
        used_presentation_order = []
        old_objs = self.store_old.query(self.model_from['ReceiverContext'])
        for old_obj in old_objs:
            new_obj = self.model_to['ReceiverContext']()
            for key in [c.key for c in new_obj.__table__.columns]:
                if key == 'tid':
                    new_obj.tid = 1
                elif key == 'presentation_order':
                    presentation_order = self.store_old.query(model_from).filter(model_from.id == old_obj.receiver_id).one().presentation_order
                    while presentation_order in used_presentation_order:
                        presentation_order += 1

                    used_presentation_order.append(presentation_order)
                    new_obj.presentation_order = presentation_order
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.store_new.add(new_obj)

    def migrate_File(self):
        old_objs = self.store_old.query(self.model_from['File'])
        for old_obj in old_objs:
            u = self.store_old.query(self.model_from['User']).filter(self.model_from['User'].img_id == old_obj.id).one_or_none()
            c = self.store_old.query(self.model_from['Context']).filter(self.model_from['User'].img_id == old_obj.id).one_or_none()
            if u is not None:
                new_obj = self.model_to['UserImg']()
                new_obj.id = u.id
                self.entries_count['UserImg'] += 1
                self.entries_count['File'] -= 1
            elif c is not None:
                new_obj = self.model_to['ContextImg']()
                new_obj.id = c.id
                self.entries_count['ContextImg'] += 1
                self.entries_count['File'] -= 1
            else:
                new_obj = self.model_to['File']()

            for key in [c.key for c in new_obj.__table__.columns]:
                if key == 'tid':
                    new_obj.tid = 1
                elif key == 'name':
                    new_obj.name = ''
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.store_new.add(new_obj)

    def migrate_File_XXX(self, XXX):
        old_objs = self.store_old.query(self.model_from[XXX])
        for old_obj in old_objs:
            new_obj = self.model_to[XXX]()

            for key in [c.key for c in new_obj.__table__.columns]:
                if key == 'tid':
                    new_obj.tid = 1
                elif key == 'file_path':
                    new_obj.file_path = old_obj.file_path.replace('files/submission', 'attachments')
                    try:
                        shutil.move(old_obj.file_path, new_obj.file_path)
                    except:
                        pass
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.store_new.add(new_obj)

    def migrate_InternalFile(self):
        return self.migrate_File_XXX('InternalFile')

    def migrate_ReceiverFile(self):
        return self.migrate_File_XXX('ReceiverFile')

    def migrate_WhistleblowerFile(self):
        return self.migrate_File_XXX('WhistleblowerFile')

    def epilogue(self):
        self.store_new.add(self.model_to['Tenant']({'label': ''}))

        static_path = os.path.abspath(os.path.join(Settings.working_path, 'files/static'))
        if os.path.exists(static_path):
            for filename in os.listdir(static_path):
                filepath = os.path.abspath(os.path.join(static_path, filename))
                if not os.path.isfile(filepath):
                    continue

                new_file = File()
                new_file.id = uuid4()
                new_file.name = filename
                new_file.data = u''
                self.store_new.add(new_file)
                shutil.move(filepath,
                            os.path.abspath(os.path.join(Settings.files_path, new_file.id)))

                self.entries_count['File'] += 1

        shutil.rmtree(os.path.abspath(os.path.join(Settings.working_path, 'files/static')), True)
        shutil.rmtree(os.path.abspath(os.path.join(Settings.working_path, 'files/submission')), True)
        shutil.rmtree(os.path.abspath(os.path.join(Settings.working_path, 'files/tmp')), True)

        try:
            # Depending of when the system was installed this directory may not exist
            shutil.rmtree(os.path.abspath(os.path.join(Settings.working_path, 'files/encrypted_upload')))
        except:
            pass
