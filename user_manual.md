# User Manual: Silo Support Ticket Issue CLI

---

## 1 · Introduction

The Silo Support Ticket Issue CLI is a powerful command-line tool designed to transform your Freshdesk support tickets into a structured, evergreen JSON issue database. By leveraging the power of Large Language Models (LLMs), it reads through ticket conversations, identifies the core issue, and intelligently clusters similar tickets together.

This tool is for support managers, product teams, and anyone who wants to gain actionable insights from support conversations. Instead of manually sifting through hundreds of tickets, you can use this tool to:

*   **Quickly identify trending issues.**
*   **Understand the root causes of customer problems.**
*   **Track issues over time with an always up-to-date database.**
*   **Save time on manual analysis and reporting.**

This manual will guide you through setting up and using the tool to its full potential.

## 2 · Getting Started

Follow these steps to get the tool up and running on your local machine.

### 2.1 · Installation

Before you can use the tool, you need to set up a Python environment and install the necessary dependencies.

**Step 1: Create a Virtual Environment**

It's highly recommended to use a virtual environment to avoid conflicts with other Python projects. Open your terminal and run the following commands:

```bash
# Create a virtual environment named .venv
python -m venv .venv

# Activate the virtual environment
# On macOS and Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate
```

**Step 2: Install Dependencies**

Once your virtual environment is active, install the required packages using pip:

```bash
pip install -r requirements.txt
```

### 2.2 · Configuration

The tool uses a `.env` file to manage configuration and API keys. You'll need to create this file in the root of the project directory.

**Step 1: Create the `.env` file**

Create a new file named `.env` in the main project folder.

**Step 2: Add Configuration Variables**

Add the following variables to your `.env` file.

**Required Variables:**

*   `FRESHDESK_DOMAIN`: Your Freshdesk domain name (e.g., `heysilo-help` for `heysilo-help.freshdesk.com`).
*   `FRESHDESK_API_KEY`: Your Freshdesk API key for authentication.

**Optional Variables:**

*   `OPENAI_API_KEY`: Required if you plan to use models from OpenAI.
*   `GROQ_API_KEY`: Required if you plan to use models hosted by Groq.
*   `LLM_MODEL`: Sets a default LLM model to use when you don't specify one. If not set, the tool will use the first model listed in its internal configuration.
*   `BATCH_SIZE`: The number of tickets to process in a single batch. The default is `3`.

Here is an example of what your `.env` file might look like:

```env
FRESHDESK_DOMAIN="your-domain"
FRESHDESK_API_KEY="your-freshdesk-api-key"
OPENAI_API_KEY="your-openai-api-key"
LLM_MODEL="gpt-4"
```

**Important:** Your API keys are secrets and should never be shared or committed to version control. The `.env` file is ignored by Git for this reason.

## 3 · How to Use the Tool

The main functionality of the tool is handled by the `process` command. You can run it in two modes: interactive (a step-by-step wizard) or non-interactive (using command-line flags).

### 3.1 · The `process` Command

This is the workhorse command that initiates the fetching, processing, and clustering of support tickets.

To see all available options, you can run:
```bash
python -m cli process --help
```

### 3.2 · Interactive Mode (The Wizard) ✨

If you run the `process` command without specifying how to select tickets (e.g., without `--pages` or `--ticket-ids`), the tool will launch a helpful interactive wizard. This is the recommended way to use the tool for the first time.

**How to launch:**
```bash
python -m cli process
```

The wizard will guide you through the following steps:

**Step 1: Select Ticket Source**
You'll be asked how you want to select tickets:
*   **Latest resolved tickets (by pages):** Fetches the most recently resolved tickets from Freshdesk. You'll be prompted to enter the number of pages to fetch (each page contains 30 tickets).
*   **Enter ticket IDs manually:** Allows you to provide a specific list of ticket IDs to process. You'll be prompted to enter a comma-separated list of IDs.

**Step 2: Choose Processing Options**
Next, you can choose additional options:
*   **Reprocess existing tickets:** If checked, the tool will re-run the LLM analysis on tickets that are already in your issue database. This is useful if you've updated the prompt or want to use a new model on old data.
*   **Refresh conversations from Freshdesk:** If checked, the tool will re-download the conversation data from Freshdesk for the selected tickets. This is useful if a ticket has been updated since it was last fetched.

**Step 3: Pick an LLM Model**
You will see a list of available LLM models to choose from for processing the tickets. This list is populated from the tool's internal configuration.

**Step 4: Review and Confirm**
Finally, the wizard will display a summary table of the selected options. You can review everything and, if it all looks correct, confirm to start the process.

### 3.3 · Non-Interactive Mode

For automation or scripting, you can run the tool in non-interactive mode by providing command-line flags. When using this mode, you must provide a ticket source (`--pages` or `--ticket-ids`) and the `--non-interactive` flag.

**Example:**
```bash
python -m cli process --pages 3 --model gpt-4-turbo --non-interactive
```

**Available Options:**

| Option                 | Description                                                                                                                              |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `--pages <int>`        | Fetch *n* pages of the latest resolved tickets (30 tickets/page). Mutually exclusive with `--ticket-ids`.                                  |
| `--ticket-ids <CSV>`   | A comma-separated list of specific ticket IDs to process.                                                                                |
| `--model <name>`       | Specify the LLM model to use (e.g., `gpt-4-turbo`). Overrides the `LLM_MODEL` environment variable.                                        |
| `--batch-size <int>`   | Override the default batch size for fetching tickets.                                                                                    |
| `--output <path>`      | Set a custom output path for the JSON database. Defaults to `output/silo_issues_db.json`.                                                |
| `--reprocess`          | Re-run the LLM analysis on tickets that are already in the database.                                                                     |
| `--refresh`            | Re-download ticket conversations from Freshdesk.                                                                                         |
| `--safe-output`        | Prevents overwriting the main database. Instead, writes to a new timestamped file.                                                       |
| `--prompt-debug`       | Prints the prompts sent to the LLM and its responses to the console without writing to the database. Useful for debugging.               |
| `--verbose`            | Enables detailed debug logging, including HTTP requests and token counts.                                                                |
| `--non-interactive`    | Required flag to run the tool without the interactive wizard.                                                                            |


### 3.4 · Viewing Configuration

The tool provides a handy command to check your current configuration.

**`config show`**

This command displays a table with your effective configuration, including Freshdesk settings, the default LLM model, and whether provider API keys have been found in your `.env` file (keys are masked for security).

```bash
python -m cli config show
```

**`config set`**

This command allows you to update the default `LLM_MODEL` or `BATCH_SIZE` in your `.env` file directly from the command line.

```bash
# Set the default model
python -m cli config set --model gpt-4

# Set the default batch size
python -m cli config set --batch-size 5
```

## 4 · Understanding the Output

The primary output of the tool is a JSON file, by default `output/silo_issues_db.json`. This file is your evergreen issue database.

### 4.1 · The Issue Database

The database is a JSON array where each object represents a distinct issue identified and clustered by the LLM. Here's a breakdown of the structure of a single issue object:

```json
{
  "issue_id": "ISSUE-0001",
  "category": "Device & Hardware",
  "short_description": "Device displays 'pressure sensor failure'...",
  "keywords": [
    "pressure sensor failure",
    "wait a sec",
    "sealing container"
  ],
  "root_cause": "Hardware fault in the pressure sensor...",
  "resolution_steps": [
    "1. Ask the user to confirm...",
    "2. Instruct the user to try..."
  ],
  "confidence": 1.0,
  "notes": "Occurs on new devices as well...",
  "tickets": [ 20, 21, 35 ]
}
```

*   `issue_id`: A unique identifier for the clustered issue.
*   `category`: The general category of the issue (e.g., "Device & Hardware", "Setup & Connectivity").
*   `short_description`: A concise, one-sentence summary of the problem.
*   `keywords`: A list of keywords and phrases associated with the issue.
*   `root_cause`: The LLM's analysis of the underlying cause of the issue.
*   `resolution_steps`: A suggested set of steps to resolve the problem.
*   `confidence`: A score from 0.0 to 1.0 indicating the LLM's confidence in its analysis.
*   `notes`: Any additional notes or context about the issue.
*   `tickets`: A list of the ticket IDs that have been clustered under this issue.

### 4.2 · Safe Output Mode

To prevent accidental data loss, the tool includes a `--safe-output` flag.

If you run the tool with this flag and are writing to the default database (`output/silo_issues_db.json`), the tool will first make a backup copy of your existing database with a timestamp (e.g., `silo_issues_db_20251019_123000.json`). It will then write the new, updated data to this backup file, leaving your original database untouched.

This is highly recommended for production workflows to ensure you can always revert to a previous version of your database if needed.

## 5 · Troubleshooting & Tips

*   **Missing API Keys:** If you get an error about missing API keys, double-check that your `.env` file is correctly named, is in the root directory of the project, and contains the correct keys for the LLM provider you are trying to use (`OPENAI_API_KEY` or `GROQ_API_KEY`).
*   **Mutually Exclusive Arguments:** You cannot use `--pages` and `--ticket-ids` at the same time. Choose one method for selecting tickets in non-interactive mode.
*   **When to use `--reprocess` vs. `--refresh`:**
    *   Use `--reprocess` when you want to re-analyze tickets that are already in your database with a new model or a new prompt, without re-downloading the data from Freshdesk.
    *   Use `--refresh` when you suspect the ticket conversation has been updated in Freshdesk and you want to pull the latest version of the data before processing.
*   **Debugging Prompts:** If the LLM output isn't what you expect, use the `--prompt-debug` flag. This will print the exact prompt being sent to the model and the raw response, which is invaluable for debugging and refining your prompts.
