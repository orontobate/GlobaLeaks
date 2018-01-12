# -*- coding: utf-8 -*-
from sqlalchemy import not_, Column, String, ForeignKeyConstraint
from sqlalchemy.dialects.sqlite import BOOLEAN

from globaleaks import LANGUAGES_SUPPORTED_CODES, models
from globaleaks.models import Base


class EnabledLanguage(models.ModelWithTID, Base):
    __tablename__ = 'enabledlanguage'

    name = Column(String, primary_key=True)

    def __init__(self, tid=1, name=None, migrate=False):
        if migrate:
            return

        self.tid = tid
        self.name = unicode(name)

    @classmethod
    def list(cls, session, tid):
        return [x[0] for x in session.query(EnabledLanguage.name).filter(EnabledLanguage.tid == tid)]

    @classmethod
    def tid_list(cls, session, tid_list):
        return [(lang.tid, lang.name) for lang in session.query(EnabledLanguage).filter(EnabledLanguage.tid.in_(tid_list)).order_by('tid', 'name')]

    @classmethod
    def add_new_lang(cls, session, tid, lang_code, appdata_dict):
        session.add(cls(tid, lang_code))
        session.flush()

        NodeL10NFactory(session, tid).initialize(lang_code, appdata_dict['node'])
        NotificationL10NFactory(session, tid).initialize(lang_code, appdata_dict['templates'])

    @classmethod
    def add_all_supported_langs(cls, session, tid, appdata_dict):
        for lang_code in LANGUAGES_SUPPORTED_CODES:
            cls.add_new_lang(session, tid, lang_code, appdata_dict)


class ConfigL10N(models.ModelWithTID, Base):
    __tablename__ = 'config_l10n'

    lang = Column(String, primary_key=True)
    var_name = Column(String, primary_key=True)
    value = Column(String)
    customized = Column(BOOLEAN, default=False)

    __table_args__ = (ForeignKeyConstraint(['tid', 'lang'], ['enabledlanguage.tid', 'enabledlanguage.name'], ondelete='CASCADE'), )

    def __init__(self, tid=1, lang_code=None, var_name=None, value='', migrate=False):
        if migrate:
            return

        self.tid = tid
        self.lang = unicode(lang_code)
        self.var_name = unicode(var_name)
        self.value = unicode(value)

    def set_v(self, value):
        value = unicode(value)
        if self.value != value:
            self.value = value
            self.customized = True


class ConfigL10NFactory(object):
    keys = []
    unmodifiable_keys = []
    modifiable_keys = []

    def __init__(self, session, tid):
        self.session = session
        self.tid = tid

    def initialize(self, lang_code, initialization_dict, keys=None):
        if keys is None:
            keys = self.keys

        for key in keys:
            value = initialization_dict[key][lang_code] if key in initialization_dict else ''
            self.session.add(ConfigL10N(self.tid, lang_code, key, value))

    def get_all(self, lang_code):
        return [r for r in self.session.query(ConfigL10N).filter(ConfigL10N.tid == self.tid, ConfigL10N.lang == lang_code, ConfigL10N.var_name.in_(list(self.keys)))]

    def localized_dict(self, lang_code):
        rows = self.get_all(lang_code)
        return {c.var_name : c.value for c in rows if c.var_name in self.keys}

    def update(self, request, lang_code):
        c_map = {c.var_name : c for c in self.get_all(lang_code)}

        for key in self.modifiable_keys:
            c_map[key].set_v(request[key])

    def update_defaults(self, langs, l10n_data_src, reset=False):
        for lang_code in langs:
            old_keys = []

            for cfg in self.get_all(lang_code):
                old_keys.append(cfg.var_name)
                if (not cfg.customized or reset or cfg.var_name in self.unmodifiable_keys) and cfg.var_name in l10n_data_src:
                    cfg.value = l10n_data_src[cfg.var_name][lang_code]

            ConfigL10NFactory.initialize(self, lang_code, l10n_data_src, list(set(self.keys) - set(old_keys)))

    def get_val(self, var_name, lang_code):
        return models.db_get(self.session, ConfigL10N, ConfigL10N.tid == self.tid, ConfigL10N.lang == lang_code, ConfigL10N.var_name == var_name).value

    def set_val(self, var_name, lang_code, value):
        cfg = self.session.query(ConfigL10N).filter(ConfigL10N.tid == self.tid, ConfigL10N.lang == lang_code, ConfigL10N.var_name == var_name).one()
        cfg.set_v(value)


class NodeL10NFactory(ConfigL10NFactory):
    keys = [
        u'description',
        u'presentation',
        u'footer',
        u'security_awareness_title',
        u'security_awareness_text',
        u'whistleblowing_question',
        u'whistleblowing_button',
        u'whistleblowing_receipt_prompt',
        u'custom_privacy_badge_tor',
        u'custom_privacy_badge_none',
        u'header_title_homepage',
        u'header_title_submissionpage',
        u'header_title_receiptpage',
        u'header_title_tippage',
        u'contexts_clarification',
        u'widget_comments_title',
        u'widget_messages_title',
        u'widget_files_title',
    ]

    modifiable_keys = keys


class NotificationL10NFactory(ConfigL10NFactory):
    keys = [
        u'admin_anomaly_mail_template',
        u'admin_anomaly_mail_title',
        u'admin_anomaly_disk_low',
        u'admin_anomaly_disk_high',
        u'admin_anomaly_activities',
        u'admin_pgp_alert_mail_template',
        u'admin_pgp_alert_mail_title',
        u'admin_test_mail_template',
        u'admin_test_mail_title',
        u'pgp_alert_mail_template',
        u'pgp_alert_mail_title',
        u'tip_mail_template',
        u'tip_mail_title',
        u'file_mail_template',
        u'file_mail_title',
        u'comment_mail_template',
        u'comment_mail_title',
        u'message_mail_template',
        u'message_mail_title',
        u'tip_expiration_summary_mail_template',
        u'tip_expiration_summary_mail_title',
        u'receiver_notification_limit_reached_mail_template',
        u'receiver_notification_limit_reached_mail_title',
        u'identity_access_authorized_mail_template',
        u'identity_access_authorized_mail_title',
        u'identity_access_denied_mail_template',
        u'identity_access_denied_mail_title',
        u'identity_access_request_mail_template',
        u'identity_access_request_mail_title',
        u'identity_provided_mail_template',
        u'identity_provided_mail_title',
        u'export_template',
        u'export_message_whistleblower',
        u'export_message_recipient',
        u'https_certificate_expiration_mail_template',
        u'https_certificate_expiration_mail_title',
        u'software_update_available_mail_template',
        u'software_update_available_mail_title',
    ]

    # These strings are not exposed in admin the interface for customization
    unmodifiable_keys = [
        u'identity_access_authorized_mail_template',
        u'identity_access_authorized_mail_title',
        u'identity_access_denied_mail_template',
        u'identity_access_denied_mail_title',
        u'identity_access_request_mail_template',
        u'identity_access_request_mail_title',
        u'identity_provided_mail_template',
        u'identity_provided_mail_title',
        u'export_template',
        u'export_message_whistleblower',
        u'export_message_recipient',
        u'admin_anomaly_mail_template',
        u'admin_anomaly_mail_title',
        u'admin_anomaly_activities',
        u'admin_anomaly_disk_high',
        u'admin_anomaly_disk_low',
        u'admin_test_mail_template',
        u'admin_test_mail_title',
        u'https_certificate_expiration_mail_template',
        u'https_certificate_expiration_mail_title'
    ]

    modifiable_keys = [item for item in keys if item not in unmodifiable_keys]

    def __init__(self, session, tid, *args, **kwargs):
        ConfigL10NFactory.__init__(self, session, tid, *args, **kwargs)

    def reset_templates(self, l10n_data_src):
        langs = EnabledLanguage.list(self.session, self.tid)
        self.update_defaults(langs, l10n_data_src, reset=True)


def update_defaults(session, tid, appdata):
    langs = EnabledLanguage.list(session, tid)

    session.query(ConfigL10N).filter(ConfigL10N.tid == tid,
                                     not_(ConfigL10N.var_name.in_(NodeL10NFactory.keys + NotificationL10NFactory.keys))).delete(synchronize_session='fetch')

    NodeL10NFactory(session, tid).update_defaults(langs, appdata['node'])
    NotificationL10NFactory(session, tid).update_defaults(langs, appdata['templates'])
