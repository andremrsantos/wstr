import datetime

from enum import IntEnum
from peewee import Model
from peewee import CharField, IntegerField, BooleanField, DateTimeField, ForeignKeyField

from app import db
from app.names import get_name

class Base(Model):
    class Meta:
        database = db

class Task(Base):
    class Status (IntEnum):
        Queued   = 0
        Running  = 1
        Complete = 2
        Failure  = 3
        Canceled = 4
    name = CharField(default = get_name, null = False)
    submitter = CharField(null = False)
    status = IntegerField(default = int(Status.Queued))
    created_at = DateTimeField(default = datetime.datetime.now)
    updated_at = DateTimeField(default = datetime.datetime.now)

    def save(self, *args, **kwargs):
        self.updated_at = datetime.datetime.now()
        return super(Task, self).save(*args, **kwargs)

    @classmethod
    def recents(cls):
        now = datetime.datetime.now()
        last_week = now - datetime.timedelta(days = 7)
        return(Task
            .select()
            .where((Task.is_complete == False) | (Task.updated_at > last_week))
            .order_by(Task.updated_at.desc()))

class SampleCollection(Base):
    name = CharField(null = False)

class Sample(Base):
    name = CharField(null = False)
    collection = ForeignKeyField(SampleCollection, backref = "samples")

class VariantCollection(Base):
    name = CharField(null = False)

class Genotype(Base):
    HOMREF = 1
    HET = 2
    HOMALT = 3
    
    sample = ForeignKeyField(Sample, backref='genotypes')
    variant = ForeignKeyField(VariantCollection, backref='genotypes')
    name = CharField(null = False)
    value = IntegerField(null = False)

def migrate_tables():
    SampleCollection.create_table(True)
    VariantCollection.create_table(True)
    Sample.create_table(True)
    Genotype.create_table(True)
    # Clear previous task collection
    Task.drop_table(True)
    Task.create_table(True)
    with db.atomic():
        col = [
            {"name": "A", "submitter": "Me", "created_at": datetime.datetime.now() - datetime.timedelta(days = 3)},
            {"name": "B", "submitter": "Me", "is_complete": True},
            {"name": "C", "submitter": "Me", "created_at": datetime.datetime.now() - datetime.timedelta(days = 1)},
            {"name": "D", "submitter": "Me", "updated_at": datetime.datetime.now() - datetime.timedelta(days = 1)},
            {"name": "E", "submitter": "Me", "is_complete": True},
            {"submitter": "Me", "is_complete": True}
        ]
        Task.insert_many(col).execute()
