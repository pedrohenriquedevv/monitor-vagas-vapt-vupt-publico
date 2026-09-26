# Vapt Vupt Appointment Monitor

A configurable appointment availability monitor developed with Python and Playwright.

The project automates the initial navigation flow of the Goiás Vapt Vupt appointment portal, checks availability for a configured municipality, analyzes available dates and times, and selects the appointment time closest to the user's preference.

> This is an independent educational project. It is not affiliated with, endorsed by, or maintained by the Government of Goiás or Vapt Vupt.

## Project motivation

This project started from a real need: repeatedly checking the appointment portal for newly available time slots.

Instead of manually completing the same steps multiple times, the workflow was automated with Python and Playwright.

The project explores:

- Browser automation
- Dynamic page interaction
- Availability detection
- Calendar navigation
- Date filtering
- Appointment time prioritization
- Environment variable management
- Logging and error handling
- Protection against unexpected portal responses

## Features

- Opens the Vapt Vupt appointment portal
- Selects the identity card service
- Completes the initial form using local environment variables
- Selects a configurable municipality and service unit
- Detects unavailable appointment messages
- Navigates through the appointment calendar
- Ignores configured weekdays
- Searches the current month and upcoming months
- Reads all available appointment times
- Selects the time closest to the user's preferred time
- Uses the later time as a tie-breaker
- Detects CAPTCHA, access denial, HTTP 429 messages, and similar protections
- Saves execution logs locally
- Saves a local screenshot when an appointment candidate is found
- Stops before entering final contact information or confirming an appointment

## Safety design

The public version was intentionally designed as a monitor rather than a fully autonomous booking bot.

It does not:

- Confirm appointments
- Click the final confirmation button
- Download appointment receipts
- Store personal information in the source code
- Bypass CAPTCHA or access restrictions
- Retry continuously
- Create multiple concurrent browser sessions
- Attempt to circumvent portal protections

The script performs one availability check per execution.

If the portal displays a CAPTCHA, blocking message, access denial, or another unexpected response, the execution stops and records the event in the local log.

## Project structure

```text
monitor-vagas-vapt-vupt-publico/
├── .env.example
├── .gitignore
├── monitor.py
├── requirements.txt
├── setup.bat
└── README.md
```

## Requirements

- Windows 10 or Windows 11
- Python 3.10 or newer
- Internet connection
- Access to the Vapt Vupt appointment portal

## Installation on Windows

### Automatic installation

Download or clone the repository and run:

```text
setup.bat
```

The setup script will:

1. Create a Python virtual environment in `.venv`
2. Activate the virtual environment
3. Update `pip`
4. Install the Python dependencies
5. Install Chromium for Playwright
6. Create a local `.env` file from `.env.example`

After installation, open the generated `.env` file and configure the required values.

### Manual installation

Create a virtual environment:

```powershell
py -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\activate
```

Install the Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

Install Chromium for Playwright:

```powershell
python -m playwright install chromium
```

Create the local configuration file:

```powershell
copy .env.example .env
```

## Configuration

Open the local `.env` file and fill in the required values:

```env
VAPT_NOME=
VAPT_CPF=
VAPT_DATA_NASCIMENTO=
VAPT_NOME_MAE=
VAPT_NOME_PAI=
VAPT_TELEFONE=
VAPT_EMAIL=

VAPT_MUNICIPIO=
VAPT_UNIDADE=
VAPT_HORARIO_PREFERIDO=
```

Example using fictional data:

```env
VAPT_NOME=JOAO DA SILVA
VAPT_CPF=000.000.000-00
VAPT_DATA_NASCIMENTO=01/01/2000
VAPT_NOME_MAE=MARIA DA SILVA
VAPT_NOME_PAI=JOSE DA SILVA
VAPT_TELEFONE=00 000000000
VAPT_EMAIL=usuario@example.com

VAPT_MUNICIPIO=CATALAO
VAPT_UNIDADE=Catalão
VAPT_HORARIO_PREFERIDO=16:00
```

Do not add real personal data to `.env.example`.

The `.env` file is ignored by Git and must remain only on the user's computer.

## Preferred time selection

The preferred appointment time is configured with:

```env
VAPT_HORARIO_PREFERIDO=16:00
```

The monitor reads every available time and selects the option with the smallest distance from the preferred time.

Example:

```text
Preferred time: 16:00
Available times: 08:00, 14:30, 15:30, 16:00, 16:30
Selected time: 16:00
```

When two options are equally distant, the later time receives priority.

Example:

```text
Preferred time: 16:00
Available times: 15:30, 16:30
Selected time: 16:30
```

The preferred time must use the `HH:MM` format.

Valid examples:

```text
08:30
14:00
16:00
```

## Blocked weekdays

The public version currently ignores Wednesday and Friday:

```python
BLOCKED_WEEKDAYS = {
    2,  # Wednesday
    4,  # Friday
}
```

Python uses the following weekday values:

```text
Monday    = 0
Tuesday   = 1
Wednesday = 2
Thursday  = 3
Friday    = 4
Saturday  = 5
Sunday    = 6
```

To change the restriction, edit `BLOCKED_WEEKDAYS` in `monitor.py`.

Example that blocks only Sunday:

```python
BLOCKED_WEEKDAYS = {
    6,
}
```

Example without blocked weekdays:

```python
BLOCKED_WEEKDAYS = set()
```

## Running the monitor

Run the project with:

```powershell
.venv\Scripts\python.exe monitor.py
```

The browser will open and perform one availability check.

Possible outcomes include:

### No appointments available

```text
No appointments are currently available.
Execution completed without available appointments.
```

### Appointment candidate found

```text
All available times: 08:00, 14:30, 15:30, 16:00
Calculated priority: 16:00, 15:30, 14:30, 08:00
Preferred time: 16:00. Selected time: 16:00.
An appointment candidate was found.
```

The public version stops before entering final contact information or confirming the appointment.

## Local output files

The monitor may create:

```text
monitor.log
appointment_candidate.png
```

These files are ignored by Git and should not be committed.

The log records:

- Execution date and time
- Portal navigation status
- Availability messages
- Dates ignored by user preference
- Available appointment times
- Calculated priority order
- Selected date and time
- Timeout and execution errors
- Possible access restrictions

The screenshot may contain information displayed by the portal. Review it before sharing it with anyone.

## Privacy

The appointment flow may process sensitive personal information, including:

- Full name
- CPF
- Date of birth
- Parents' names
- Telephone number
- Email address

Keep this information only in the local `.env` file.

Never commit or publish:

- `.env`
- Execution logs containing personal information
- Screenshots containing personal information
- Appointment receipts
- Appointment protocols
- QR codes
- Personal documents

If personal information is accidentally committed, deleting it from the current file may not remove it from the Git history.

## Responsible use

Use this project responsibly and only with information that belongs to the user or that the user is authorized to process.

Do not use the project to:

- Overload public services
- Perform continuous or aggressive requests
- Circumvent access controls
- Bypass CAPTCHA
- Reserve appointments for third parties without authorization
- Create duplicate or unnecessary appointments
- Prevent other citizens from accessing available services

Review the portal's current terms, rules, and privacy information before use.

Portal behavior and selectors may change without notice. If the interface changes, the monitor may stop working until its selectors are updated.

## Known limitations

- The project depends on the current structure of the portal
- Interface changes may invalidate Playwright selectors
- The monitor currently targets the identity card service flow
- Municipality and unit names must match the values displayed by the portal
- The public version does not confirm appointments
- The public version does not run continuously
- The public version does not include Windows Task Scheduler configuration
- CAPTCHA and blocking messages stop the execution
- Calendar availability must still be provided by the portal
- The project cannot guarantee appointment availability

## Troubleshooting

### Missing environment variables

If the terminal displays:

```text
Missing environment variables
```

Open `.env` and complete every required value.

### Invalid preferred time

If the terminal displays:

```text
VAPT_HORARIO_PREFERIDO must use the HH:MM format
```

Use a value such as:

```env
VAPT_HORARIO_PREFERIDO=16:00
```

### Playwright browser not installed

Run:

```powershell
python -m playwright install chromium
```

### Portal timeout

A timeout may occur because of:

- Slow internet connection
- Portal instability
- Interface changes
- Temporary service unavailability

Review `monitor.log` for the recorded error.

### Selector not found

If Playwright reports that a button, field, or option was not found, the portal interface may have changed.

The affected locator must be reviewed in `monitor.py`.

## Technology

- Python
- Playwright
- python-dotenv
- Chromium
- Regular expressions
- Environment variables
- Local logging

## Development background

This project was created from a practical workflow and evolved through real navigation tests, availability checks, calendar inspection, time-slot analysis, logging, and error diagnosis.

The primary engineering lesson was the importance of separating:

- Interactive testing
- Automated execution
- Personal configuration
- Public source code
- Confirmation actions
- Diagnostic behavior

## Disclaimer

This software is provided for educational and experimental purposes.

The author does not guarantee continuous compatibility with the portal, appointment availability, successful execution, or suitability for a specific purpose.

Users are responsible for protecting personal data, following applicable rules, reviewing selected information, and using the project without disrupting the service.

## Author

Developed by Pedro Henrique Lopes de Araújo.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
