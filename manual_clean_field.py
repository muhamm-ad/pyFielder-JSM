import requests
import argparse

from secrets import JIRA_DOMAIN, JIRA_USERNAME, JIRA_API_TOKEN

# Constants
JIRA_BASE_URL = "https://" + JIRA_DOMAIN

# JIRA API Headers
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

def parse_arguments():
    """
    Parse command line arguments.
    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description='Delete custom fields from Jira based on a query filter')
    parser.add_argument('--query', type=str, required=True, help='Query filter for custom fields')
    return parser.parse_args()

def get_all_custom_fields(query=""):
    """
    Retrieve all custom fields matching the query from Jira.
    Args:
        query (str): Query string to filter custom fields
    Returns:
        list: List of tuples containing field IDs and names
    """
    all_fields = []
    start_at = 0
    max_results = 50

    while True:
        url = f"{JIRA_BASE_URL}/rest/api/3/field/search?query={query}&startAt={start_at}&maxResults={max_results}"
        response = requests.get(url, auth=(JIRA_USERNAME, JIRA_API_TOKEN), headers=HEADERS)

        if response.status_code == 200:
            data = response.json()
            fields = [(field["id"], field["name"]) for field in data['values'] if field["id"]]
            all_fields.extend(fields)

            # Si nous avons récupéré moins de résultats que max_results, nous avons tout
            if len(data['values']) < max_results:
                break

            start_at += max_results
        else:
            print(f"Error fetching fields: {response.status_code} - {response.text}")
            break

    return all_fields

def delete_custom_field(field_id):
    """
    Delete a specific custom field from Jira.
    Args:
        field_id (str): ID of the custom field to delete
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    url = f"{JIRA_BASE_URL}/rest/api/3/field/{field_id}"
    response = requests.delete(url, auth=(JIRA_USERNAME, JIRA_API_TOKEN), headers=HEADERS)

    if response.status_code == 200:
        return True
    else:
        print(f"Failed to delete {field_id}: {response.status_code} - {response.text}")
        return False

def main():
    """
    Main function to process custom field deletion based on query filter.
    """
    args = parse_arguments()

    # Track fields for reporting
    deleted_fields = []
    remaining_fields = []

    # Get all custom fields matching the query
    custom_fields = get_all_custom_fields(query=args.query)

    if not custom_fields:
        print(f"No custom fields found matching query: {args.query}")
        return

    print(f"Found {len(custom_fields)} fields matching query: {args.query}")

    # Delete all matching custom fields
    for field_id, field_name in custom_fields:
        if delete_custom_field(field_id):
            deleted_fields.append((field_id, field_name))
        else:
            remaining_fields.append((field_id, field_name))

    # Print summary
    print("\nDeletion Summary:")
    print("-" * 50)
    print(f"\nSuccessfully deleted fields ({len(deleted_fields)}):")
    for field_id, field_name in deleted_fields:
        print(f"- {field_name} ({field_id})")

    print(f"\nFailed to delete fields ({len(remaining_fields)}):")
    for field_id, field_name in remaining_fields:
        print(f"- {field_name} ({field_id})")

if __name__ == "__main__":
    main()
