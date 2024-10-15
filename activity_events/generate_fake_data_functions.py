import random
import math
from datetime import timedelta
from django.utils import timezone
from faker import Faker
from .models import ActivityEvent
from .common_functions import save_records_to_model

fake = Faker('en_US')

def generate_and_save_fake_data_list(n_events=6000, n_users=30, start_date=None, end_date=None):

    if end_date is None:
        end_date = timezone.now()

    if start_date is None:
        start_date = end_date - timedelta(days=90)
    
    fields_dict = ActivityEvent.get_fields_dict()

    # Mapping of field names to their corresponding generation functions and the number of values to generate
    generation_map = {
        'id': (generate_uuids, n_events),
        'activity': (generate_words, 25),
        'operation': (generate_words, 15),
        'organizationid': (generate_uuids, 1),
        'userid': (generate_emails, n_users),
        'userkey': (generate_uuids, n_users),
        'useragent': (generate_user_agents, n_users),
        'clientip': (generate_ipv4_addresses, n_users),        
    }
    
    values_dict = {}
    for field, datatype in fields_dict.items():
        if field in generation_map:
            func, count = generation_map[field]
            values_list = func(count)
            values_dict[field] = values_list
        elif field == 'issuccess':
            values_list = ['true', 'false']
            values_dict[field] = values_list               
        elif datatype == 'CharField' and field.endswith('id') and field != 'task_id':     
            values_list = generate_uuids(n_users * 3)
            values_dict[field] = values_list
        elif datatype == 'CharField' and field.endswith('name'):               
            values_list = generate_phrases(n_users)
            values_dict[field] = values_list

    data_list = []
    for i in values_dict.get('id'):        
        event_dict = {}
        for field, datatype in fields_dict.items():
            if field in values_dict:
                if field == 'id':
                    event_dict[field] = i
                elif field in ['activityid', 'activity', 'userid', 'userkey', 'operation', 'organizationid']:                    
                    event_dict[field] = random_from_list(values_dict[field])
                else:
                    event_dict[field] = random_from_list(values_dict[field], 0.2)
            else:
                if datatype == 'DateTimeField':
                    if field == 'creationtime':
                        event_dict[field] = random_iso_datetime_between(start_date, end_date)
                    elif field not in ['created_at', 'updated_at']:
                        iso_datetime = random_iso_datetime_between(start_date, end_date, 0.3)
                        if iso_datetime:
                            event_dict[field] = iso_datetime
                else:
                    event_dict[field] = random_string(0.3)
        event_dict.update(random_dict(0.3))
        data_list.append(event_dict)
    
    save_result = save_records_to_model(data_list, ActivityEvent)
    
    return save_result
    
def generate_emails(count=30, domain="baz.com"):
    emails = []
    for _ in range(count):
        email = f"{fake.first_name().lower()}.{fake.last_name().lower()}@{domain}"
        emails.append(email)
    return emails

def random_iso_datetime_between(start_datetime, end_datetime, null_probability=0, null_value=''):
    if random.random() < null_probability:
        return null_value
    return fake.date_time_between(start_date=start_datetime, end_date=end_datetime).isoformat()

def generate_words(count=50):
    strings = []
    for _ in range(count):
        random_word = fake.word()
        strings.append(random_word)
    return strings

def generate_phrases(count=50, max_words=4):
    phrases = []
    for _ in range(count):
        phrase = fake.sentence(nb_words=max_words, variable_nb_words=False).strip('.')
        phrases.append(phrase)
    return phrases

def generate_ipv4_addresses(count=50):    
    ipv4_addresses = []
    for _ in range(count):
        address = fake.ipv4()
        ipv4_addresses.append(address)    
    return ipv4_addresses    

def generate_user_agents(count=50):
    user_agents = []
    for _ in range(count):
        user_agent = fake.user_agent()
        user_agents.append(user_agent)
    return user_agents

def generate_uuids(count=50):
    uuids = []
    for _ in range(count):
        uuid = fake.uuid4()
        uuids.append(uuid)
    return uuids

def random_from_list(values, null_probability=0, null_value=''):
    if random.random() < null_probability:
        return null_value
    return random.choices(values, weights=[1.5 ** i for i in range(len(values))], k=1)[0]


def random_string(null_probability=0, min_chars=5, max_chars=15):    
    if random.random() < null_probability:
        return ''
    return fake.pystr(min_chars=min_chars, max_chars=max_chars)

def random_dict(null_probability=0, min_num_keys=2, max_num_keys=5):
    if random.random() < null_probability:
        return {}  
    num_keys = random.randint(min_num_keys, max_num_keys)   
    return {f"{fake.word()}{fake.random_int(min=1, max=9)}": fake.pystr(min_chars=5, max_chars=10) for _ in range(num_keys)}