# LinkedIn Employee Email Extractor

This script extracts employee names and positions from a LinkedIn company page and generates their likely email addresses using the email pattern from Hunter.io.

## Features

- Scrapes all available employees from a LinkedIn company page (requires a valid `li_at` session cookie). If a non-business account is used it might hit the 1000 request limit.
- Uses Hunter.io to determine the company’s email address pattern.
- Outputs results to the console and/or a CSV file.

## Requirements

- Install requirements using `pip install -r requirements.txt`

## Setup

### 1. Hunter.io API Key

Fill in `hunter.conf` with your Hunter API key:

hunter_api = "\<YOUR_HUNTER_API_KEY\>"

### 2. LinkedIn Session Cookie

You need a valid `li_at` cookie from a logged-in LinkedIn session.  
You can find this in your browser’s developer tools under Application > Cookies.

## Usage

python lidump.py --url https://www.linkedin.com/company/<company-slug\> --cookie \<li_at_cookie\> --domain \<company-domain\> [--output-csv output.csv]

- `--url` : LinkedIn company page URL (e.g., https://www.linkedin.com/company/example)
- `--cookie` : Your LinkedIn `li_at` session cookie
- `--domain` : The company’s email domain (e.g., example.com)
- `--output-csv` : (Optional) Output results to a CSV file

### Example

python lidump.py --url https://www.linkedin.com/company/example --cookie AQED... --domain example.com --output-csv employees.csv

## Output

- **Console output:**

  Firstname;Lastname;Email;Position  
  John;Doe;john.doe@example.com;HR Manager  
  ...

- **CSV output** (if `--output-csv` is provided):  
  Columns: Firstname, Lastname, Email, Position

## Notes

- This script is for educational and authorized use only.
- LinkedIn may block or rate-limit requests. Use responsibly and in accordance with LinkedIn’s terms of service.
- The accuracy of email generation depends on the pattern provided by Hunter.io.