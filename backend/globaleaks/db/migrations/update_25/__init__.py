# -*- coding: utf-8 -*-

from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import Model, ModelWithID
from globaleaks.models.properties import *
from globaleaks.security import sha512


class User_v_24(ModelWithID):
    __tablename__ = 'user'
    creation_date = Column(DATETIME)
    username = Column(String)
    password = Column(String)
    salt = Column(String)
    deletable = Column(BOOLEAN)
    name = Column(String)
    description = Column(JSON)
    role = Column(String)
    state = Column(String)
    last_login = Column(DATETIME)
    mail_address = Column(String)
    language = Column(String)
    timezone = Column(Integer)
    password_change_needed = Column(BOOLEAN)
    password_change_date = Column(DATETIME)
    pgp_key_info = Column(String)
    pgp_key_fingerprint = Column(String)
    pgp_key_public = Column(String)
    pgp_key_expiration = Column(DATETIME)
    pgp_key_status = Column(String)


class SecureFileDelete_v_24(Model):
    __tablename__ = 'securefiledelete'
    filepath = Column(String, primary_key=True)


class MigrationScript(MigrationBase):
    def migrate_Node(self):
        old_node = self.store_old.query(self.model_from['Node']).one()
        new_node = self.model_to['Node']()

        for key in [c.key for c in new_node.__table__.columns]:
            if key == 'receipt_salt':
                new_node.receipt_salt = sha512(old_node.receipt_salt.encode('utf8'))[:32]
                continue

            setattr(new_node, key, getattr(old_node, key))

        self.store_new.add(new_node)

    def migrate_User(self):
        old_objs = self.store_old.query(self.model_from['User'])
        for old_obj in old_objs:
            new_obj = self.model_to['User']()

            for key in [c.key for c in new_obj.__table__.columns]:
                if key == 'salt':
                    new_obj.salt = sha512(old_obj.salt.encode('utf8'))[:32]
                    continue

                setattr(new_obj, key, getattr(old_obj, key))

            self.store_new.add(new_obj)
