"""
ORM Models definitions.
"""
from __future__ import absolute_import

import collections

from datetime import timedelta

from globaleaks.models.properties import *
from globaleaks.orm import transact
from globaleaks.rest import errors
from globaleaks.settings import Settings
from globaleaks.utils.utility import datetime_now, datetime_null, datetime_to_ISO8601, uuid4


def db_forge_obj(session, mock_class, mock_fields):
    obj = mock_class(mock_fields)
    session.add(obj)
    session.flush()
    return obj


@transact
def forge_obj(session, mock_class, mock_fields):
    return db_forge_obj(session, mock_class, mock_fields)


def db_get(session, model, *args, **kwargs):
    if isinstance(model, collections.Iterable):
        ret = session.query(*model).filter(*args, **kwargs).one_or_none()
    else:
        ret = session.query(model).filter(*args, **kwargs).one_or_none()

    if ret is None:
        raise errors.ModelNotFound(model)

    return ret


@transact
def get(session, model, *args, **kwargs):
    return db_get(session, model, *args, **kwargs)


def db_delete(session, model, *args, **kwargs):
    if isinstance(model, collections.Iterable):
        q = session.query(*model).filter(*args, **kwargs)
    else:
        q = session.query(model).filter(*args, **kwargs)

    return q.delete(synchronize_session='fetch')


@transact
def delete(session, model, *args, **kwargs):
    return db_delete(session, model, *args, **kwargs)



Base = declarative_base()


class Model(object):
    """
    Globaleaks's most basic model.

    Define a set of methods on the top of Storm to simplify
    creation/access/update/deletions of data.
    """
    # initialize empty list for the base classes
    properties = []
    unicode_keys = []
    localized_keys = []
    int_keys = []
    bool_keys = []
    datetime_keys = []
    json_keys = []
    date_keys = []
    optional_references = []
    list_keys = []

    def __init__(self, values=None, migrate=False):
        self.update(values)

        self.properties =  [c.key for c in self.__table__.columns]

    def update(self, values=None):
        """
        Updated Models attributes from dict.
        """
        if values is None:
            return

        if 'id' in values and values['id']:
            setattr(self, 'id', values['id'])

        if 'tid' in values and values['tid'] != '':
            setattr(self, 'tid', values['tid'])

        for k in getattr(self, 'unicode_keys'):
            if k in values and values[k] is not None:
                setattr(self, k, unicode(values[k]))

        for k in getattr(self, 'int_keys'):
            if k in values and values[k] is not None:
                setattr(self, k, int(values[k]))

        for k in getattr(self, 'datetime_keys'):
            if k in values and values[k] is not None:
                setattr(self, k, values[k])

        for k in getattr(self, 'bool_keys'):
            if k in values and values[k] is not None:
                if values[k] == u'true':
                    value = True
                elif values[k] == u'false':
                    value = False
                else:
                    value = bool(values[k])
                setattr(self, k, value)

        for k in getattr(self, 'localized_keys'):
            if k in values and values[k] is not None:
                value = values[k]
                previous = getattr(self, k)

                if previous and isinstance(previous, dict):
                    previous.update(value)
                    setattr(self, k, previous)
                else:
                    setattr(self, k, value)

        for k in getattr(self, 'json_keys'):
            if k in values and values[k] is not None:
                setattr(self, k, values[k])

        for k in getattr(self, 'optional_references'):
            if k in values and values[k]:
                setattr(self, k, values[k])

    def __str__(self):
        # pylint: disable=no-member
        values = ['{}={}'.format(attr, getattr(self, attr)) for attr in self.properties]
        return '<%s model with values %s>' % (self.__class__.__name__, ', '.join(values))

    def __repr__(self):
        return self.__str__()

    def __setattr__(self, name, value):
        # harder better faster stronger
        if isinstance(value, str):
            value = unicode(value)

        return super(Model, self).__setattr__(name, value)

    def dict(self, language):
        """
        Return a dictionary serialization of the current model.
        """
        ret = {}

        for k in self.properties:
            value = getattr(self, k)

            if value is not None:
                if k in self.localized_keys:
                    ret[k] = value[language] if language in value else u''

                elif k in self.date_keys:
                    ret[k] = datetime_to_ISO8601(value)
            else:
                if self.__table__.columns[k].default and not callable(self.__table__.columns[k].default.arg):
                    ret[k] = self.__table__.columns[k].default.arg
                else:
                    ret[k] = ''

        for k in self.list_keys:
            ret[k] = []

        return ret


class ModelWithID(Model):
    """
    Base class for working the database, already integrating an id.
    """
    id = Column(String, primary_key=True, default=uuid4)


class ModelWithTID(Model):
    """
    Base class for models requiring a TID
    """
    __tablename__ = None

    @declared_attr
    def tid(cls):
        # pylint: disable=no-self-argument
        return Column(ForeignKey('tenant.id', ondelete='CASCADE'), primary_key=True, default=1)


class ModelWithTIDandID(Model):
    """
    Base class for models requiring a TID and an ID
    """
    __tablename__ = None

    id = Column(String, primary_key=True, default=uuid4)

    @declared_attr
    def tid(cls):
        # pylint: disable=no-self-argument
        return Column(ForeignKey('tenant.id', ondelete='CASCADE'), primary_key=True, default=1)


class Tenant(ModelWithID, Base):
    """
    Class used to implement tenants
    """
    __tablename__ = 'tenant'
    id = Column(Integer, primary_key=True)
    label = Column(String, default=u'')
    active = Column(BOOLEAN, default=True)
    creation_date = Column(DATETIME, default=datetime_now)
    subdomain = Column(String, default=u'')

    unicode_keys = ['label', 'subdomain']
    bool_keys = ['active']


class User(ModelWithTIDandID, Base):
    """
    This model keeps track of globaleaks users.
    """
    __tablename__ = 'user'

    creation_date = Column(DATETIME, default=datetime_now)

    username = Column(String, default=u'')

    password = Column(String, default=u'')
    salt = Column(String)

    name = Column(String, default=u'')
    description = Column(JSON, default="dict")

    public_name = Column(String, default=u'')

    # roles: 'admin', 'receiver', 'custodian'
    role = Column(String, default=u'receiver')
    state = Column(String, default=u'enabled')
    last_login = Column(DATETIME, default=datetime_null)
    mail_address = Column(String, default=u'')
    language = Column(String)
    password_change_needed = Column(BOOLEAN, default=True)
    password_change_date = Column(DATETIME, default=datetime_null)

    # BEGIN of PGP key fields
    pgp_key_fingerprint = Column(String, default=u'')
    pgp_key_public = Column(String, default=u'')
    pgp_key_expiration = Column(DATETIME, default=datetime_null)
    # END of PGP key fields

    __table_args__ = (CheckConstraint(role.in_(['admin','receiver', 'custodian'])), \
                      CheckConstraint(state.in_(['disabled', 'enabled'])))

    unicode_keys = ['username', 'role', 'state',
                    'language', 'mail_address', 'name',
                    'public_name', 'language']

    localized_keys = ['description']

    bool_keys = ['password_change_needed']

    date_keys = ['creation_date', 'last_login', 'password_change_date', 'pgp_key_expiration']


class Context(ModelWithTIDandID, Base):
    """
    This model keeps track of contexts settings.
    """
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
    enable_attachments = Column(BOOLEAN, default=True) # Lets WB attach files to submission
    enable_rc_to_wb_files = Column(BOOLEAN, default=False) # The name says it all folks

    tip_timetolive = Column(Integer, default=15) # in days, -1 indicates no expiration

    # localized strings
    name = Column(JSON, default=dict)
    description = Column(JSON, default=dict)
    recipients_clarification = Column(JSON, default=dict)

    status_page_message = Column(JSON, default=dict)

    show_receivers_in_alphabetical_order = Column(BOOLEAN, default=True)

    presentation_order = Column(Integer, default=0)

    questionnaire_id = Column(String, default=u'default')

    unicode_keys = ['questionnaire_id']

    localized_keys = ['name', 'description', 'recipients_clarification', 'status_page_message']

    int_keys = [
      'tip_timetolive',
      'maximum_selectable_receivers',
      'presentation_order'
    ]

    bool_keys = [
      'select_all_receivers',
      'show_small_receiver_cards',
      'show_context',
      'show_recipients_details',
      'show_receivers_in_alphabetical_order',
      'allow_recipients_selection',
      'enable_comments',
      'enable_messages',
      'enable_two_way_comments',
      'enable_two_way_messages',
      'enable_attachments',
      'enable_rc_to_wb_files'
    ]

    list_keys = ['receivers']


class InternalTip(ModelWithTIDandID, Base):
    """
    This is the internal representation of a Tip that has been submitted
    """
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

    receipt_hash = Column(String, default=u'')

    wb_last_access = Column(DATETIME, default=datetime_now)
    wb_access_counter = Column(Integer, default=0)

    __table_args__ = (ForeignKeyConstraint(['tid', 'context_id'], ['context.tid', 'context.id'], ondelete='CASCADE'), )


class ReceiverTip(ModelWithTIDandID, Base):
    """
    This is the table keeping track of ALL the receivers activities and
    date in a Tip, Tip core data are stored in StoredTip. The data here
    provide accountability of Receiver accesses, operations, options.
    """
    __tablename__ = 'receivertip'

    internaltip_id = Column(String)
    receiver_id = Column(String)

    last_access = Column(DATETIME, default=datetime_null)
    access_counter = Column(Integer, default=0)

    label = Column(String, default=u'')

    can_access_whistleblower_identity = Column(BOOLEAN, default=False)

    new = Column(Integer, default=True)

    enable_notifications = Column(BOOLEAN, default=True)

    __table_args__ = (ForeignKeyConstraint(['tid', 'internaltip_id'], ['internaltip.tid', 'internaltip.id'], ondelete='CASCADE'),
                      ForeignKeyConstraint(['tid', 'receiver_id'], ['receiver.tid', 'receiver.id'], ondelete='CASCADE'))

    unicode_keys = ['label']

    bool_keys = ['enable_notifications']


class IdentityAccessRequest(ModelWithTIDandID, Base):
    """
    This model keeps track of identity access requests by receivers and
    of the answers by custodians.
    """
    __tablename__ = 'identityaccessrequest'
    receivertip_id = Column(String)
    request_date = Column(DATETIME, default=datetime_now)
    request_motivation = Column(String, default=u'')
    reply_date = Column(DATETIME, default=datetime_null)
    reply_user_id = Column(String, default=u'')
    reply_motivation = Column(String, default=u'')
    reply = Column(String, default=u'pending')

    __table_args__ = (ForeignKeyConstraint(['tid', 'receivertip_id'], ['receivertip.tid', 'receivertip.id'], ondelete='CASCADE'),)


class InternalFile(ModelWithTIDandID, Base):
    """
    This model keeps track of submission files
    """
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

    __table_args__ = (ForeignKeyConstraint(['tid', 'internaltip_id'], ['internaltip.tid', 'internaltip.id'], ondelete='CASCADE'),)


class ReceiverFile(ModelWithTIDandID, Base):
    """
    This model keeps track of files destinated to a specific receiver
    """
    __tablename__ = 'receiverfile'
    internalfile_id = Column(String)
    receivertip_id = Column(String)
    file_path = Column(String)
    size = Column(Integer)
    downloads = Column(Integer, default=0)
    last_access = Column(DATETIME, default=datetime_null)

    new = Column(Integer, default=True)

    status = Column(String)
    # statuses: 'reference', 'encrypted', 'unavailable', 'nokey'
    # reference = receiverfile.file_path reference internalfile.file_path
    # encrypted = receiverfile.file_path is an encrypted file for
    #                                    the specific receiver
    # unavailable = the file was supposed to be available but something goes
    # wrong and now is lost

    __table_args__ = (ForeignKeyConstraint(['tid', 'internalfile_id'], ['internalfile.tid', 'internalfile.id'], ondelete='CASCADE'),
                      ForeignKeyConstraint(['tid', 'receivertip_id'], ['receivertip.tid', 'receivertip.id'], ondelete='CASCADE'),
                      CheckConstraint(status.in_(['processing', 'reference', 'encrypted', 'unavailable', 'nokey'])))


class WhistleblowerFile(ModelWithTIDandID, Base):
    """
    This models stores metadata of files uploaded by recipients intended to be
    delivered to the whistleblower. This file is not encrypted and nor is it
    integrity checked in any meaningful way.
    """
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

    __table_args__ = (ForeignKeyConstraint(['tid', 'receivertip_id'], ['receivertip.tid', 'receivertip.id'], ondelete='CASCADE'),)


class Comment(ModelWithTIDandID, Base):
    """
    This table handle the comment collection, has an InternalTip referenced
    """
    __tablename__ = 'comment'
    creation_date = Column(DATETIME, default=datetime_now)

    internaltip_id = Column(String)

    author_id = Column(String)
    content = Column(String)

    type = Column(String)
    # types: 'receiver', 'whistleblower'

    new = Column(Integer, default=True)

    __table_args__ = (ForeignKeyConstraint(['tid', 'internaltip_id'], ['internaltip.tid', 'internaltip.id'], ondelete='CASCADE'),
                      ForeignKeyConstraint(['tid', 'author_id'], ['user.tid', 'user.id'], ondelete='CASCADE'))


class Message(ModelWithTIDandID, Base):
    """
    This table handle the direct messages between whistleblower and one
    Receiver.
    """
    __tablename__ = 'message'
    creation_date = Column(DATETIME, default=datetime_now)

    receivertip_id = Column(String)
    content = Column(String)

    type = Column(String)
    # types: 'receiver', whistleblower'

    new = Column(Integer, default=True)

    __table_args__ = (ForeignKeyConstraint(['tid', 'receivertip_id'], ['receivertip.tid', 'receivertip.id'], ondelete='CASCADE'),
                      CheckConstraint(type.in_(['receiver', 'whistleblower'])))


class Mail(ModelWithTIDandID, Base):
    """
    This model keeps track of emails to be spooled by the system
    """
    __tablename__ = 'mail'
    creation_date = Column(DATETIME, default=datetime_now)

    address = Column(String)
    subject = Column(String)
    body = Column(String)

    processing_attempts = Column(Integer, default=0)

    unicode_keys = ['address', 'subject', 'body']


class Receiver(ModelWithTID, Base):
    """
    This model keeps track of receivers settings.
    """
    __tablename__ = 'receiver'

    id = Column(String, primary_key=True)

    configuration = Column(String, default=u'default')
    # configurations: 'default', 'forcefully_selected', 'unselectable'

    # Admin chosen options
    can_delete_submission = Column(BOOLEAN, default=False)
    can_postpone_expiration = Column(BOOLEAN, default=False)
    can_grant_permissions = Column(BOOLEAN, default=False)

    tip_notification = Column(BOOLEAN, default=True)

    __table_args__ = (ForeignKeyConstraint(['tid', 'id'], ['user.tid', 'user.id'], ondelete='CASCADE'),
                      CheckConstraint(configuration.in_(['default', 'forcefully_selected', 'unselectable'])))

    unicode_keys = ['configuration']

    bool_keys = [
        'can_delete_submission',
        'can_postpone_expiration',
        'can_grant_permissions',
        'tip_notification',
    ]

    list_keys = ['contexts']


class Field(ModelWithTIDandID, Base):
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

    # This is set if the field should be duplicated for collecting statistics
    # when encryption is enabled.
    stats_enabled = Column(BOOLEAN, default=False)

    triggered_by_score = Column(Integer, default=0)

    fieldgroup_id = Column(String)
    step_id = Column(String)
    template_id = Column(String)

    type = Column(String, default=u'inputbox')

    instance = Column(String, default=u'instance')
    editable = Column(BOOLEAN, default=True)

    __table_args__ = (ForeignKeyConstraint(['tid', 'step_id'], ['step.tid', 'step.id'], ondelete='CASCADE'),
                      ForeignKeyConstraint(['tid', 'fieldgroup_id'], ['field.tid', 'field.id'], ondelete='CASCADE'),
                      ForeignKeyConstraint(['tid', 'template_id'], ['field.tid', 'field.id'], ondelete='CASCADE'),
                      CheckConstraint(type.in_(['inputbox',
                                                'textarea',
                                                'multichoice',
                                                'selectbox',
                                                'checkbox',
                                                'modal',
                                                'dialog',
                                                'tos',
                                                'fileupload',
                                                'number',
                                                'date',
                                                'email',
                                                'fieldgroup'])), \
                      CheckConstraint(instance.in_(['instance',
                                                    'reference',
                                                    'template'])),
                      CheckConstraint("((instance IS 'instance' AND template_id IS NULL AND \
                                                                    ((step_id IS NOT NULL AND fieldgroup_id IS NULL) OR \
                                                                    (step_id IS NULL AND fieldgroup_id IS NOT NULL))) OR \
                                        (instance IS 'reference' AND template_id is NOT NULL AND \
                                                                     ((step_id IS NOT NULL AND fieldgroup_id IS NULL) OR \
                                                                     (step_id IS NULL AND fieldgroup_id IS NOT NULL))) OR \
                                        (instance IS 'template' AND template_id IS NULL AND \
                                                                    (step_id IS NULL OR fieldgroup_id IS NULL)))"))

    unicode_keys = ['type', 'instance', 'key']
    int_keys = ['x', 'y', 'width', 'triggered_by_score']
    localized_keys = ['label', 'description', 'hint', 'multi_entry_hint']
    bool_keys = ['editable', 'multi_entry', 'preview', 'required', 'stats_enabled']
    optional_references = ['template_id', 'step_id', 'fieldgroup_id']


class FieldAttr(ModelWithTIDandID, Base):
    __tablename__ = 'fieldattr'
    field_id = Column(String)
    name = Column(String)
    type = Column(String)
    value = Column(JSON)

    __table_args__ = (ForeignKeyConstraint(['tid', 'field_id'], ['field.tid', 'field.id'], ondelete='CASCADE'),
                      CheckConstraint(type.in_(['int',
                                                'bool',
                                                'unicode',
                                                'localized'])),)

    # FieldAttr is a special model.
    # Here we consider all its attributes as unicode, then
    # depending on the type we handle the value as a localized value
    unicode_keys = ['field_id', 'name', 'type']

    def update(self, values=None):
        """
        Updated ModelWithIDs attributes from dict.
        """
        super(FieldAttr, self).update(values)

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


class FieldOption(ModelWithTIDandID, Base):
    __tablename__ = 'fieldoption'
    field_id = Column(String)
    presentation_order = Column(Integer, default=0)
    label = Column(JSON)
    score_points = Column(Integer, default=0)
    trigger_field = Column(String)

    __table_args__ = (ForeignKeyConstraint(['tid', 'field_id'], ['field.tid', 'field.id'], ondelete='CASCADE'),
                      ForeignKeyConstraint(['tid', 'trigger_field'], ['field.tid', 'field.id'], ondelete='CASCADE'))

    unicode_keys = ['field_id']
    int_keys = ['presentation_order', 'score_points']
    localized_keys = ['label']
    optional_references = ['trigger_field']


class FieldAnswer(ModelWithTIDandID, Base):
    __tablename__ = 'fieldanswer'
    internaltip_id = Column(String)
    fieldanswergroup_id = Column(String)
    key = Column(String, default=u'')
    is_leaf = Column(BOOLEAN, default=True)
    value = Column(String, default=u'')

    __table_args__ = (ForeignKeyConstraint(['tid', 'internaltip_id'], ['internaltip.tid', 'internaltip.id'], ondelete='CASCADE'),
                      ForeignKeyConstraint(['tid', 'fieldanswergroup_id'], ['fieldanswergroup.tid', 'fieldanswergroup.id'], ondelete='CASCADE'))

    unicode_keys = ['internaltip_id', 'key', 'value']
    bool_keys = ['is_leaf']


class FieldAnswerGroup(ModelWithTIDandID, Base):
    __tablename__ = 'fieldanswergroup'
    number = Column(Integer, default=0)
    fieldanswer_id = Column(String)

    __table_args__ = (ForeignKeyConstraint(['tid', 'fieldanswer_id'], ['fieldanswer.tid', 'fieldanswer.id'], ondelete='CASCADE'),)

    unicode_keys = ['fieldanswer_id']
    int_keys = ['number']


class Step(ModelWithTIDandID, Base):
    __tablename__ = 'step'
    questionnaire_id = Column(String)
    label = Column(JSON)
    description = Column(JSON)
    presentation_order = Column(Integer, default=0)

    __table_args__ = (ForeignKeyConstraint(['tid', 'questionnaire_id'], ['questionnaire.tid', 'questionnaire.id'], ondelete='CASCADE'),)

    unicode_keys = ['questionnaire_id']
    int_keys = ['presentation_order']
    localized_keys = ['label', 'description']


class Questionnaire(ModelWithTIDandID, Base):
    __tablename__ = 'questionnaire'
    name = Column(String, default=u'')
    enable_whistleblower_identity = Column(BOOLEAN, default=False)
    editable = Column(BOOLEAN, default=True)

    # TODO: this variables are unused and should be removed at next migration
    show_steps_navigation_bar = Column(BOOLEAN, default=False)
    steps_navigation_requires_completion = Column(BOOLEAN, default=False)

    unicode_keys = ['name']
    bool_keys = ['editable']
    list_keys = ['steps']


class ArchivedSchema(Model, Base):
    __tablename__ = 'archivedschema'
    hash = Column(String, primary_key=True)
    type = Column(String, primary_key=True)
    schema = Column(JSON)

    unicode_keys = ['hash']


class Stats(ModelWithTIDandID, Base):
    __tablename__ = 'stats'
    start = Column(DATETIME)
    summary = Column(JSON)


class Anomalies(ModelWithTIDandID, Base):
    __tablename__ = 'anomalies'
    date = Column(DATETIME)
    alarm = Column(Integer)
    events = Column(JSON)


class SecureFileDelete(Model, Base):
    __tablename__ = 'securefiledelete'
    filepath = Column(String, primary_key=True)


# Follow classes used for Many to Many references
class ReceiverContext(ModelWithTID, Base):
    """
    Class used to implement references between Receivers and Contexts
    """
    __tablename__ = 'receiver_context'

    context_id = Column(String, primary_key=True)
    receiver_id = Column(String, primary_key=True)
    presentation_order = Column(Integer, default=0)

    __table_args__ = (ForeignKeyConstraint(['tid', 'context_id'], ['context.tid', 'context.id'], ondelete='CASCADE'),
                      ForeignKeyConstraint(['tid', 'receiver_id'], ['receiver.tid', 'receiver.id'], ondelete='CASCADE'))

    unicode_keys = ['context_id', 'receiver_id']
    int_keys = ['presentation_order']


class Counter(ModelWithTID, Base):
    """
    Class used to implement unique counters
    """
    __tablename__ = 'counter'
    key = Column(String, primary_key=True)
    counter = Column(Integer, default=1)
    update_date = Column(DATETIME, default=datetime_now)

    unicode_keys = ['key']
    int_keys = ['number']


class ShortURL(ModelWithTIDandID, Base):
    """
    Class used to implement url shorteners
    """
    __tablename__ = 'shorturl'
    shorturl = Column(String)
    longurl = Column(String)

    unicode_keys = ['shorturl', 'longurl']


class File(ModelWithTIDandID, Base):
    """
    Class used for storing files
    """
    __tablename__ = 'file'
    name = Column(String, default=u'')
    data = Column(String, default=u'')

    unicode_keys = ['data', 'name']


class UserImg(ModelWithTIDandID, Base):
    """
    Class used for storing user pictures
    """
    __tablename__ = 'userimg'
    data = Column(String)

    unicode_keys = ['data']


class ContextImg(ModelWithTIDandID, Base):
    """
    Class used for storing context pictures
    """
    __tablename__ = 'contextimg'
    data = Column(String)

    unicode_keys = ['data']


class CustomTexts(ModelWithTID, Base):
    """
    Class used to implement custom texts
    """
    __tablename__ = 'customtexts'
    lang = Column(String, primary_key=True)
    texts = Column(JSON)

    unicode_keys = ['lang']
    json_keys = ['texts']
