# -*- coding: utf-8 -*-
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import ModelWithID
from globaleaks.models.properties import *


class Node_v_28(ModelWithID):
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


class Context_v_28(ModelWithID):
    __tablename__ = 'context'
    show_small_cards = Column(BOOLEAN)
    show_context = Column(BOOLEAN)
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


class MigrationScript(MigrationBase):
    def migrate_Node(self):
        old_node = self.store_old.query(self.model_from['Node']).one()
        new_node = self.model_to['Node']()

        for key in [c.key for c in new_node.__table__.columns]:
            if key == 'disable_submissions':
                new_node.disable_submissions = False
            else:
                setattr(new_node, key, getattr(old_node, key))

        self.store_new.add(new_node)


    def migrate_Context(self):
        old_objs = self.store_old.query(self.model_from['Context'])
        for old_obj in old_objs:
            new_obj = self.model_to['Context']()
            for key in [c.key for c in new_obj.__table__.columns]:
                if key == 'show_steps_navigation_bar':
                    new_obj.show_steps_navigation_bar = True
                elif key == 'steps_navigation_requires_completion':
                    new_obj.steps_navigation_requires_completion = False
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.store_new.add(new_obj)
