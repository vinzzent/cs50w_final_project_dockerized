from django import template
from urllib.parse import urlencode
from django.utils.dateparse import parse_datetime

register = template.Library()


@register.filter
def get_attr(obj, name):
    """
    Returns the value of the specified attribute from the given object.

    :param obj: The object from which to retrieve the attribute.
    :param name: The name of the attribute to access.
    :return: The value of the attribute if it exists, otherwise None.
    """
    return getattr(obj, name, None)

##############################

@register.filter
def get_value(dic, key):
    """
    Retrieves the value associated with a given key from a dictionary.

    :param dic: The dictionary from which to retrieve the value.
    :param key: The key whose corresponding value is to be fetched.
    :return: The value associated with the key, or None if the key is not present in the dictionary.
    """    
    return dic.get(key, None)

##############################

@register.filter
def index(indexable, i):
    """
    Returns the element at the specified index from the indexable object.

    :param indexable: The object (like a list or tuple) to retrieve the element from.
    :param i: The index of the element to fetch.
    :return: The element at the specified index.
    """  
    return indexable[i]

##############################

@register.filter
def has_non_empty_query_params(dic):
    """
    Checks if a dictionary has non-empty query parameters.

    This function evaluates whether a dictionary contains non-empty values
    for keys other than 'page' and those starting with 'orderby'. It also
    counts the 'orderby_' keys with non-empty values. The function returns
    True if there is at least one non-empty value or if there are two or
    more non-empty 'orderby_' keys.

    :param dic: The dictionary to check.
    :return: True if the dictionary has non-empty query parameters or
            at least two non-empty 'orderby_' keys; False otherwise.
    """
    if not isinstance(dic, dict):
        return False

    has_non_empty = False
    orderby_count = 0

    for key, value in dic.items():
        # Check for keys starting with 'orderby'
        if key.startswith('orderby_'):
            if value not in (None, ''):  # Skip empty values
                orderby_count += 1
        elif key != 'page':
            # Exclude 'page' key and 'orderby' keys, check if value is non-empty
            if isinstance(value, (str, list, dict)) and not value:
                continue  # Skip empty values of type string, list, or dict
            if value:
                has_non_empty = True

    # Return True if either condition is met
    return has_non_empty or orderby_count >= 2

##############################

@register.filter
def endswith(value, arg):
    """
    Checks if a given string ends with a specified suffix.

    :param value: The string to check.
    :param arg: The suffix to look for at the end of the string.
    :return: True if the string ends with the specified suffix, False otherwise.
    """
    return value.endswith(arg)

##############################

@register.filter
def build_query_string_for_admin_activity_events(request_get):
    """
    Generates a query string from request.GET items, excluding 'page'.
    Converts values of keys ending with '__gte' or '__lt' to ISO 8601 date strings.

    :param request_get: The GET parameters dictionary from Django HttpRequest.
    :return: The constructed query string, prefixed with '?', or an empty string if no parameters are present.
    """
    params = {}
    for key, value in request_get.items():
        if key != 'page':
            # Check if the key ends with '__gte' or '__lt'
            if key.endswith('__gte') or key.endswith('__lt'):
                try:
                    # Parse the value to a datetime object
                    date_value = parse_datetime(value)
                    if date_value:
                        # Convert to ISO 8601 format
                        value = date_value.isoformat()
                except ValueError:
                    # If parsing fails, keep the original value
                    pass
            params[key] = value

    query_string = urlencode(params, doseq=True)
    return f"?{query_string}" if query_string else ""

##############################

@register.filter
def build_query_string(request_get):
    """
    Generates a query string with the current GET parameters,
    excluding the 'page' parameter.

    :param request_get: The GET parameters dictionary from Django HttpRequest.
    :return: A query string, prefixed with '?', or an empty string if no parameters are present.
    """
    params = request_get.copy()
    params.pop('page', None)
    return urlencode(params, doseq=True)

##############################

@register.filter
def generate_filters_description(request_dict, filters_dict):
    """
    Generates a description of filters from the request dictionary.

    :param request_dict: The dictionary of request parameters to describe.
    :param filters_dict: A dictionary mapping filter keys to their display names.
    :return: A string describing the applied filters, or an empty string if no filters are present.
    """
    if not isinstance(request_dict, dict) or not isinstance(filters_dict, dict):
        return ''  # Return an empty string for invalid input

    filters_desc = []

    for key, value in request_dict.items():
        if not value:
            continue  # Skip empty values

        # Initialize comparison operator and cleaned key
        comparison_operator = '='
        cleaned_key = key

        # Determine comparison operator and clean key
        if '__gte' in key:
            cleaned_key = key.replace('__gte', '')
            comparison_operator = '>='
        elif '__lte' in key:
            cleaned_key = key.replace('__lte', '')
            comparison_operator = '<='

        # Only add description if cleaned_key exists in filters_dict
        if cleaned_key in filters_dict:
            displayname = filters_dict[cleaned_key].get('displayname', '')
            displayname = displayname if displayname else cleaned_key
            filters_desc.append(f'{displayname} {comparison_operator} {value}')

    # Join filters with ' & ' and return
    return ' & '.join(filters_desc)

##############################

@register.filter
def generate_orderby_description(request_dict, orderby_dict):
    """
    Generates a description of the sorting order from the request dictionary.

    :param request_dict: The dictionary of request parameters to describe.
    :param orderby_dict: A dictionary mapping filter keys to their display names.
    :return: A string describing the applied sorting order, or an empty string if no sorting is present.
    """
    if not isinstance(request_dict, dict) or not isinstance(orderby_dict, dict):
        return ''  # Return an empty string for invalid input

    # Extract field and direction names
    field_name = orderby_dict.get('fields', {}).get('name')
    direction_name = orderby_dict.get('directions', {}).get('name')

    # Return empty string if field or direction names are missing
    if not field_name or not direction_name:
        return ''

    # Get the actual values from the request
    field = request_dict.get(field_name)
    direction = request_dict.get(direction_name)

    if field and direction:
        # Get field values and direction values from orderby_dict
        fields = orderby_dict.get('fields', {}).get('values', {})
        directions = orderby_dict.get('directions', {}).get('values', {})

        # Determine the display name, defaulting to field if empty
        displayname = next(
            (i.get('displayname', '') for i in fields.values() if field == i.get('fieldname')),
            field
        )
        # Ensure displayname is the fallback if it was empty
        displayname = displayname if displayname != '' else field

        # Get the description for direction, or use the direction as is if not found
        direction_description = directions.get(direction, direction)

        return f"{displayname} ({direction_description})"

    return ''

##############################

@register.filter
def get_first_datetime_field_value(field_values, field_types):
    """
    Returns the value from `field_values` corresponding to the first occurrence of 'DateTimeField' in `field_types`.

    :param field_values: List of field values (list).
    :param field_types: List of field types (list), where one entry is 'DateTimeField'.
    :return: Value from `field_values` at the first occurrence of 'DateTimeField', or None if not found.
    """
    if not isinstance(field_values, list) or not isinstance(field_types, list):
        return None

    try:
        index = field_types.index('DateTimeField')
        return field_values[index] if index < len(field_values) else None
    except ValueError:
        return None

@register.filter
def find_first_occurrence(lst, target):
    """
    Returns the index of the first occurrence of `target` in `lst`.

    :param lst: List of elements (list).
    :param target: String to find (str).
    :return: Index of the first occurrence of `target` in `lst` (int), or -1 if not found.
    """
    try:
        return lst.index(target)
    except ValueError:
        return -1