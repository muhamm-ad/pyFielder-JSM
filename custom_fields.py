import copy
import requests
from requests.models import HTTPBasicAuth
from typing import Dict, List

from secrets import JIRA_DOMAIN, JIRA_USERNAME, JIRA_API_TOKEN
BASE_URL = f"https://{JIRA_DOMAIN}/rest/api/3"
AUTH = HTTPBasicAuth(JIRA_USERNAME, JIRA_API_TOKEN)
HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}

create_error_count = 0
delete_error_count = 0


# Function to create a context for a custom field
def create_field_context(field_id, verbose: bool = True):
    global create_error_count
    url = f"{BASE_URL}/field/{field_id}/context"
    data = {
        "name": f"Default Context for {field_id}",
        "description": "Context created via API",
        "projectIds": [],
        "issueTypeIds": [],
    }
    response = requests.post(url, auth=AUTH, headers=HEADERS, json=data)
    if response.status_code == 201:
        context_id = response.json()["id"]
        if verbose: print(f"Context '{context_id}' created for field '{field_id}'.")
        return context_id
    else:
        create_error_count += 1
        if verbose:
            print(f"Failed to create context for field '{field_id}'. Status code: {response.status_code}")
            print(f"Error: {response.text}")
        return None


# Function to get context ID of a custom field
def get_field_context_id(field_id, verbose: bool = True):
    global create_error_count
    response = requests.get(url=f"{BASE_URL}/field/{field_id}/context", auth=AUTH, headers=HEADERS)
    if response.status_code == 200:
        contexts = response.json().get("values", [])
        if contexts:
            return contexts[0]["id"]
    create_error_count += 1
    if verbose: print(f"Failed to get context for field '{field_id}'.")
    return None


# Function to add options to a custom field
def add_options_to_field(field_id, context_id, options, field_type, verbose: bool = True):
    global create_error_count
    if (
        field_type
        == "com.atlassian.jira.plugin.system.customfieldtypes:cascadingselect"
    ):
        parent_option_ids = {}
        # Adding parent options
        for opt in options:
            if "parentValue" not in opt:
                data = {"options": [{"value": opt["value"]}]}
                response = requests.post(
                    url=f"{BASE_URL}/field/{field_id}/context/{context_id}/option",
                    auth=AUTH,
                    headers=HEADERS,
                    json=data,
                )
                if response.status_code == 200:
                    added_option = response.json()["options"][0]
                    parent_option_ids[opt["value"]] = added_option["id"]
                    if verbose: print(f"Parent option '{opt['value']}' added with ID '{added_option['id']}'.")
                else:
                    create_error_count += 1
                    if verbose:
                        print(f"Failed to add parent option '{opt['value']}'. Status code: {response.status_code}")
                        print(f"Error: {response.text}")
        # Adding child options
        for opt in options:
            if "parentValue" in opt:
                parent_id = parent_option_ids.get(opt["parentValue"])
                if not parent_id:
                    if verbose: print(f"Parent option '{opt['parentValue']}' not found for child '{opt['value']}'.")
                    continue
                data = {"options": [{"value": opt["value"], "optionId": parent_id}]}
                response = requests.post(
                    url=f"{BASE_URL}/field/{field_id}/context/{context_id}/option",
                    auth=AUTH,
                    headers=HEADERS,
                    json=data,
                )
                if response.status_code == 200:
                    if verbose: print(f"Child option '{opt['value']}' added under parent ID '{parent_id}'.")
                else:
                    create_error_count += 1
                    if verbose:
                        print(f"Failed to add child option '{opt['value']}'. Status code: {response.status_code}")
                        print(f"Error: {response.text}")
    else:
        response = requests.post(
            url=f"{BASE_URL}/field/{field_id}/context/{context_id}/option",
            auth=AUTH,
            headers=HEADERS,
            json={"options": options},
        )
        if response.status_code == 200:
            if verbose: print(f"Options added to field '{field_id}' successfully.")
        else:
            create_error_count += 1
            if verbose:
                print(f"Failed to add options to field '{field_id}'. Status code: {response.status_code}")
                print(f"Error: {response.text}")


# Function to retrieve options for a custom field
def get_options(field_id, context_id, field_type, verbose: bool = True):
    global create_error_count
    response = requests.get(
        url=f"{BASE_URL}/field/{field_id}/context/{context_id}/option",
        auth=AUTH,
        headers=HEADERS,
    )

    if response.status_code != 200:
        create_error_count += 1
        if verbose:
            print(f"Failed to retrieve options for field '{field_id}'. Status: {response.status_code}")
            print(f"Error: {response.text}")
        return []

    all_options = response.json().get("values", [])

    if (field_type == "com.atlassian.jira.plugin.system.customfieldtypes:cascadingselect"):
        parent_options = [opt for opt in all_options if "optionId" not in opt]
        child_options = [opt for opt in all_options if "optionId" in opt]

        parent_map = {}
        for p in parent_options:
            parent_map[p["id"]] = {"value": p["value"], "id": p["id"], "children": []}

        for c in child_options:
            parent_data = parent_map.get(c.get("optionId"))
            if parent_data:
                parent_data["children"].append({"value": c["value"], "id": c["id"]})

        return list(parent_map.values())
    else:
        return [{"value": opt["value"], "id": opt["id"]} for opt in all_options]


# Function to retrieve the default value of a custom field
def set_default_value(field_id, context_id, default_value, field_type, verbose: bool = True):
    global create_error_count

    if field_type == "com.atlassian.jira.plugin.system.customfieldtypes:textfield":
        data = {
            "defaultValues": [
                {"contextId": context_id, "text": default_value, "type": "textfield"}
            ]
        }
    elif field_type == "com.atlassian.jira.plugin.system.customfieldtypes:float":
        data = {
            "defaultValues": [
                {"contextId": context_id, "number": default_value, "type": "float"}
            ]
        }

    elif field_type == "com.atlassian.jira.plugin.system.customfieldtypes:datetime":
        data = {
            "defaultValues": [
                {
                    "contextId": context_id,
                    "dateTime": default_value,
                    "type": "datetimepicker",
                }
            ]
        }

    elif field_type == "com.atlassian.jira.plugin.system.customfieldtypes:select":
        options = get_options(field_id, context_id, field_type, verbose=verbose)
        default_option = next((opt for opt in options if opt["value"] == default_value), None)
        if default_option:
            data = {
                "defaultValues": [
                    {
                        "contextId": context_id,
                        "optionId": default_option["id"],
                        "type": "option.single",
                    }
                ]
            }
        else:
            if verbose: print(f"Default option '{default_value}' not found for field '{field_id}'.")
            return

    elif field_type == "com.atlassian.jira.plugin.system.customfieldtypes:multiselect":
        options = get_options(field_id, context_id, field_type, verbose=verbose)
        default_values = (default_value if isinstance(default_value, list) else [default_value])
        option_ids = []
        for val in default_values:
            default_option = next((opt for opt in options if opt["value"] == val), None)
            if default_option:
                option_ids.append(default_option["id"])
            else:
                if verbose: print(f"Default option '{val}' not found for field '{field_id}'.")
        if option_ids:
            data = {
                "defaultValues": [
                    {
                        "contextId": context_id,
                        "optionIds": option_ids,
                        "type": "option.multiple",
                    }
                ]
            }
        else:
            create_error_count += 1
            if verbose: print(f"No valid default options found for field '{field_id}'.")
            return

    elif (field_type == "com.atlassian.jira.plugin.system.customfieldtypes:cascadingselect"):
        options = get_options(field_id, context_id, field_type, verbose=verbose)
        parent_option = next((opt for opt in options if opt["value"] == default_value[0]), None)
        if parent_option:
            child_option = None
            if len(default_value) > 1:
                child_option = next(
                    (c for c in parent_option["children"] if c["value"] == default_value[1]),
                    None,
                )
                if not child_option:
                    create_error_count += 1
                    if verbose: print(f"Child option '{default_value[1]}' not found under parent '{default_value[0]}' for field '{field_id}'.")
                    return

            if child_option:
                data = {
                    "defaultValues": [
                        {
                            "contextId": context_id,
                            "optionId": parent_option["id"],
                            "cascadingOptionId": child_option["id"],
                            "type": "option.cascading",
                        }
                    ]
                }
            else:
                # Only parent default
                data = {
                    "defaultValues": [
                        {
                            "contextId": context_id,
                            "optionId": parent_option["id"],
                            "type": "option.cascading",
                        }
                    ]
                }
        else:
            create_error_count += 1
            if verbose: print(f"Parent option '{default_value[0]}' not found for field '{field_id}'.")
            return
    else:
        create_error_count += 1
        if verbose: print(f"Error: Default value setting not implemented for field type '{field_type}'.")
        return

    response = requests.put(
        url=f"{BASE_URL}/field/{field_id}/context/defaultValue",
        auth=AUTH,
        headers=HEADERS,
        json=data,
    )
    if response.status_code == 204:
        if verbose: print(f"Default value set for field '{field_id}'.")
    else:
        create_error_count += 1
        if verbose: 
            print(f"Failed to set default value for field '{field_id}'. Status code: {response.status_code}")
            print(f"Error: {response.json()}")


def get_default_values(field_id):
    response = requests.get(
        url=f"{BASE_URL}/field/{field_id}/context/defaultValue",
        auth=AUTH,
        headers=HEADERS,
    )

    if response.status_code == 200:
        return response.json()["values"]
    else:
        return None


def process_default_answer(question_type, default_values):
    """
    Given a question type (e.g., 'cd', 'cl', 'cc', 'tl', 'no', 'dt') and the Jira default values,
    this function returns a transformed defaultAnswer dictionary suitable for our internal representation.

    Expected default value formats from Jira:

    - For text line (tl), numeric (no), and datetime (dt):
      The default is often provided as a dictionary with a "text", "number", or "dateTime" key respectively.
      Example:
        tl: [{"type": "textfield", "text": "default text"}]
        no: [{"type": "float", "number": "40"}]
        dt: [{"type": "datetimepicker", "dateTime": "2023-05-10T14:00:00Z"}]

      Our internal format should be: {"text": "<default_value>"}

    - For single-choice dropdown (cd):
      The default is usually given as: [{"type": "option.single", "optionId": "12345"}]

      Our internal format should be:{"choices": ["12345"]}
      If no default, {"choices": []}

    - For multiple-choice list (cl):
      The default might be something like: [{"type": "option.multiple", "optionIds": ["12345", "67890"]}]

      Our internal format should be: {"choices": ["12345", "67890"]}
      If no default, {"choices": []}

    - For cascading choice (cc):
      The default may look like: [{"type": "option.cascading", "optionId": "12345", "cascadingOptionId": "67890"}]

      Our internal format should be: {"choices": ["12345:67890"]}
      If no default, {"choices": []}

    If no default values are provided or the field type is not recognized:
      - For tl, no, dt: return {"text": ""}
      - For cd, cl, cc: return {"choices": []}
    """

    if default_values is None or len(default_values) == 0:
        if question_type in ("tl", "no", "dt"):
            return {"text": ""}
        else:
            return {"choices": []}

    dv = default_values[0]  # Generally taking the first default value

    if question_type == "tl":
        return {"text": dv.get("text", "")}

    elif question_type == "no":
        return {"text": str(dv.get("number", ""))}

    elif question_type == "dt":
        return {"text": dv.get("dateTime", "")}

    elif question_type == "ts":
        return {"text": dv.get("text", "")}

    elif question_type == "cd":
        option_id = dv.get("optionId")
        return {"choices": [option_id]} if option_id else {"choices": []}

    elif question_type == "cl":
        option_ids = dv.get("optionIds", [])
        return {"choices": option_ids}

    elif question_type == "cc":
        # Cascading choice default might be {"optionId": "12345", "cascadingOptionId": "67890"}
        parent_id = dv.get("optionId")
        child_id = dv.get("cascadingOptionId")
        if parent_id and child_id:
            return {"choices": [f"{parent_id}:{child_id}"]}
        else:
            return {"choices": []}

    # If a question type not recognized, return empty text answer
    return {"text": ""}


def get_design_question_default_answer(field_id, question_type):
    """
    This function fetches the default values for a given field ID,
    then processes them into a defaultAnswer structure based on the question type.
    """
    default_values = get_default_values(field_id)
    return process_default_answer(question_type, default_values)


def create_custom_fields_options_defaultvalue(field_to_create, field_id, verbose: bool = True):
    if field_id:
        context_id = get_field_context_id(field_id)
        if not context_id:
            context_id = create_field_context(field_id)  # Create a context if none exists

        if context_id :
            if ("options" in field_to_create and field_to_create["options"]):  # Add options if applicable
                add_options_to_field(
                    field_id,
                    context_id,
                    field_to_create["options"],
                    field_to_create["type"],
                    verbose=verbose
                )
            if "defaultValue" in field_to_create:  # Set default value if provided
                set_default_value(
                    field_id,
                    context_id,
                    field_to_create["defaultValue"],
                    field_to_create["type"],
                    verbose=verbose
                )

        return context_id
    return None


def create_field_info_dict(field_to_create, context_id, created_field_id):
    """Creates a dictionary containing field information"""
    options = []
    if context_id and "options" in field_to_create and field_to_create["options"]:
        raw_options = get_options(created_field_id, context_id, field_to_create["type"])
        if (field_to_create["type"] == "com.atlassian.jira.plugin.system.customfieldtypes:cascadingselect"):
            transformed_options = []
            for parent in raw_options:
                transformed_options.append(
                    {
                        "parent_option_value": parent["value"],
                        "parent_option_id": parent["id"],
                        "child_options": parent["children"],
                    }
                )
            options = transformed_options
        else:
            options = raw_options

    return {"id": created_field_id, "context_id": context_id, "options": options}


def create_cf(field_data, verbose: bool = True):
    field_id = None
    context_id = None

    global create_error_count
    data = {
        "name": field_data["name"],
        "description": field_data.get("description", ""),
        "type": field_data["type"],
    }

    if "searcherKey" in field_data:
        data["searcherKey"] = field_data["searcherKey"]

    response = requests.post(url=f"{BASE_URL}/field", auth=AUTH, headers=HEADERS, json=data)

    if response.status_code == 201:
        field_id = response.json()["id"]
        context_id = create_custom_fields_options_defaultvalue(field_data, field_id, verbose=verbose)
        if verbose: print(f"Custom field '{field_data['name']}'({field_id}) created successfully.")
    else:
        create_error_count += 1
        if verbose: 
            print(f"Failed to create custom field '{field_data['name']}'. Status code: {response.status_code}")
            print(f"Error: {response.json()}")

    return (field_id, context_id)


def create_custom_fields(custom_field_to_create: List[Dict], iterations: int, verbose: bool = True):
    result = {}
    
    for num in range(1, iterations + 1):
        for new_field in custom_field_to_create:
            new_field_name = f"{new_field['name']}_{num}"
            new_field_copy = copy.deepcopy(new_field)
            new_field_copy["name"] = new_field_name

            created_field_id, context_id = create_cf(new_field_copy, verbose=verbose)
            field_info = create_field_info_dict(new_field_copy, context_id, created_field_id)
            result[new_field_name] = field_info

    if verbose:
        print("\nDONE CREATING CUSTOM FIELDS!")
        print(f"Total custom fields created: {len(result)}")
        print(f"Total errors encountered: {create_error_count}")

    return result


def delete_custom_fields(custom_fields_to_delete: Dict, verbose: bool = True):
    global delete_error_count
    fields_not_deleted = {}

    for field_name, field_info in custom_fields_to_delete.items():
        field_id = field_info["id"]
        response = requests.delete(url=f"{BASE_URL}/field/{field_id}", auth=AUTH, headers=HEADERS)
        if response.status_code == 200:
            if verbose: print(f"Successfully deleted field {field_name} ({field_id})")
        else:
            if verbose: print(f"Failed to delete field {field_name} ({field_id}): {response.status_code} - {response.text}")
            fields_not_deleted[field_name] = field_info
            delete_error_count += 1

    if verbose:
        print("\nDONE DELETING CUSTOM FIELDS!")
        print(f"Total errors encountered: {delete_error_count}")
        
    return fields_not_deleted
