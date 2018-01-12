# -*- coding: utf-8
from globaleaks import models
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models.properties import *
from globaleaks.settings import Settings
from globaleaks.utils.utility import datetime_now, datetime_null


class Context_v_34(models.ModelWithID):
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
    tip_timetolive = Column(Integer, default=15)
    name = Column(JSON)
    description = Column(JSON)
    recipients_clarification = Column(JSON)
    status_page_message = Column(JSON)
    show_receivers_in_alphabetical_order = Column(BOOLEAN, default=False)
    presentation_order = Column(Integer, default=0)
    questionnaire_id = Column(String)
    img_id = Column(String)


class WhistleblowerTip_v_34(models.ModelWithID):
    __tablename__ = 'whistleblowertip'
    internaltip_id = Column(String)
    receipt_hash = Column(String)
    access_counter = Column(Integer, default=0)


class InternalTip_v_34(models.ModelWithID):
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

class MigrationScript(MigrationBase):
    def migrate_Context(self):
        old_objs = self.store_old.query(self.model_from['Context'])
        for old_obj in old_objs:
            new_obj = self.model_to['Context']()
            for key in [c.key for c in new_obj.__table__.columns]:
                if key == 'tip_timetolive':
                    tip_ttl = 5 * 365
                    if old_obj.tip_timetolive > tip_ttl:
                        Settings.print_msg('[WARNING] Found an expiration date longer than 5 years! Configuring tips to never expire.')
                        # If data retention was larger than 5 years the intended goal was
                        # probably to keep the submission around forever.
                        new_obj.tip_timetolive = -1
                    elif old_obj.tip_timetolive < -1:
                        Settings.print_msg('[WARNING] Found a negative tip expiration! Configuring tips to never expire.')
                        new_obj.tip_timetolive = -1
                    else:
                        new_obj.tip_timetolive = old_obj.tip_timetolive
                    continue

                elif key == 'enable_rc_to_wb_files':
                    new_obj.enable_rc_to_wb_files = False

                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.store_new.add(new_obj)

    def migrate_User(self):
        default_language = self.store_new.query(self.model_to['Config']).filter(self.model_to['Config'].var_name == u'default_language').one().value['v']
        enabled_languages = [r[0] for r in self.store_old.query(self.model_to['EnabledLanguage'].name)]

        old_objs = self.store_old.query(self.model_from['User'])
        for old_obj in old_objs:
            new_obj = self.model_to['User']()
            for key in [c.key for c in new_obj.__table__.columns]:
                if key in ['pgp_key_public', 'pgp_key_fingerprint'] and getattr(old_obj, key) is None:
                    setattr(new_obj, key, '')

                elif key in ['pgp_key_expiration'] and getattr(old_obj, key) is None:
                    setattr(new_obj, key, datetime_null())

                elif key == 'language' and getattr(old_obj, key) not in enabled_languages:
                    # fix users that have configured a language that has never been there
                    setattr(new_obj, key, default_language)

                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.store_new.add(new_obj)

    def migrate_WhistleblowerTip(self):
        old_objs = self.store_old.query(self.model_from['WhistleblowerTip'])
        for old_obj in old_objs:
            new_obj = self.model_to['WhistleblowerTip']()
            for key in [c.key for c in new_obj.__table__.columns]:
                if key == 'id':
                    new_obj.id = old_obj.internaltip_id
                    continue

                setattr(new_obj, key, getattr(old_obj, key))

            self.store_new.add(new_obj)

    def epilogue(self):
        c = self.store_new.query(self.model_to['Config']).filter(self.model_to['Config'].var_name == u'wbtip_timetolive').one()
        if int(c.value['v']) < 5:
            c.value['v'] = 90
        elif int(c.value['v']) > 365 * 2:
            c.value['v'] = 365 * 2

        self.store_new.commit()
