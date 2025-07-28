# JSM Custom Field Automation

This project automates the creation and deletion of custom fields in Jira Service Management (JSM) using the Jira REST API.

## Features

- Create multiple custom fields with options and default values
- Delete custom fields and clean up state
- Track created fields in a state file
- Command-line interface for easy usage

## Requirements

- Python 3.7+
- `requests` library
- Jira Cloud account with admin permissions
- A `secrets.py` file in the project root with the following variables:
  
  ```python
  JIRA_DOMAIN = "your-domain.atlassian.net"
  JIRA_USERNAME = "your-email@example.com"
  JIRA_API_TOKEN = "your-api-token"
  ```

  You can generate an API token from your Atlassian account.

## Setup

1. Clone the repository.
2. Install dependencies:

   ```bash
   pip install requests
   ```

3. Create a `secrets.py` file as described above.

## Usage

Run the main script with the desired action:

```bash
python main.py apply --iterations 5
```

- `apply`: Creates or updates the custom fields as defined in `utils.py`.
- `destroy`: Deletes the custom fields tracked in the state file and removes the state file.

### Options

- `--iterations, -n N` : Number of custom fields to create (default: 1)
- `--state-file, -f FILE` : Path to state file (default: jsm_state.json)
- `--verbose, -v` : Enable detailed messages for field creation and deletion

### Examples

- Create configuration for 5 custom fields:

  ```bash
  python main.py apply --iterations 5
  ```

- Remove existing configuration:

  ```bash
  python main.py destroy
  ```

## Customization

Edit `utils.py` to define the custom fields you want to create. Each field can have a name, description, type, options, and default value.

## Troubleshooting

- Ensure your Jira credentials in `secrets.py` are correct.
- The script requires admin permissions in Jira.
- If you encounter API errors, check your network and Jira API limits.
- The state file (`jsm_state.json` by default) tracks created fields. If you manually delete fields in Jira, you may need to delete or reset this file.

## License

See [LICENSE](LICENSE).
