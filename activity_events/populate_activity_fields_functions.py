from django.db import connection
from .models import ActivityEventField, ActivityEvent

def populate_activity_fields():
    try:
        required_tables = ['activity_events_activityevent',
                               'activity_events_activityeventfield']

        missing_tables = check_missing_tables(required_tables)
        if missing_tables:
            missing_tables_str = ', '.join(missing_tables)
            error_message = f"Required tables do not exist: {
                 missing_tables_str}."
            raise ValueError(error_message)

        fields_status = remove_stale_fields()
        fields_status.update(update_activity_fields())
        return fields_status
    except Exception as e:        
        raise e

def check_missing_tables(table_names):
    # Check if the specified tables are missing in the database.
    existing_tables = connection.introspection.table_names()
    return [table_name for table_name in table_names if table_name not in existing_tables]

def update_activity_fields():
    model = ActivityEvent
    fields = model._meta.get_fields()  # Use get_fields() to include all field types

    fields_status = {}

    for field in fields:
        field_name = field.name
        field_type = field.get_internal_type()

        # Try to get the FieldPreference for this fieldname
        field_pref, created = ActivityEventField.objects.get_or_create(
            fieldname=field_name,
            fieldtype=field_type       
        )

        if created:
            # If the field was created, mark it as 'created'
            field_pref.displayname=field_name
            field_pref.save()
            fields_status[field_name] = 'created'
        else:
            if field_pref.fieldtype != field_type:
                # If the fieldtype is different, update it and mark as 'updated'
                field_pref.fieldtype = field_type
                field_pref.save()
                fields_status[field_name] = 'updated'
            else:
                # If no change was made, mark as 'no change'
                fields_status[field_name] = 'no change'

    return fields_status

def remove_stale_fields():
     # Get the field names from the ActivityEvent model
    model = ActivityEvent
    current_field_names = set(
        field.name for field in model._meta.get_fields())

    # Fetch all ActivityEventField entries that are stale
    stale_fields = ActivityEventField.objects.exclude(
        fieldname__in=current_field_names)

    removal_status = {}
    for field_entry in stale_fields:
        removal_status[field_entry.fieldname] = 'removed'

    stale_fields.delete()

    return removal_status