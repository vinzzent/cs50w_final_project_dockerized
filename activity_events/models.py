from django.db import models
from django.db.models import F
from datetime import datetime
from zoneinfo import ZoneInfo
from django.core.exceptions import ValidationError
import uuid

class ActivityEventField(models.Model):
    fieldname = models.CharField(max_length=120, unique=True, blank=False, null=False)    
    fieldtype = models.CharField(max_length=60, blank=False, null=False)
    displayname = models.CharField(max_length=60, default='', blank=True, null=False)
    displayorder = models.IntegerField(default=None, null=True, blank=True)
    display = models.BooleanField(default=False, blank=False, null=False)    
    filter = models.BooleanField(default=False, blank=False, null=False)
    orderby = models.BooleanField(default=False, blank=False, null=False)
    search = models.BooleanField(default=False, blank=False, null=False)
    export = models.BooleanField(default=False, blank=False, null=False)
    chart = models.BooleanField(default=False, blank=False, null=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = [F("displayorder").asc(nulls_last=True), "fieldname"]

class SyncTask(models.Model):
    STATUS_CHOICES = [
        ('pending', 'PENDING'),
        ('success', 'SUCCESS'),
        ('failure', 'FAILURE'),
    ]
    taskuuid = models.CharField(max_length=60, unique=True, blank=False, null=False)
    taskname = models.CharField(max_length=120, blank=False, null=False)
    status = models.CharField(max_length=10, default='PENDING', choices=STATUS_CHOICES, blank=False, null=False)
    result = models.TextField(default='', null=False, blank=False)
    started_at = models.DateTimeField(blank=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.taskuuid:
            # Generate a prefixed UUID
            self.taskuuid = f"synctask-{uuid.uuid4()}"
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-started_at']

class ActivityEvent(models.Model):
    activityid = models.CharField(max_length=60, default='', blank=True, null=False)
    datasetname = models.CharField(max_length=120, default='', blank=True, null=False)
    issuccess=models.CharField(max_length=60,  default='', blank=True, null=False)
    itemname = models.CharField(max_length=120, default='', blank=True, null=False)
    activity = models.CharField(max_length=120, blank=False, null=False)
    workload = models.CharField(max_length=60, default='', blank=True, null=False)
    refreshenforcementpolicy = models.CharField(max_length=60, default='', blank=True, null=False)
    operation = models.CharField(max_length=120, blank=False, null=False)
    recordtype = models.CharField(max_length=60, default='', blank=True, null=False)
    requestid = models.CharField(max_length=60, default='', blank=True, null=False)
    organizationid = models.CharField(max_length=60, blank=False, null=False)
    id = models.CharField(max_length=60, primary_key=True, blank=False, null=False)
    usertype = models.CharField(max_length=60, default='', blank=True, null=False)
    workspaceid = models.CharField(max_length=60, default='', blank=True, null=False)
    datasetid = models.CharField(max_length=60, default='', blank=True, null=False)
    userid = models.CharField(max_length=60, blank=False, null=False)
    creationtime = models.DateTimeField(blank=False, null=False)
    objectid = models.CharField(max_length=255, default='', blank=True, null=False)
    workspacename = models.CharField(max_length=120, default='', blank=True, null=False)
    clientip = models.CharField(max_length=60, default='', blank=True, null=False)
    userkey = models.CharField(max_length=60, blank=False, null=False)
    artifactkind = models.CharField(max_length=60, default='', blank=True, null=False)
    useragent = models.CharField(max_length=255, default='', blank=True, null=False)
    artifactid = models.CharField(max_length=60, default='', blank=True, null=False)
    capacityid = models.CharField(max_length=60, default='', blank=True, null=False)
    capacityname = models.CharField(max_length=120, default='', blank=True, null=False)
    artifactname = models.CharField(max_length=120, default='', blank=True, null=False)
    lastrefreshtime = models.DateTimeField(blank=True, null=True,)
    dataconnectivitymode = models.CharField(max_length=60, default='', blank=True, null=False)
    distributionmethod = models.CharField(max_length=60, default='', blank=True, null=False)
    reporttype = models.CharField(max_length=60, default='', blank=True, null=False)
    reportid = models.CharField(max_length=60, default='', blank=True, null=False)
    reportname = models.CharField(max_length=120, default='', blank=True, null=False)
    refreshtype = models.CharField(max_length=60, default='', blank=True, null=False)
    consumptionmethod = models.CharField(max_length=60, default='', blank=True, null=False)
    itemid = models.CharField(max_length=60, default='', blank=True, null=False)
    modelssnapshots = models.CharField(max_length=255, default='', blank=True, null=False)
    aggregatedworkspaceinformation = models.CharField(max_length=255, default='', blank=True, null=False)
    importdisplayname = models.CharField(max_length=120, default='', blank=True, null=False)
    importtype = models.CharField(max_length=60, default='', blank=True, null=False)
    importid = models.CharField(max_length=60, default='', blank=True, null=False)
    importsource = models.CharField(max_length=60, default='', blank=True, null=False)
    appname = models.CharField(max_length=120, default='', blank=True, null=False)
    appreportid = models.CharField(max_length=60, default='', blank=True, null=False)
    appid = models.CharField(max_length=60, default='', blank=True, null=False)
    exporteventstartdatetimeparameter = models.DateTimeField(blank=True, null=True)
    exporteventenddatetimeparameter = models.DateTimeField(blank=True, null=True)
    extra_data = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    task_id = models.CharField(max_length=60, default='', null=False, blank=True)

    @classmethod
    def get_fields_dict(cls):
        field_info = {}
        for field in cls._meta.get_fields():
            field_info[field.name] = field.get_internal_type()
        return field_info
    
    @classmethod
    def get_filtered_fields_dict(cls, filtered_fields):
        data = cls.get_fields_dict()        
        if isinstance(filtered_fields, list):
            return {key: data[key] for key in filtered_fields if key in data}
        elif isinstance(filtered_fields, dict):        
            return {
                key: [data[key], attribute] for key, attribute in filtered_fields.items() if key in data
            }
        return {}


    @classmethod
    def create_or_update_from_dict(cls, data, task_id=None):
        field_info = cls.get_fields_dict()
        unmapped_data = {}
        mapped_data = {}        
        validation_errors_max_length = {} 
        # Determine if we need to create a new instance or update an existing one
        instance_id = data.get('Id') or data.get('id')
        if instance_id is None:
            raise ValueError("Id of activity event must be provided")  # Raise exception if Id is missing
        try:
            instance = cls.objects.get(id=instance_id)
            created = False
        except cls.DoesNotExist:
            instance = cls()
            created = True 
        # Process each field        
        for field, value in data.items():
            field_lower = field.lower()
            if field_lower in field_info:
                model_field = field_lower
                field_type = field_info[field_lower]                
                # Apply transformation based on field type
                if field_type == 'CharField':
                    max_length = cls._meta.get_field(field_lower).max_length
                    val_length = len(str(value))
                    if val_length > max_length:
                        value = str(value)[:max_length]
                        validation_errors_max_length[model_field] = f'Value in {field_lower} trimmed to {str(max_length)} chars (was {str(val_length)}, exceeded limit).'
                elif field_type == 'DateTimeField':
                    value = datetime.fromisoformat(value).replace(tzinfo=ZoneInfo('UTC'))
                elif field_type == 'BooleanField':
                    value = bool(value)
                mapped_data[model_field] = value
            else:
                unmapped_data[field] = value        
        # Set or update fields on the instance
        for field, value in mapped_data.items():
            setattr(instance, field, value)
        # Store unmapped data in extra_data attribute
        instance.extra_data = unmapped_data
        if task_id:
            instance.task_id = task_id
        try:
            instance.full_clean()  # Validate all fields
            instance.save()  # Save the validated instance to the database
        except ValidationError as e:           
            raise e
        if validation_errors_max_length:
            raise ValidationError(validation_errors_max_length)
        status = 'created' if created else 'updated'       
        return instance, status
    
    class Meta:
        ordering = ['-created_at']
