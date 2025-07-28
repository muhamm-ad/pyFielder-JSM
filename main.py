"""
Main script for JSM (Jira Service Management) configuration management

This script manages the automated creation and deletion of custom fields
in Jira Service Management.

Usage:
------
python jsm_main.py <action> [options]

Available actions:
----------------
- apply   : Creates or updates the configuration
- destroy : Removes existing configuration

Main options:
------------
--iterations, -n N     : Number of custom fields to create (default: 1)
--state-file, -f FILE   : Path to state file (default: jsm_state.json)
--verbose, -v           : Enable detailed messages

Usage examples:
-------------
1. Create configuration for 5 custom fields:
   python jsm_main.py apply --iterations 5

2. Remove existing configuration:
   python jsm_main.py destroy

Notes:
-----
- State file (default: jsm_state.json) is used to track created elements
"""

import json
import sys
import argparse
import os
from custom_fields import create_custom_fields, delete_custom_fields
from utils import JSM_STATE_FILE, CUSTOM_FIELDS_TO_CREATE


states = {  # State dictionary to track configuration elements
    "custom_fields": [],
}


def load_state():
    if os.path.exists(JSM_STATE_FILE):
        with open(JSM_STATE_FILE, "r") as f:
            return json.load(f)
    else:
        raise FileNotFoundError(f"State file not found: {JSM_STATE_FILE}")


def save_state(state_dict):
    with open(JSM_STATE_FILE, "w") as f:
        json.dump(state_dict, f, indent=2)


def get_existing_custom_fields():
    """
    Retrieves existing custom fields from state file.

    Returns:
        dict: Dictionary of existing custom fields

    Raises:
        Exception: If custom fields cannot be retrieved
    """
    try:
        current_state = load_state()
        if current_state["custom_fields"]:
            return current_state["custom_fields"]
        else:
            print("No existing custom fields found in state file.")
            sys.exit(1)
    except FileNotFoundError:
        raise Exception("Cannot get existing custom fields.")


def destroy_configuration(verbose=False):
    """Removes existing configuration based on saved state."""
    try:
        current_state = load_state()
    except FileNotFoundError as e:
        return

    # Delete custom fields using the saved state
    if len(current_state["custom_fields"]) > 0:
        current_state["custom_fields"] = delete_custom_fields(current_state["custom_fields"], verbose=verbose)
        save_state(current_state)
    print("Custom fields deleted.")

    print("Destroy Done.\n")


def apply_configuration(iterations, verbose=False):
    """Creates or updates the configuration."""
    try:
        current_state = load_state()
        if current_state:
            destroy_configuration(verbose=verbose)
    except FileNotFoundError as e:
        print(f"{e}")
        pass

    # Create or Get Custom Fields
    created_custom_fields = create_custom_fields(CUSTOM_FIELDS_TO_CREATE, iterations, verbose=verbose)
    print("Custom fields created.")
    states["custom_fields"] = created_custom_fields
    save_state(states)

    print("Apply Done.\n")


def main():
    global JSM_STATE_FILE

    parser = argparse.ArgumentParser(
        description="JSM Configuration Tool - Tool to manage JSM configuration and custom fields",
        epilog="Example: python jsm_main.py apply --iterations 5",
    )

    parser.add_argument(
        "action",
        choices=["apply", "destroy"],
        help='Action to perform: "apply" to create custom fields, "destroy" to delete it',
    )

    parser.add_argument(
        "--iterations",
        "-n",
        type=int,
        help="Number of custom fields to create (default: 1)",
        default=1,
        metavar="N",
    )

    parser.add_argument(
        "--state-file",
        "-f",
        type=str,
        help=f"Path to state file (default: {JSM_STATE_FILE})",
        default=None,
        metavar="FILE",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable detailed messages"
    )

    args = parser.parse_args()

    # Update state file path if provided
    if args.state_file is not None:
        JSM_STATE_FILE = args.state_file

    # Validate argument value
    if args.iterations <= 0:
        print("Error: iterations must be a positive number")
        sys.exit(1)

    if args.action == "apply":
        apply_configuration(args.iterations, verbose=args.verbose)
    elif args.action == "destroy":
        destroy_configuration(verbose=args.verbose)
        try:
            if os.path.exists(JSM_STATE_FILE):
                os.remove(JSM_STATE_FILE)
        except Exception as e:
            print(f"Warning: Could not remove state file: {e}")


if __name__ == "__main__":
    main()
