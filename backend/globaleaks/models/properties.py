# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, CheckConstraint, ForeignKeyConstraint, types
from sqlalchemy.dialects.sqlite import BOOLEAN, DATETIME
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.schema import ForeignKey

import json
class StringyJSON(types.TypeDecorator):
    """Stores and retrieves JSON as TEXT."""

    impl = types.TEXT

    def process_bind_param(self, value, dialect): 
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value

JSON = types.TEXT().with_variant(StringyJSON, 'sqlite')
