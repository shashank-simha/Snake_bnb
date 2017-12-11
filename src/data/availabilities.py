import mongoengine


class Availability(mongoengine.EmbeddedDocument):
    guest_owner_id = mongoengine.ObjectIdField()
    guest_snake_id = mongoengine.ObjectIdField()

    added_date = mongoengine.DateTimeField()
    from_date = mongoengine.DateTimeField(required=True)
    to_date = mongoengine.DateTimeField(required=True)

    @property
    def duration_in_days(self):
        dt = self.from_date - self.to_date
        return dt.days