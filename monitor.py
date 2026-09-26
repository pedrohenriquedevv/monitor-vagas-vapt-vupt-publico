import os
import re
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import (
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# CONFIGURATION
# ============================================================

URL = (
    "https://www.go.gov.br/servicos-digitais/vapt-vupt/"
    "agendamento-atendimento-presencial/sem-login"
)

NAME = os.getenv("VAPT_NOME", "").strip()
CPF = os.getenv("VAPT_CPF", "").strip()
BIRTH_DATE = os.getenv(
    "VAPT_DATA_NASCIMENTO",
    "",
).strip()
MOTHER_NAME = os.getenv(
    "VAPT_NOME_MAE",
    "",
).strip()
FATHER_NAME = os.getenv(
    "VAPT_NOME_PAI",
    "",
).strip()
PHONE = os.getenv("VAPT_TELEFONE", "").strip()
EMAIL = os.getenv("VAPT_EMAIL", "").strip()

MUNICIPALITY = os.getenv(
    "VAPT_MUNICIPIO",
    "CATALAO",
).strip()

EXPECTED_UNIT = os.getenv(
    "VAPT_UNIDADE",
    "Catalão",
).strip()

PREFERRED_TIME = os.getenv(
    "VAPT_HORARIO_PREFERIDO",
    "16:00",
).strip()

# The public version always stops before confirmation.
HEADLESS = False

# Monday = 0
# Tuesday = 1
# Wednesday = 2
# Thursday = 3
# Friday = 4
# Saturday = 5
# Sunday = 6
BLOCKED_WEEKDAYS = {
    2,  # Wednesday
    4,  # Friday
}

MAX_MONTHS_TO_SEARCH = 3

DEFAULT_TIMEOUT_MS = 20_000
NAVIGATION_TIMEOUT_MS = 60_000

PROJECT_DIRECTORY = Path(__file__).resolve().parent

LOG_FILE = PROJECT_DIRECTORY / "monitor.log"
SCREENSHOT_FILE = (
    PROJECT_DIRECTORY / "appointment_candidate.png"
)


# ============================================================
# LOGGING
# ============================================================

def log(message):
    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    line = f"[{timestamp}] {message}"

    print(line, flush=True)

    with LOG_FILE.open(
        "a",
        encoding="utf-8",
    ) as file:
        file.write(line + "\n")


def save_screenshot(page):
    try:
        if page.is_closed():
            return

        page.screenshot(
            path=str(SCREENSHOT_FILE),
            full_page=True,
        )

        log(
            "Screenshot saved locally as "
            f"{SCREENSHOT_FILE.name}."
        )

    except Exception as error:
        log(
            "Could not save screenshot: "
            f"{type(error).__name__}: {error}"
        )


# ============================================================
# TEXT HELPERS
# ============================================================

def get_full_page_text(page):
    """
    The portal may contain more than one body element.

    all_inner_texts() avoids Playwright strict-mode errors
    caused by multiple matching body elements.
    """

    texts = page.locator("body").all_inner_texts()

    return "\n".join(texts)


def normalize_text(text):
    return " ".join(
        text.lower().split()
    )


# ============================================================
# TIME HELPERS
# ============================================================

def time_to_minutes(text):
    match = re.fullmatch(
        r"\s*(\d{1,2}):(\d{2})\s*",
        text,
    )

    if match is None:
        return None

    hour = int(match.group(1))
    minute = int(match.group(2))

    if hour > 23 or minute > 59:
        return None

    return hour * 60 + minute


def validate_preferred_time():
    preferred_time_minutes = time_to_minutes(
        PREFERRED_TIME
    )

    if preferred_time_minutes is None:
        raise RuntimeError(
            "VAPT_HORARIO_PREFERIDO must use the "
            "HH:MM format, for example 16:00."
        )

    return preferred_time_minutes


PREFERRED_TIME_MINUTES = validate_preferred_time()


def time_priority(text):
    """
    Selects the available time closest to the preferred time.

    If two available times have the same distance from the
    preferred time, the later time receives priority.

    Example with preferred time 16:00:
    15:30 and 16:30 have the same distance.
    The selected time will be 16:30.
    """

    minutes = time_to_minutes(text)

    if minutes is None:
        return float("inf"), 0

    distance = abs(
        minutes - PREFERRED_TIME_MINUTES
    )

    return distance, -minutes


def choose_best_time(available_times):
    valid_times = []

    for available_time in available_times:
        clean_time = available_time.strip()

        if time_to_minutes(clean_time) is not None:
            valid_times.append(clean_time)

    valid_times = list(
        dict.fromkeys(valid_times)
    )

    if not valid_times:
        return None

    log(
        "All available times: "
        + ", ".join(valid_times)
    )

    ordered_times = sorted(
        valid_times,
        key=time_priority,
    )

    log(
        "Calculated priority: "
        + ", ".join(ordered_times)
    )

    selected_time = ordered_times[0]

    log(
        f"Preferred time: {PREFERRED_TIME}. "
        f"Selected time: {selected_time}."
    )

    return selected_time


# ============================================================
# DATE HELPERS
# ============================================================

def parse_date(text):
    months = {
        "janeiro": 1,
        "fevereiro": 2,
        "março": 3,
        "abril": 4,
        "maio": 5,
        "junho": 6,
        "julho": 7,
        "agosto": 8,
        "setembro": 9,
        "outubro": 10,
        "novembro": 11,
        "dezembro": 12,
    }

    match = re.search(
        r"(\d{1,2}) de ([a-zç]+)(?: de (\d{4}))?",
        text.lower().strip(),
    )

    if match is None:
        return None

    day = int(match.group(1))
    month_name = match.group(2)
    year_text = match.group(3)

    month = months.get(month_name)

    if month is None:
        return None

    current_year = datetime.now().year

    year = (
        int(year_text)
        if year_text
        else current_year
    )

    try:
        date = datetime(
            year=year,
            month=month,
            day=day,
        )

        if (
            year_text is None
            and datetime.now().month == 12
            and month == 1
        ):
            date = date.replace(
                year=current_year + 1
            )

        return date

    except ValueError:
        return None


# ============================================================
# ENVIRONMENT VALIDATION
# ============================================================

def validate_environment():
    required_values = {
        "VAPT_NOME": NAME,
        "VAPT_CPF": CPF,
        "VAPT_DATA_NASCIMENTO": BIRTH_DATE,
        "VAPT_NOME_MAE": MOTHER_NAME,
        "VAPT_NOME_PAI": FATHER_NAME,
        "VAPT_TELEFONE": PHONE,
        "VAPT_EMAIL": EMAIL,
    }

    missing_variables = [
        variable
        for variable, value in required_values.items()
        if not value
    ]

    if missing_variables:
        raise RuntimeError(
            "Missing environment variables: "
            + ", ".join(missing_variables)
        )


# ============================================================
# SAFETY CHECKS
# ============================================================

def check_for_blocking(page):
    page_text = get_full_page_text(
        page
    ).lower()

    indicators = [
        "captcha",
        "acesso negado",
        "access denied",
        "too many requests",
        "muitas requisições",
        "atividade suspeita",
        "comportamento suspeito",
        "temporariamente bloqueado",
        "erro 429",
    ]

    for indicator in indicators:
        if indicator in page_text:
            raise RuntimeError(
                "Blocking or protection detected: "
                f"{indicator}"
            )


def get_visible_dialog(page):
    dialogs = page.get_by_role("dialog")

    for index in range(dialogs.count()):
        dialog = dialogs.nth(index)

        try:
            if dialog.is_visible():
                return dialog

        except Exception:
            continue

    return None


# ============================================================
# INITIAL SERVICE FLOW
# ============================================================

def open_service_flow(page):
    log("Opening the Vapt Vupt portal.")

    page.goto(
        URL,
        wait_until="domcontentloaded",
        timeout=NAVIGATION_TIMEOUT_MS,
    )

    check_for_blocking(page)

    page.get_by_role(
        "button",
        name="Novo Agendamento",
    ).click()

    page.locator("ng-select").filter(
        has_text="Selecione o órgão",
    ).click()

    page.get_by_text(
        "SSP - Secretaria de Estado da",
        exact=False,
    ).click()

    page.get_by_role(
        "textbox",
        name="Serviços",
    ).click()

    page.get_by_text(
        "SSP - CARTEIRA DE IDENTIDADE",
        exact=False,
    ).click()

    page.get_by_role(
        "button",
        name="Aceitar",
    ).click()

    page.get_by_role(
        "textbox",
        name="Nome",
        exact=True,
    ).fill(NAME)

    page.get_by_role(
        "textbox",
        name="CPF",
    ).fill(CPF)

    page.get_by_role(
        "textbox",
        name="Data de nascimento",
    ).fill(BIRTH_DATE)

    page.get_by_role(
        "textbox",
        name="Nome da mãe",
    ).fill(MOTHER_NAME)

    page.get_by_role(
        "textbox",
        name="Nome do pai",
    ).fill(FATHER_NAME)

    page.get_by_role(
        "button",
        name="Continuar",
    ).click()

    page.get_by_role(
        "button",
        name="Agendar presencial",
    ).click()

    log(
        "Identity card service selected and "
        "initial information completed."
    )


# ============================================================
# MUNICIPALITY
# ============================================================

def select_municipality(page):
    page.get_by_text(
        "Selecione o município que deseja atendimento",
        exact=False,
    ).click()

    municipality_option = page.get_by_title(
        MUNICIPALITY
    )

    if municipality_option.count() == 0:
        municipality_option = page.get_by_role(
            "option",
            name=MUNICIPALITY,
        )

    if municipality_option.count() == 0:
        raise RuntimeError(
            f"Municipality not found: {MUNICIPALITY}"
        )

    municipality_option.first.click()

    log(
        f"Municipality selected: {MUNICIPALITY}."
    )

    page.wait_for_timeout(2500)

    check_for_blocking(page)

    dialog = get_visible_dialog(page)

    if dialog is None:
        log(
            "The unavailable-slots message did not appear. "
            "Availability may exist."
        )

        return True

    message = dialog.inner_text().strip()
    normalized_message = normalize_text(message)

    log(
        "Portal message: "
        + message.replace("\n", " | ")
    )

    if "esgotados" in normalized_message:
        log(
            "No appointments are currently available."
        )

        return False

    raise RuntimeError(
        f"Unexpected portal message: {message}"
    )


# ============================================================
# CALENDAR
# ============================================================

def open_date_schedule(page):
    option = page.get_by_text(
        "Agendamento por data",
        exact=False,
    )

    option.wait_for(
        state="visible",
        timeout=15_000,
    )

    option.click()

    log("Date scheduling mode selected.")


def get_valid_dates(page):
    page.wait_for_timeout(1200)

    cells = page.get_by_role("gridcell")
    valid_dates = []

    for index in range(cells.count()):
        cell = cells.nth(index)

        try:
            accessible_name = cell.get_attribute(
                "aria-label"
            )

            if not accessible_name:
                accessible_name = (
                    cell.inner_text().strip()
                )

            date = parse_date(accessible_name)

            if date is None:
                continue

            if date.date() < datetime.now().date():
                continue

            if date.weekday() in BLOCKED_WEEKDAYS:
                log(
                    "Date ignored by user preference: "
                    + date.strftime("%Y-%m-%d")
                )

                continue

            aria_disabled = cell.get_attribute(
                "aria-disabled"
            )

            classes = (
                cell.get_attribute("class") or ""
            ).lower()

            disabled = (
                aria_disabled == "true"
                or "disabled" in classes
            )

            if disabled:
                continue

            valid_dates.append(
                {
                    "date": date,
                    "element": cell,
                    "accessible_name": accessible_name,
                }
            )

        except Exception:
            continue

    valid_dates.sort(
        key=lambda item: item["date"]
    )

    return valid_dates


def move_to_next_month(page):
    button = page.get_by_role(
        "button",
        name="Next month",
    )

    if button.count() == 0:
        return False

    button = button.first

    if not button.is_visible():
        return False

    if not button.is_enabled():
        return False

    button.click()
    page.wait_for_timeout(1200)

    log("Calendar moved to the next month.")

    return True


def select_date(page):
    for month_index in range(
        MAX_MONTHS_TO_SEARCH
    ):
        valid_dates = get_valid_dates(page)

        if valid_dates:
            selection = valid_dates[0]
            selected_date = selection["date"]

            selection["element"].click()

            log(
                "Selected date: "
                + selected_date.strftime(
                    "%Y-%m-%d"
                )
            )

            return selected_date

        log(
            "No valid dates found in the current "
            f"calendar. Search "
            f"{month_index + 1}/{MAX_MONTHS_TO_SEARCH}."
        )

        if month_index == MAX_MONTHS_TO_SEARCH - 1:
            break

        if not move_to_next_month(page):
            break

    return None


# ============================================================
# UNIT
# ============================================================

def select_unit(page):
    unit_field = page.get_by_role(
        "textbox",
        name="Unidade",
    )

    if unit_field.count() == 0:
        unit_field = page.get_by_text(
            "Selecione a unidade que deseja atendimento",
            exact=False,
        )

    if unit_field.count() == 0:
        raise RuntimeError(
            "Unit selection field was not found."
        )

    unit_field.first.wait_for(
        state="visible",
        timeout=15_000,
    )

    unit_field.first.click()

    unit_option = page.get_by_role(
        "option",
        name=re.compile(
            re.escape(EXPECTED_UNIT),
            re.IGNORECASE,
        ),
    )

    if unit_option.count() == 0:
        unit_option = page.get_by_text(
            EXPECTED_UNIT,
            exact=True,
        )

    if unit_option.count() == 0:
        raise RuntimeError(
            f"Expected unit was not found: "
            f"{EXPECTED_UNIT}"
        )

    unit_option.first.click()

    log(
        f"Unit selected: {EXPECTED_UNIT}."
    )


# ============================================================
# AVAILABLE TIMES
# ============================================================

def list_available_times(page):
    time_field = page.get_by_role(
        "textbox",
        name="Horários disponíveis",
    )

    time_field.wait_for(
        state="visible",
        timeout=15_000,
    )

    time_field.click()
    page.wait_for_timeout(700)

    options = page.get_by_role("option")
    available_times = []

    for index in range(options.count()):
        option = options.nth(index)

        try:
            text = option.inner_text().strip()

            if time_to_minutes(text) is not None:
                available_times.append(text)

        except Exception:
            continue

    return list(
        dict.fromkeys(available_times)
    )


def select_time(page, selected_time):
    option = page.get_by_role(
        "option",
        name=selected_time,
        exact=True,
    )

    option.wait_for(
        state="visible",
        timeout=10_000,
    )

    option.click()

    log(
        f"Appointment time selected: {selected_time}."
    )


# ============================================================
# PUBLIC SAFE EXECUTION
# ============================================================

def run():
    validate_environment()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=HEADLESS,
        )

        context = browser.new_context(
            viewport={
                "width": 1366,
                "height": 768,
            }
        )

        page = context.new_page()

        page.set_default_timeout(
            DEFAULT_TIMEOUT_MS
        )

        try:
            open_service_flow(page)

            availability_found = select_municipality(
                page
            )

            if not availability_found:
                log(
                    "Execution completed without "
                    "available appointments."
                )

                return

            check_for_blocking(page)

            open_date_schedule(page)

            selected_date = select_date(page)

            if selected_date is None:
                log(
                    "No valid appointment dates were found."
                )

                return

            select_unit(page)

            available_times = list_available_times(
                page
            )

            if not available_times:
                log(
                    "No appointment times were found "
                    "for the selected date."
                )

                return

            selected_time = choose_best_time(
                available_times
            )

            if selected_time is None:
                log(
                    "No valid appointment time "
                    "could be selected."
                )

                return

            select_time(
                page,
                selected_time,
            )

            save_screenshot(page)

            log(
                "An appointment candidate was found."
            )

            log(
                "The public version stops before entering "
                "contact details or confirming an appointment."
            )

            log(
                "Selected candidate: "
                f"{selected_date.strftime('%Y-%m-%d')} "
                f"at {selected_time}."
            )

        except PlaywrightTimeoutError as error:
            log(
                "The portal took too long to respond: "
                f"{error}"
            )

            save_screenshot(page)

        except Exception as error:
            log(
                "Execution error: "
                f"{type(error).__name__}: {error}"
            )

            save_screenshot(page)

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    run()
