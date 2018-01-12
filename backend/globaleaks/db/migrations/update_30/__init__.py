# -*- coding: utf-8 -*-
import os

from globaleaks.db.migrations.update import MigrationBase
from globaleaks.handlers.admin.field import db_create_field
from globaleaks.models import ModelWithID, Model
from globaleaks.models.properties import *
from globaleaks.settings import Settings


class Node_v_29(ModelWithID):
    __tablename__ = 'node'
    version = Column(String)
    version_db = Column(String)
    name = Column(String)
    public_site = Column(String)
    hidden_service = Column(String)
    receipt_salt = Column(String)
    languages_enabled = Column(JSON)
    default_language = Column(String)
    default_timezone = Column(Integer)
    description = Column(JSON)
    presentation = Column(JSON)
    footer = Column(JSON)
    security_awareness_title = Column(JSON)
    security_awareness_text = Column(JSON)
    context_selector_label = Column(JSON)
    maximum_namesize = Column(Integer)
    maximum_textsize = Column(Integer)
    maximum_filesize = Column(Integer)
    tor2web_admin = Column(BOOLEAN)
    tor2web_custodian = Column(BOOLEAN)
    tor2web_whistleblower = Column(BOOLEAN)
    tor2web_receiver = Column(BOOLEAN)
    tor2web_unauth = Column(BOOLEAN)
    allow_unencrypted = Column(BOOLEAN)
    allow_iframes_inclusion = Column(BOOLEAN)
    submission_minimum_delay = Column(Integer)
    submission_maximum_ttl = Column(Integer)
    can_postpone_expiration = Column(BOOLEAN)
    can_delete_submission = Column(BOOLEAN)
    can_grant_permissions = Column(BOOLEAN)
    ahmia = Column(BOOLEAN)
    wizard_done = Column(BOOLEAN)
    disable_submissions = Column(BOOLEAN)
    disable_privacy_badge = Column(BOOLEAN)
    disable_security_awareness_badge = Column(BOOLEAN)
    disable_security_awareness_questions = Column(BOOLEAN)
    disable_key_code_hint = Column(BOOLEAN)
    disable_donation_panel = Column(BOOLEAN)
    enable_captcha = Column(BOOLEAN)
    enable_proof_of_work = Column(BOOLEAN)
    enable_experimental_features = Column(BOOLEAN)
    whistleblowing_question = Column(JSON)
    whistleblowing_button = Column(JSON)
    simplified_login = Column(BOOLEAN)
    enable_custom_privacy_badge = Column(BOOLEAN)
    custom_privacy_badge_tor = Column(JSON)
    custom_privacy_badge_none = Column(JSON)
    header_title_homepage = Column(JSON)
    header_title_submissionpage = Column(JSON)
    header_title_receiptpage = Column(JSON)
    header_title_tippage = Column(JSON)
    widget_comments_title = Column(JSON)
    widget_messages_title = Column(JSON)
    widget_files_title = Column(JSON)
    landing_page = Column(String)
    show_contexts_in_alphabetical_order = Column(BOOLEAN)
    threshold_free_disk_megabytes_high = Column(Integer)
    threshold_free_disk_megabytes_medium = Column(Integer)
    threshold_free_disk_megabytes_low = Column(Integer)
    threshold_free_disk_percentage_high = Column(Integer)
    threshold_free_disk_percentage_medium = Column(Integer)
    threshold_free_disk_percentage_low = Column(Integer)


class Context_v_29(ModelWithID):
    __tablename__ = 'context'
    show_small_cards = Column(BOOLEAN)
    show_context = Column(BOOLEAN)
    show_steps_navigation_bar = Column(BOOLEAN)
    steps_navigation_requires_completion = Column(BOOLEAN)
    show_recipients_details = Column(BOOLEAN)
    allow_recipients_selection = Column(BOOLEAN)
    maximum_selectable_receivers = Column(Integer)
    select_all_receivers = Column(BOOLEAN)
    enable_comments = Column(BOOLEAN)
    enable_messages = Column(BOOLEAN)
    enable_two_way_comments = Column(BOOLEAN)
    enable_two_way_messages = Column(BOOLEAN)
    enable_attachments = Column(BOOLEAN)
    enable_whistleblower_identity = Column(BOOLEAN)
    tip_timetolive = Column(Integer)
    name = Column(JSON)
    description = Column(JSON)
    recipients_clarification = Column(JSON)
    questionnaire_layout = Column(String)
    show_receivers_in_alphabetical_order = Column(BOOLEAN)
    presentation_order = Column(Integer)


class Step_v_29(ModelWithID):
    __tablename__ = 'step'
    context_id = Column(String)
    label = Column(JSON)
    description = Column(JSON)
    presentation_order = Column(Integer)
    triggered_by_score = Column(Integer)


class FieldAnswer_v_29(ModelWithID):
    __tablename__ = 'fieldanswer'
    internaltip_id = Column(String)
    key = Column(String, default=u'')
    is_leaf = Column(BOOLEAN, default=True)
    value = Column(String, default=u'')


class FieldAnswerGroup_v_29(ModelWithID):
    __tablename__ = 'fieldanswergroup'
    number = Column(Integer, default=0)
    fieldanswer_id = Column(String)


class FieldAnswerGroupFieldAnswer_v_29(Model):
    __tablename__ = 'fieldanswergroup_fieldanswer'

    fieldanswergroup_id = Column(String, primary_key=True)
    fieldanswer_id = Column(String, primary_key=True)


class MigrationScript(MigrationBase):
    def migrate_Node(self):
        old_node = self.store_old.query(self.model_from['Node']).one()
        new_node = self.model_to['Node']()

        for key in [c.key for c in new_node.__table__.columns]:
            if key == 'disable_encryption_warnings':
                new_node.disable_encryption_warnings = False
                continue

            setattr(new_node, key, getattr(old_node, key))

        self.store_new.add(new_node)

    def migrate_FieldAnswer(self):
        old_objs = self.store_old.query(self.model_from['FieldAnswer'])
        for old_obj in old_objs:
            new_obj = self.model_to['FieldAnswer']()
            for key in [c.key for c in new_obj.__table__.columns]:
                if key == 'fieldanswergroup_id':
                    old_ref = self.store_old.query(self.model_from['FieldAnswerGroupFieldAnswer']) \
                                            .filter(self.model_from['FieldAnswerGroupFieldAnswer'].fieldanswer_id == old_obj.id).one_or_none()
                    if old_ref is not None:
                        new_obj.fieldanswergroup_id = old_ref.fieldanswergroup_id
                    continue

                setattr(new_obj, key, getattr(old_obj, key))

            self.store_new.add(new_obj)

    def migrate_Context(self):
        # Migrated in the epilogue
        pass

    def migrate_Step(self):
        # Migrated in the epilogue
        pass

    def epilogue(self):
        self.fail_on_count_mismatch['Step'] = False
        self.fail_on_count_mismatch['Field'] = False
        self.fail_on_count_mismatch['FieldOption'] = False
        self.fail_on_count_mismatch['FieldAttr'] = False

        default_language = self.store_old.query(self.model_from['Node']).one().default_language

        old_contexts = self.store_old.query(self.model_from['Context'])
        for old_context in old_contexts:
            map_on_default = False
            new_questionnaire_id = None

            for old_step in self.store_old.query(self.model_from['Step']).filter(self.model_from['Step'].context_id == old_context.id):
                if self.store_old.query(self.model_from['Field']).filter(self.model_from['Field'].step_id == old_step.id).count() != 4:
                    break

                for field in self.store_old.query(self.model_from['Field']).filter(self.model_from['Field'].step_id == old_step.id):
                    if 'en' in field.label and field.label['en'] == 'Short title':
                        map_on_default = True
                        break

                if map_on_default:
                    break

            if not map_on_default:
                new_questionnaire = self.model_to['Questionnaire']()
                new_questionnaire.name = old_context.name[default_language] if default_language in old_context.name else ''
                new_questionnaire.layout = old_context.questionnaire_layout
                new_questionnaire.show_steps_navigation_bar = old_context.show_steps_navigation_bar
                new_questionnaire.steps_navigation_requires_completion = old_context.steps_navigation_requires_completion
                new_questionnaire.enable_whistleblower_identity = old_context.enable_whistleblower_identity
                self.store_new.add(new_questionnaire)
                new_questionnaire_id = new_questionnaire.id

                for old_step in self.store_old.query(self.model_from['Step']).filter(self.model_from['Step'].context_id == old_context.id):
                    new_step = self.model_to['Step']()
                    for key in [c.key for c in new_step.__table__.columns]:
                        if key == 'questionnaire_id':
                            new_step.questionnaire_id = new_questionnaire.id
                        else:
                            setattr(new_step, key, getattr(old_step, key))

                    self.store_new.add(new_step)

            new_context = self.model_to['Context']()
            for key in [c.key for c in new_context.__table__.columns]:
                if key == 'status_page_message':
                    new_context.status_page_message = ''
                elif key == 'questionnaire_id':
                    if new_questionnaire_id is not None:
                        new_context.questionnaire_id = new_questionnaire_id
                else:
                    setattr(new_context, key, getattr(old_context, key))

            self.store_new.add(new_context)
