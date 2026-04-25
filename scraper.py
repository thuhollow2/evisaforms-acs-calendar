from __future__ import annotations

import datetime as dt
import atexit
import html
import json
import multiprocessing as mp
import random
import re
import time
import os
import platform as py_platform
import sys
import ddddocr
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from queue import Empty
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urljoin, urlparse
from urllib.request import Request, urlopen

from PIL import Image
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, TimeoutError as PlaywrightTimeoutError, sync_playwright
from playwright_stealth import Stealth

current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)

BASE_ACS_URL = "https://evisaforms.state.gov/acs/"
ACS_SCHEDULING_URL = "https://evisaforms.state.gov/Instructions/ACSSchedulingSystem.asp"
DEFAULT_CONFIG_PATH = "config.json"
DEFAULT_INTERVAL_MINUTES = 2
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_CHECK_ONCE_MAX_SECONDS = 180
DEFAULT_ACTION_DELAY_MS = 90
DEFAULT_CALENDAR_REQUEST_DELAY_SECONDS = 0.8
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
)
STEALTH = Stealth()

CSRF_PATTERNS = (
    re.compile(r"CSRFToken=(\w+)", re.IGNORECASE),
    re.compile(r'name=["\']CSRFToken["\'][^>]*value=["\'](\w+)["\']', re.IGNORECASE),
)
HTML_TAG_RE = re.compile(r"<[^>]+>")
CITY_OPTION_RE = re.compile(
    r"new\s+Option\(\s*['\"]((?:\\.|[^'\"\\])*)['\"]\s*,\s*['\"]([A-Z0-9]{3,})['\"]\s*,\s*false\s*,\s*false\s*\)\s*;",
    re.IGNORECASE,
)
COUNTRY_SELECT_RE = re.compile(
    r"<select\b[^>]*name=[\"']CountryCodeShow[\"'][^>]*>(?P<body>.*?)</select>",
    re.IGNORECASE | re.DOTALL,
)
OPTION_TAG_RE = re.compile(
    r"<option\b[^>]*value=[\"']([^\"']*)[\"'][^>]*>(.*?)</option>",
    re.IGNORECASE | re.DOTALL,
)
COUNTRY_BLOCK_RE = re.compile(
    r'if\s*\(\s*selectedvalue\s*==\s*"([^"]+)"\s*\)\s*\{(.*?)\n\}',
    re.IGNORECASE | re.DOTALL,
)
AVAILABLE_CELL_RE = re.compile(
    r"<td\b[^>]*bgcolor\s*=\s*['\"]#ffffc0['\"][^>]*>(.*?)</td>",
    re.IGNORECASE | re.DOTALL,
)
DAY_LINK_RE = re.compile(r"<a\b[^>]*>(\d+)</a>", re.IGNORECASE)
HREF_RE = re.compile(r"<a\b[^>]*href\s*=\s*['\"]?([^'\"\s>]+)", re.IGNORECASE)
AVAILABLE_COUNT_RE = re.compile(r"Available\s*\((\d+)\)", re.IGNORECASE)
DEFAULT_PAGE_NAME_RE = re.compile(
    r"<td[^>]*align\s*=\s*center[^>]*>\s*<br>\s*(.*?)\s*<br>",
    re.IGNORECASE | re.DOTALL,
)
TIME_TEXT_RE = re.compile(r"(\d{1,2}:\d{2})")
TIME_COUNT_RE = re.compile(r"\((\d+)\s+Available\)", re.IGNORECASE)
CONFIRMATION_LABEL_RE = re.compile(r":\s*$")
RELATIVE_MONTH_VALUE_RE = re.compile(r"^\+\d+$")
AVAILABLE_DATE_RECORDS_DIR = "available_date_records"
BOOKING_ARTIFACTS_DIR = "booking_artifacts"
CITY_CACHE_DIR = "cache"
CITY_CACHE_FILE = "cache/city.md"
BOOKING_CITIZENSHIP_CACHE_FILE = "cache/citizenship.md"
BOOKING_BIRTH_COUNTRY_CACHE_FILE = "cache/birthcountry.md"
LOG_DIR = "log"
LOG_PATH_ENV = "EVISAFORMS_LOG_PATH"
LOG_OWNER_PID_ENV = "EVISAFORMS_LOG_OWNER_PID"
LOG_SESSION_ENV = "EVISAFORMS_LOG_SESSION"
CITY_CACHE_TTL_SECONDS = 24 * 60 * 60
DEFAULT_RETRY_BACKOFF_SECONDS = 2.0
MAX_RETRY_BACKOFF_SECONDS = 60.0
RETRY_BACKOFF_JITTER_RATIO = 0.25
REQUEST_CONTEXT_EXPIRED_CONSECUTIVE_MONTH_FETCH_ERRORS = 4
MONTH_YEAR_TEXT_RE = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\b\s+(\d{4})\b",
    re.IGNORECASE,
)
HTML_MONTH_INPUT_RE = re.compile(
    r'name=["\']nMonth["\'][^>]*value=["\'](\d{1,2})["\']|value=["\'](\d{1,2})["\'][^>]*name=["\']nMonth["\']',
    re.IGNORECASE,
)
HTML_YEAR_INPUT_RE = re.compile(
    r'name=["\']nYear["\'][^>]*value=["\'](\d{4})["\']|value=["\'](\d{4})["\'][^>]*name=["\']nYear["\']',
    re.IGNORECASE,
)
HTML_MONTH_YEAR_QUERY_RE = re.compile(
    r"nMonth=(\d{1,2}).{0,120}?nYear=(\d{4})|nYear=(\d{4}).{0,120}?nMonth=(\d{1,2})",
    re.IGNORECASE | re.DOTALL,
)
HTML_SELECT_RE = re.compile(
    r"<select\b[^>]*name=[\"'](?P<name>nMonth|nYear)[\"'][^>]*>(?P<body>.*?)</select>",
    re.IGNORECASE | re.DOTALL,
)
HTML_SELECTED_OPTION_RE = re.compile(
    r"<option\b(?=[^>]*selected)[^>]*value=[\"']?([^\"' >]+)",
    re.IGNORECASE | re.DOTALL,
)
SERVICE_INPUT_ROW_RE = re.compile(
    r"<tr\b[^>]*>.*?"
    r"<input\b[^>]*type\s*=\s*(?:['\"])?(?P<input_type>radio|checkbox)(?:['\"])?[^>]*"
    r"name\s*=\s*(?:['\"])?(?P<input_name>chkservice|chkservicespec)(?:['\"])?[^>]*>"
    r".*?</td>\s*<td\b[^>]*>(?P<label>.*?)</td>.*?</tr>",
    re.IGNORECASE | re.DOTALL,
)
GENERIC_SELECT_RE_TEMPLATE = r"<select\b[^>]*name=[\"']{name}[\"'][^>]*>(?P<body>.*?)</select>"
MONTH_NAME_TO_NUMBER = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}
PERSISTENT_BROWSER_PROFILE_DIR = os.path.expanduser("~/.config/playwright-acs-calendar")
_LOGGING_INITIALIZED = False
_LOG_FILE_HANDLE = None
_ORIGINAL_STDOUT = sys.stdout
_ORIGINAL_STDERR = sys.stderr


class TeeStream:
    def __init__(self, *streams: Any) -> None:
        self._streams = streams

    def write(self, data: str) -> int:
        for stream in self._streams:
            try:
                stream.write(data)
                if "\n" in data:
                    stream.flush()
            except Exception:
                continue
        return len(data)

    def flush(self) -> None:
        for stream in self._streams:
            try:
                stream.flush()
            except Exception:
                continue

    def isatty(self) -> bool:
        return any(getattr(stream, "isatty", lambda: False)() for stream in self._streams)

    @property
    def encoding(self) -> str:
        for stream in self._streams:
            encoding = getattr(stream, "encoding", None)
            if encoding:
                return encoding
        return "utf-8"


def initialize_output_logging() -> None:
    global _LOGGING_INITIALIZED, _LOG_FILE_HANDLE
    if _LOGGING_INITIALIZED:
        return

    current_pid = str(os.getpid())
    log_path_raw = os.environ.get(LOG_PATH_ENV)
    log_owner_pid = os.environ.get(LOG_OWNER_PID_ENV)
    if not log_path_raw or log_owner_pid != current_pid:
        log_dir = Path(LOG_DIR)
        log_dir.mkdir(parents=True, exist_ok=True)
        session_id = os.environ.get(LOG_SESSION_ENV)
        if not session_id:
            session_id = dt.datetime.now().astimezone().strftime("%Y%m%d_%H%M%S_%f")
            os.environ[LOG_SESSION_ENV] = session_id
        log_path = log_dir / f"run_{session_id}_pid{current_pid}.log"
        os.environ[LOG_PATH_ENV] = str(log_path.resolve())
        os.environ[LOG_OWNER_PID_ENV] = current_pid
    else:
        log_path = Path(log_path_raw)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    _LOG_FILE_HANDLE = log_path.open("a", encoding="utf-8", buffering=1)
    sys.stdout = TeeStream(sys.stdout, _LOG_FILE_HANDLE)
    sys.stderr = TeeStream(sys.stderr, _LOG_FILE_HANDLE)
    _LOGGING_INITIALIZED = True

    def close_log_file() -> None:
        global _LOG_FILE_HANDLE
        sys.stdout = _ORIGINAL_STDOUT
        sys.stderr = _ORIGINAL_STDERR
        if _LOG_FILE_HANDLE is None:
            return
        try:
            _LOG_FILE_HANDLE.flush()
            _LOG_FILE_HANDLE.close()
        except Exception:
            pass
        _LOG_FILE_HANDLE = None

    atexit.register(close_log_file)
    return


def should_disable_linux_sandbox() -> bool:
    if os.name != "posix":
        return False
    if py_platform.system().lower() != "linux":
        return False
    geteuid = getattr(os, "geteuid", None)
    if not callable(geteuid):
        return False
    try:
        return geteuid() == 0
    except Exception:
        return False


@dataclass
class Location:
    city: str
    post_code: str
    display_name: str
    country: str = ""


@dataclass(frozen=True)
class CalendarRequestContext:
    cookie_header: str
    csrf_token: str
    appointment_type: str
    service_type: str
    service_label: Optional[str] = None
    calendar_year: Optional[int] = None
    calendar_month: Optional[int] = None


@dataclass(frozen=True)
class MonthTarget:
    year: int
    month: int


@dataclass(frozen=True)
class AppointmentDay:
    year: int
    month: int
    day: int
    count: Optional[int]
    booking_url: Optional[str]

    @property
    def date_value(self) -> dt.date:
        return dt.date(self.year, self.month, self.day)

    @property
    def iso_date(self) -> str:
        return self.date_value.isoformat()


@dataclass(frozen=True)
class MonthAvailability:
    year: int
    month: int
    available: bool
    days: Tuple[AppointmentDay, ...]


@dataclass(frozen=True)
class TimeSlot:
    value: str
    label: str
    count: Optional[int]

    @property
    def time_value(self) -> dt.time:
        return dt.datetime.strptime(self.value, "%Y/%m/%d %H:%M").time()


@dataclass(frozen=True)
class DateSelectionRule:
    start: dt.date
    end: dt.date
    weight: int
    raw_value: str

    def matches(self, candidate: dt.date) -> bool:
        return self.start <= candidate <= self.end


@dataclass(frozen=True)
class DateSelectionConfig:
    rules: Tuple[DateSelectionRule, ...]
    filter_mode: str
    final_pick: str


@dataclass(frozen=True)
class TimeSelectionConfig:
    filter_mode: str
    final_pick: str


@dataclass(frozen=True)
class BubbleConfig:
    enabled: bool
    password: str


@dataclass(frozen=True)
class ApplicantConfig:
    last_name: str = ""
    first_name: str = ""
    dob_day: Optional[int] = None
    dob_month: Optional[int] = None
    dob_year: Optional[int] = None
    telephone: str = ""
    email: str = ""
    citizenship: str = ""
    birth_country: str = ""
    sex: str = ""
    passport_number: str = ""
    non_applicant_1: str = ""
    non_applicant_2: str = ""


@dataclass(frozen=True)
class BookingConfig:
    enabled: bool
    date_selection: DateSelectionConfig
    time_selection: TimeSelectionConfig
    bubble: BubbleConfig
    applicant: Optional[ApplicantConfig]
    applicant_error: Optional[str]
    artifacts_dir: str


class BookingConfigError(RuntimeError):
    pass


class PageState(str, Enum):
    EXPIRED_ID = "expired_id"
    BAD_SUBMIT = "bad_submit"
    BAD_SUBMIT_CHANGE = "bad_submit_change"
    CANCEL_BOOKING = "cancel_booking"
    CANCEL_SUBMIT = "cancel_submit"
    APPOINTMENT_CANCEL_QUERY = "appointment_cancel_query"
    APPOINTMENT_DETAIL = "appointment_detail"
    VERIFICATION = "verification"
    APPOINTMENT_SELECTION = "appointment_selection"
    SERVICE_SELECTION_LOADING = "service_selection_loading"
    SERVICE_SELECTION = "service_selection"
    CALENDAR = "calendar"
    BOOKING_FORM = "booking_form"
    RETRY = "retry"
    CONFIRMATION = "confirmation"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class PageSnapshot:
    state: PageState
    url: str
    body_text: str
    has_inline_verification_prompt: bool


@dataclass(frozen=True)
class ServiceSelectionSnapshot:
    service_inputs: Any
    service_labels: Tuple[str, ...]
    selection_mode: str

    @property
    def input_count(self) -> int:
        return len(self.service_labels)


@dataclass(frozen=True)
class RuntimeConfigValues:
    months: Tuple[str, ...]
    interval_minutes: int
    timeout_seconds: int
    check_once_max_seconds: int
    action_delay_ms: int
    calendar_request_delay_seconds: float
    browser_channel: Optional[str]
    city_value: str
    service_index: Optional[int]
    service_indexs: Tuple[int, ...]
    booking_config: BookingConfig
    show_browser: bool
    user_agent: str


def solve_verification_image(image_bytes: bytes) -> str:
    ocr = ddddocr.DdddOcr(show_ad=False)
    verification_code = ocr.classification(image_bytes)
    return verification_code


def normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def is_expired_id_page_text(text: str) -> bool:
    text_lower = text.lower()
    return (
        "your support id" in text_lower
        and (
            "request rejected" in text_lower
            or "failureconfig" in text_lower
        )
    )


def normalize_city_token(text: str) -> str:
    compact = normalize_whitespace(html.unescape(text)).upper()
    return re.sub(r"[^A-Z0-9]+", "", compact)


def normalize_city_value(text: str) -> str:
    return normalize_whitespace(html.unescape(text)).upper()


def strip_html(fragment: str) -> str:
    return normalize_whitespace(html.unescape(HTML_TAG_RE.sub(" ", fragment)))


def extract_csrf_token(page_html: str) -> str:
    for pattern in CSRF_PATTERNS:
        match = pattern.search(page_html)
        if match:
            return match.group(1)
    raise RuntimeError("无法从页面中提取 CSRFToken")


def first_query_value(query: Dict[str, List[str]], key: str) -> Optional[str]:
    values = query.get(key)
    if not values:
        return None
    return values[0]


def first_matched_group(match: re.Match[str]) -> Optional[str]:
    for group in match.groups():
        if group is not None:
            return group
    return None


def extract_calendar_year_month_from_html(
    page_html: str,
) -> Tuple[Optional[int], Optional[int]]:
    month_match = HTML_MONTH_INPUT_RE.search(page_html)
    year_match = HTML_YEAR_INPUT_RE.search(page_html)
    month_value = parse_optional_int(first_matched_group(month_match)) if month_match else None
    year_value = parse_optional_int(first_matched_group(year_match)) if year_match else None
    if month_value is not None and year_value is not None and 1 <= month_value <= 12:
        return year_value, month_value

    selected_values: Dict[str, Optional[int]] = {"nMonth": None, "nYear": None}
    for select_match in HTML_SELECT_RE.finditer(page_html):
        selected_match = HTML_SELECTED_OPTION_RE.search(select_match.group("body"))
        if not selected_match:
            continue
        selected_values[select_match.group("name")] = parse_optional_int(selected_match.group(1))
    month_value = selected_values["nMonth"]
    year_value = selected_values["nYear"]
    if month_value is not None and year_value is not None and 1 <= month_value <= 12:
        return year_value, month_value

    query_match = HTML_MONTH_YEAR_QUERY_RE.search(page_html)
    if query_match:
        if query_match.group(1) and query_match.group(2):
            month_value = parse_optional_int(query_match.group(1))
            year_value = parse_optional_int(query_match.group(2))
        else:
            year_value = parse_optional_int(query_match.group(3))
            month_value = parse_optional_int(query_match.group(4))
        if month_value is not None and year_value is not None and 1 <= month_value <= 12:
            return year_value, month_value

    plain_text = strip_html(page_html)
    month_year_match = MONTH_YEAR_TEXT_RE.search(plain_text)
    if month_year_match:
        month_value = MONTH_NAME_TO_NUMBER.get(month_year_match.group(1).lower())
        year_value = parse_optional_int(month_year_match.group(2))
        if month_value is not None and year_value is not None:
            return year_value, month_value

    return None, None


def extract_calendar_request_context(
    current_url: str,
    cookie_header: str,
    fallback_html: str = "",
    fallback_service_label: Optional[str] = None,
) -> CalendarRequestContext:
    query = parse_qs(urlparse(current_url).query)
    csrf_token = first_query_value(query, "CSRFToken")
    appointment_type = first_query_value(query, "type")
    service_type = first_query_value(query, "servicetype")
    calendar_year = parse_optional_int(first_query_value(query, "nYear"))
    calendar_month = parse_optional_int(first_query_value(query, "nMonth"))

    if not csrf_token and fallback_html:
        csrf_token = extract_csrf_token(fallback_html)
    if fallback_html and (calendar_year is None or calendar_month is None):
        html_year, html_month = extract_calendar_year_month_from_html(fallback_html)
        if calendar_year is None:
            calendar_year = html_year
        if calendar_month is None:
            calendar_month = html_month

    if not csrf_token or not appointment_type or not service_type:
        raise RuntimeError("无法解析日历请求所需的参数")

    return CalendarRequestContext(
        cookie_header=cookie_header,
        csrf_token=csrf_token,
        appointment_type=appointment_type,
        service_type=service_type,
        service_label=fallback_service_label,
        calendar_year=calendar_year,
        calendar_month=calendar_month,
    )


def build_default_headers(
    user_agent: str,
    referer: Optional[str] = None,
) -> Dict[str, str]:
    headers = {
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
            "image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": user_agent,
    }
    if referer:
        headers["Referer"] = referer
    return headers


def decode_response_body(response) -> str:
    body = response.read()
    charset = response.headers.get_content_charset() or "utf-8"
    try:
        return body.decode(charset, errors="replace")
    except LookupError:
        return body.decode("utf-8", errors="replace")


def coerce_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "y", "on"}:
            return True
        if lowered in {"0", "false", "no", "n", "off", ""}:
            return False
    return bool(value)


def parse_iso_date(value: str) -> dt.date:
    try:
        return dt.datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise RuntimeError(f"日期格式必须是 YYYY-MM-DD, 当前值: {value}") from exc


def parse_optional_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_month_item(raw_month: Any) -> str:
    if isinstance(raw_month, bool):
        raise RuntimeError("config.json 中的 months 不能包含布尔值")
    if isinstance(raw_month, str):
        value = raw_month.strip()
        if not value:
            raise RuntimeError("config.json 中的 months 不能包含空字符串")
        if RELATIVE_MONTH_VALUE_RE.fullmatch(value):
            return value
    raise RuntimeError(
        f"config.json 中的 months 每一项必须是 +0, +1 这类字符串, 当前值: {raw_month}"
    )


def validate_months(months: Sequence[Any]) -> Tuple[str, ...]:
    validated = [parse_month_item(month) for month in months]
    if not validated:
        raise RuntimeError("config.json 中的 months 不能为空")
    return tuple(validated)


def add_month_offset(base_year: int, base_month: int, offset: int) -> MonthTarget:
    month_index = (base_year * 12 + (base_month - 1)) + offset
    target_year, target_month_index = divmod(month_index, 12)
    return MonthTarget(year=target_year, month=target_month_index + 1)


def load_config(config_path: str | Path = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    path = Path(config_path)
    if not path.is_file():
        raise RuntimeError(f"未找到配置文件: {path.resolve()}")

    try:
        with path.open("r", encoding="utf-8") as file:
            config = json.load(file)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"配置文件不是合法的 JSON: {exc}") from exc

    if not isinstance(config, dict):
        raise RuntimeError("config.json 顶层必须是 JSON 对象")
    return config


def resolve_months_from_config(config: Dict[str, Any]) -> Tuple[str, ...]:
    raw_months = config.get("months")
    if raw_months is None:
        raise RuntimeError("config.json 需要配置 months")
    if not isinstance(raw_months, list):
        raise RuntimeError("config.json 中的 months 必须是数组")
    return validate_months(raw_months)


def extract_country_code_map(page_html: str) -> Dict[str, str]:
    country_code_map: Dict[str, str] = {}
    match = COUNTRY_SELECT_RE.search(page_html)
    if not match:
        return country_code_map

    for raw_value, raw_label in OPTION_TAG_RE.findall(match.group("body")):
        country_code = normalize_whitespace(raw_value).upper()
        country_name = normalize_whitespace(strip_html(raw_label))
        if not country_code or not country_name or country_name.lower().startswith("select "):
            continue
        country_code_map[country_code] = country_name

    return country_code_map


def build_location(
    country: str,
    city_name: str,
    post_code: str,
) -> Optional[Location]:
    normalized_country = normalize_whitespace(country)
    normalized_city = normalize_whitespace(city_name)
    normalized_post_code = normalize_whitespace(post_code).upper()
    city_token = normalize_city_token(normalized_city)
    if (
        not normalized_country
        or not city_token
        or not normalized_post_code
        or normalized_city.lower().startswith("select ")
    ):
        return None

    return Location(
        city=normalized_city,
        post_code=normalized_post_code,
        display_name=normalized_city,
        country=normalized_country,
    )


def extract_city_options(page_html: str) -> List[Location]:
    country_code_map = extract_country_code_map(page_html)
    seen: set[Tuple[str, str]] = set()
    locations: List[Location] = []

    for raw_country_code, block_body in COUNTRY_BLOCK_RE.findall(page_html):
        country_code = normalize_whitespace(raw_country_code).upper()
        country_name = country_code_map.get(country_code, country_code)
        for city_name_raw, post_code in CITY_OPTION_RE.findall(block_body):
            city_name = normalize_whitespace(
                city_name_raw.replace("\\'", "'").replace('\\"', '"')
            )
            location = build_location(country_name, city_name, post_code)
            if location is None:
                continue

            key = (normalize_city_token(location.city), location.post_code)
            if key in seen:
                continue
            seen.add(key)
            locations.append(location)

    return locations


def extract_city_options_from_dom(page: Page) -> List[Location]:
    rows = page.evaluate(
        """() => {
            const countrySelect = document.querySelector("select[name='CountryCodeShow']");
            const citySelect = document.querySelector("select[name='PostCodeShow']");
            if (!countrySelect || !citySelect || typeof moveover !== "function") {
                return [];
            }

            const results = [];
            for (let index = 0; index < countrySelect.options.length; index += 1) {
                const countryOption = countrySelect.options[index];
                const countryValue = (countryOption.value || "").trim();
                const countryName = (countryOption.text || "").replace(/\\s+/g, " ").trim();
                if (!countryValue || !countryName || /^select /i.test(countryName)) {
                    continue;
                }

                countrySelect.selectedIndex = index;
                moveover();

                for (let cityIndex = 0; cityIndex < citySelect.options.length; cityIndex += 1) {
                    const cityOption = citySelect.options[cityIndex];
                    const postCode = (cityOption.value || "").trim();
                    const cityName = (cityOption.text || "").replace(/\\s+/g, " ").trim();
                    if (!postCode || !cityName || /^select /i.test(cityName)) {
                        continue;
                    }

                    results.push({
                        country: countryName,
                        city: cityName,
                        post_code: postCode,
                    });
                }
            }

            return results;
        }"""
    )

    seen: set[Tuple[str, str]] = set()
    locations: List[Location] = []
    if not isinstance(rows, list):
        return locations

    for row in rows:
        if not isinstance(row, dict):
            continue
        location = build_location(
            str(row.get("country", "")),
            str(row.get("city", "")),
            str(row.get("post_code", "")),
        )
        if location is None:
            continue

        key = (normalize_city_token(location.city), location.post_code)
        if key in seen:
            continue
        seen.add(key)
        locations.append(location)

    return locations


def wait_for_city_options(page: Page, timeout_seconds: int) -> None:
    deadline = time.monotonic() + max(1, timeout_seconds)
    while time.monotonic() < deadline:
        try:
            dom_options = extract_city_options_from_dom(page)
            regex_options = extract_city_options(page.content())
            if dom_options:
                break
        except Exception:
            pass


def location_option_key(location: Location) -> Tuple[str, str, str]:
    return (
        normalize_country_option(location.country),
        normalize_city_token(location.city),
        normalize_whitespace(location.post_code).upper(),
    )


def dedupe_locations(locations: Sequence[Location]) -> List[Location]:
    deduped: List[Location] = []
    seen: set[Tuple[str, str, str]] = set()
    for location in locations:
        key = location_option_key(location)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(location)
    return deduped


def dedupe_option_values(values: Sequence[str]) -> Tuple[str, ...]:
    deduped: List[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = normalize_country_option(value)
        if not normalized or normalized == "SELECT" or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)
    return tuple(deduped)


def choose_preferred_locations(dom_options: Sequence[Location], regex_options: Sequence[Location]) -> List[Location]:
    dom_unique = dedupe_locations(dom_options)
    regex_unique = dedupe_locations(regex_options)
    dom_keys = [location_option_key(location) for location in dom_unique]
    regex_keys = [location_option_key(location) for location in regex_unique]
    is_consistent = dom_keys == regex_keys
    chosen_source = "DOM" if len(dom_unique) >= len(regex_unique) else "Regex"
    print(
        "\n提示\n====\n城市列表 DOM/正则完整比较: "
        f"{'一致' if is_consistent else '不一致'}, "
        f"DOM={len(dom_unique)}, Regex={len(regex_unique)}, "
        f"使用{chosen_source}"
    )
    return dom_unique if chosen_source == "DOM" else regex_unique


def choose_preferred_option_values(
    field_label: str,
    dom_options: Sequence[str],
    regex_options: Sequence[str],
) -> Tuple[str, ...]:
    dom_unique = dedupe_option_values(dom_options)
    regex_unique = dedupe_option_values(regex_options)
    if not dom_unique and not regex_unique:
        return ()

    is_consistent = dom_unique == regex_unique
    chosen_source = "DOM" if len(dom_unique) >= len(regex_unique) else "Regex"
    print(
        f"\n提示\n====\n{field_label} DOM/正则完整比较: "
        f"{'一致' if is_consistent else '不一致'}, "
        f"DOM={len(dom_unique)}, Regex={len(regex_unique)}, "
        f"使用{chosen_source}"
    )
    return dom_unique if chosen_source == "DOM" else regex_unique


def extract_service_options_from_html(page_html: str) -> Tuple[Tuple[str, ...], str]:
    labels: List[str] = []
    input_types: List[str] = []
    for match in SERVICE_INPUT_ROW_RE.finditer(page_html):
        label = strip_html(match.group("label"))
        if not label:
            continue
        labels.append(label)
        input_types.append(normalize_whitespace(match.group("input_type")).lower())

    if not labels:
        return (), "radio"

    selection_mode = "checkbox" if any(input_type == "checkbox" for input_type in input_types) else "radio"
    return tuple(labels), selection_mode


def load_city_options_from_page(page: Page, timeout_seconds: int) -> List[Location]:
    wait_for_city_options(page, timeout_seconds)
    dom_options = extract_city_options_from_dom(page)
    regex_options = extract_city_options(page.content())
    return choose_preferred_locations(dom_options, regex_options)


def windows_like_http_headers() -> Dict[str, str]:
    return {
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua-mobile": "?0",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
    }


def apply_windows_ua_overrides(
    context: BrowserContext,
    page: Page,
    user_agent: str,
) -> None:
    user_agent_json = json.dumps(user_agent)
    page.add_init_script(
        f"""
        (() => {{
            const ua = {user_agent_json};
            Object.defineProperty(navigator, 'userAgent', {{ get: () => ua }});
            Object.defineProperty(navigator, 'platform', {{ get: () => 'Win32' }});
            Object.defineProperty(navigator, 'vendor', {{ get: () => 'Google Inc.' }});
            Object.defineProperty(navigator, 'maxTouchPoints', {{ get: () => 0 }});
        }})();
        """
    )

    try:
        session = context.new_cdp_session(page)
        session.send(
            "Emulation.setUserAgentOverride",
            {
                "userAgent": user_agent,
                "platform": "Windows",
                "acceptLanguage": "zh-CN,zh;q=0.9,en;q=0.8",
            },
        )
    except Exception:
        pass

    context.set_extra_http_headers(windows_like_http_headers())


def launch_persistent_context(
    playwright: Playwright,
    headless: bool,
    user_agent: str,
) -> BrowserContext:
    launch_args = [
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-blink-features=AutomationControlled",
    ]
    if should_disable_linux_sandbox():
        launch_args.extend(["--no-sandbox", "--disable-dev-shm-usage"])

    if headless:
        launch_args.extend(["--headless=new", "--disable-gpu"])

    return playwright.chromium.launch_persistent_context(
        user_data_dir=PERSISTENT_BROWSER_PROFILE_DIR,
        headless=headless,
        args=launch_args,
        viewport={"width": 1366, "height": 768},
        locale="en-US",
        user_agent=user_agent,
        extra_http_headers=windows_like_http_headers(),
    )


def escape_markdown_cell(value: str) -> str:
    return normalize_whitespace(value).replace("|", "\\|")


def unescape_markdown_cell(value: str) -> str:
    return normalize_whitespace(value.replace("\\|", "|"))


def normalize_country_option(value: str) -> str:
    return normalize_whitespace(value).strip().upper()


def save_single_column_markdown(
    file_path: str,
    column_name: str,
    values: Sequence[str],
) -> None:
    output_path = Path(file_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"| Index | {column_name} |",
        "| -------- | -------- |",
    ]
    for index, value in enumerate(values, start=1):
        lines.append(f"| {index} | {escape_markdown_cell(value)} |")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def remove_file_if_exists(file_path: str) -> None:
    path = Path(file_path)
    if not path.exists():
        return
    try:
        path.unlink()
    except Exception:
        pass


def load_cached_city_options(max_age_seconds: int = CITY_CACHE_TTL_SECONDS) -> List[Location]:
    cache_path = Path(CITY_CACHE_FILE)
    if not cache_path.is_file():
        return []

    try:
        cache_age_seconds = time.time() - cache_path.stat().st_mtime
        if cache_age_seconds > max_age_seconds:
            print(f"\n城市缓存已过期 ({int(cache_age_seconds)} 秒), 忽略缓存")
            return []
        raw_text = cache_path.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"\n城市缓存读取失败, 忽略缓存\n====\n{exc}")
        return []

    locations: List[Location] = []
    seen: set[Tuple[str, str]] = set()
    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line.startswith("|"):
            continue
        if "Index" in line and "Country" in line and "City" in line and "Code" in line:
            continue
        if set(line.replace("|", "").replace("-", "").replace(" ", "")) == set():
            continue

        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 4:
            continue

        _, country_name_raw, city_name_raw, post_code_raw = cells
        country_name = unescape_markdown_cell(country_name_raw)
        city_name = unescape_markdown_cell(city_name_raw)
        post_code = normalize_whitespace(post_code_raw).upper()
        location = build_location(country_name, city_name, post_code)
        if location is None:
            continue

        key = (normalize_city_token(location.city), location.post_code)
        if key in seen:
            continue
        seen.add(key)
        locations.append(location)

    return locations


def save_cached_city_options(locations: Sequence[Location]) -> None:
    cache_dir = Path(CITY_CACHE_DIR)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = Path(CITY_CACHE_FILE)
    lines = [
        "| Index | Country | City | Code |",
        "| -------- | -------- | -------- | -------- |",
    ]
    for index, location in enumerate(locations, start=1):
        lines.append(
            f"| {index} | {escape_markdown_cell(location.country)} | "
            f"{escape_markdown_cell(location.city)} | {location.post_code} |"
        )
    cache_path.write_text("\n".join(lines), encoding="utf-8")


def find_location_in_options(
    options: Sequence[Location],
    city: str,
) -> Optional[Location]:
    city_token = normalize_city_token(city)
    exact_matches = [
        option for option in options if normalize_city_token(option.city) == city_token
    ]
    if len(exact_matches) == 1:
        return exact_matches[0]
    if len(exact_matches) > 1:
        joined = ", ".join(f"{option.city} ({option.post_code})" for option in exact_matches)
        raise RuntimeError(f"城市 {city} 匹配到多个地点, 请写得更精确: {joined}")

    fuzzy_matches = [
        option for option in options if city_token in normalize_city_token(option.city)
    ]
    if len(fuzzy_matches) == 1:
        return fuzzy_matches[0]
    if len(fuzzy_matches) > 1:
        joined = ", ".join(f"{option.city} ({option.post_code})" for option in fuzzy_matches)
        raise RuntimeError(f"城市 {city} 匹配到多个地点, 请写得更精确: {joined}")

    return None


def resolve_location_from_city(
    city: str,
    headless: bool,
    timeout_seconds: int,
    user_agent: str,
) -> Location:
    city = normalize_city_value(city)
    city_token = normalize_city_token(city)
    if not city_token:
        raise RuntimeError("config.json 中的 city 不能为空")

    print(f"\n解析城市: {city}")
    cached_options = load_cached_city_options()
    if cached_options:
        print(f"读取城市缓存: {len(cached_options)} 个地点")
        cached_location = find_location_in_options(cached_options, city)
        if cached_location is not None:
            print(
                f"命中城市缓存: {cached_location.city} ({cached_location.post_code}), "
                "按缓存有效期直接使用"
            )
            return cached_location
        print("城市缓存中不存在当前城市, 改为在线解析")

    options: List[Location] = []
    online_parse_error: Optional[Exception] = None
    try:
        with sync_playwright() as playwright:
            launch_args = ["--disable-blink-features=AutomationControlled"]
            if should_disable_linux_sandbox():
                launch_args.extend(["--no-sandbox", "--disable-dev-shm-usage"])

            browser = playwright.chromium.launch(
                headless=headless,
                args=launch_args,
            )
            try:
                context = browser.new_context(
                    user_agent=user_agent,
                    locale="en-US",
                    viewport={"width": 1366, "height": 768},
                    extra_http_headers=windows_like_http_headers(),
                )
                page = context.new_page()
                apply_windows_ua_overrides(context, page, user_agent)
                STEALTH.apply_stealth_sync(page)
                page.goto(
                    ACS_SCHEDULING_URL,
                    wait_until="networkidle",
                    timeout=timeout_seconds * 1000,
                )
                print("\n当前页面: 城市列表页")
                print(f"URL: {page.url}")
                options = load_city_options_from_page(page, timeout_seconds)
                print(f"城市列表 DOM/脚本解析数量: {len(options)}")
                context.close()
            finally:
                browser.close()

            if not options:
                print("\n提示\n====\n常规上下文未解析到城市列表, 改用持久化上下文重试")
                persistent_context = launch_persistent_context(playwright, headless=headless, user_agent=user_agent)
                try:
                    page = persistent_context.pages[0] if persistent_context.pages else persistent_context.new_page()
                    apply_windows_ua_overrides(persistent_context, page, user_agent)
                    STEALTH.apply_stealth_sync(page)
                    page.goto(
                        ACS_SCHEDULING_URL,
                        wait_until="networkidle",
                        timeout=timeout_seconds * 1000,
                    )
                    print("\n当前页面: 城市列表页")
                    print(f"URL: {page.url}")
                    options = load_city_options_from_page(page, timeout_seconds)
                    print(f"城市列表 DOM/脚本解析数量: {len(options)}")
                finally:
                    persistent_context.close()

        if not options:
            raise RuntimeError("城市列表解析为空, 可能触发了验证码或页面策略拦截")
    except Exception as exc:
        online_parse_error = exc

    if online_parse_error is not None:
        raise online_parse_error

    print(f"城市列表解析完成: {len(options)} 个地点")
    save_cached_city_options(options)
    print(f"城市缓存已更新: {Path(CITY_CACHE_FILE).resolve()}")
    resolved_location = find_location_in_options(options, city)
    if resolved_location is not None:
        return resolved_location

    city_list = ", ".join(f"{option.city} ({option.post_code})" for option in options)
    raise RuntimeError(
        f"没有找到城市 {city}, 请检查拼写. 当前解析到的地点: {city_list}"
    )


def extract_display_name(page_html: str, fallback_city: str) -> str:
    match = DEFAULT_PAGE_NAME_RE.search(page_html)
    if not match:
        return fallback_city
    display_name = strip_html(match.group(1))
    return display_name or fallback_city


def parse_date_selection_rule(raw_item: Any, weight: int) -> DateSelectionRule:
    if isinstance(raw_item, str):
        exact_date = parse_iso_date(raw_item)
        return DateSelectionRule(
            start=exact_date,
            end=exact_date,
            weight=weight,
            raw_value=raw_item,
        )

    raise RuntimeError("booking.date_selection.targets 的每一项必须是 YYYY-MM-DD 日期字符串")


def parse_date_selection_config(raw_config: Any) -> DateSelectionConfig:
    config = raw_config if isinstance(raw_config, dict) else {}
    filter_mode = str(config.get("filter_mode", "none")).strip().lower()
    if filter_mode not in {"none", "weight", "max_available"}:
        raise RuntimeError("booking.date_selection.filter_mode 只能是 none, weight, max_available")

    final_pick = str(config.get("final_pick", "earliest")).strip().lower()
    if final_pick not in {"earliest", "latest"}:
        raise RuntimeError("booking.date_selection.final_pick 只能是 earliest, latest")

    targets_raw = config.get("targets", [])
    if targets_raw is None:
        targets_raw = []
    if not isinstance(targets_raw, list):
        raise RuntimeError("booking.date_selection.targets 必须是数组")

    weights_raw = config.get("weights", [])
    if weights_raw is None:
        weights_raw = []
    if not isinstance(weights_raw, list):
        raise RuntimeError("booking.date_selection.weights 必须是数组")

    if filter_mode == "weight":
        if not targets_raw:
            raise RuntimeError("booking.date_selection.filter_mode 为 weight 时, targets 不能为空")
        if len(weights_raw) != len(targets_raw):
            raise RuntimeError("booking.date_selection.filter_mode 为 weight 时, weights 长度必须与 targets 一致")

    rules: List[DateSelectionRule] = []
    for index, raw_item in enumerate(targets_raw):
        weight = 0
        if index < len(weights_raw):
            weight = int(weights_raw[index])
            if weight < 0:
                raise RuntimeError("booking.date_selection.weights 中的权重必须是非负整数")
        rules.append(parse_date_selection_rule(raw_item, weight))

    return DateSelectionConfig(
        rules=tuple(rules),
        filter_mode=filter_mode,
        final_pick=final_pick,
    )


def parse_time_selection_config(raw_config: Any) -> TimeSelectionConfig:
    config = raw_config if isinstance(raw_config, dict) else {}
    filter_mode = str(config.get("filter_mode", "none")).strip().lower()
    if filter_mode not in {"none", "max_available"}:
        raise RuntimeError("booking.time_selection.filter_mode 只能是 none, max_available")

    final_pick = str(config.get("final_pick", "earliest")).strip().lower()
    if final_pick not in {"earliest", "latest"}:
        raise RuntimeError("booking.time_selection.final_pick 只能是 earliest, latest")

    return TimeSelectionConfig(
        filter_mode=filter_mode,
        final_pick=final_pick,
    )


def parse_bubble_config(raw_config: Any) -> BubbleConfig:
    config = raw_config if isinstance(raw_config, dict) else {}
    return BubbleConfig(
        enabled=coerce_bool(config.get("enabled"), default=False),
        password=str(config.get("password", "") or "").strip(),
    )


def parse_applicant_config(raw_config: Any) -> Tuple[Optional[ApplicantConfig], Optional[str]]:
    if not isinstance(raw_config, dict):
        return ApplicantConfig(), None

    dob_day: Optional[int] = None
    dob_month: Optional[int] = None
    dob_year: Optional[int] = None
    dob_raw = raw_config.get("date_of_birth")
    if str(dob_raw or "").strip():
        try:
            dob_date = parse_iso_date(str(dob_raw))
        except RuntimeError as exc:
            return None, str(exc)
        dob_day = dob_date.day
        dob_month = dob_date.month
        dob_year = dob_date.year

    sex_raw = str(raw_config.get("sex", "")).strip().upper()
    if sex_raw and sex_raw not in {"M", "F"}:
        return None, "booking.applicant.sex 只能是 M, F"

    non_applicant_1 = str(raw_config.get("non_applicant_1", raw_config.get("txtNon1", ""))).strip()
    non_applicant_2 = str(raw_config.get("non_applicant_2", raw_config.get("txtNon2", ""))).strip()
    names_raw = raw_config.get("non_applicant_names")
    if names_raw is not None:
        if isinstance(names_raw, str):
            names = [line.strip() for line in re.split(r"[\r\n]+", names_raw) if line.strip()]
        elif isinstance(names_raw, (list, tuple)):
            names = [
                str(item).strip()
                for item in names_raw
                if item is not None and str(item).strip()
            ]
        else:
            return None, "booking.applicant.non_applicant_names 必须是字符串或数组"

        if len(names) == 1:
            non_applicant_1 = names[0]
            non_applicant_2 = ""
        elif len(names) >= 2:
            split_index = (len(names) + 1) // 2
            non_applicant_1 = "\n".join(names[:split_index])
            non_applicant_2 = "\n".join(names[split_index:])
        else:
            non_applicant_1 = ""
            non_applicant_2 = ""

    return (
        ApplicantConfig(
            last_name=str(raw_config.get("last_name", "")).strip(),
            first_name=str(raw_config.get("first_name", "")).strip(),
            dob_day=dob_day,
            dob_month=dob_month,
            dob_year=dob_year,
            telephone=str(raw_config.get("telephone", "")).strip(),
            email=str(raw_config.get("email", "")).strip(),
            citizenship=str(raw_config.get("citizenship", "")).strip().upper(),
            birth_country=str(raw_config.get("birth_country", "")).strip().upper(),
            sex=sex_raw,
            passport_number=str(raw_config.get("passport_number", "")).strip(),
            non_applicant_1=non_applicant_1,
            non_applicant_2=non_applicant_2,
        ),
        None,
    )


def parse_booking_config(raw_config: Any) -> BookingConfig:
    config = raw_config if isinstance(raw_config, dict) else {}
    applicant, applicant_error = parse_applicant_config(config.get("applicant", {}))

    return BookingConfig(
        enabled=coerce_bool(config.get("enabled"), default=False),
        date_selection=parse_date_selection_config(config.get("date_selection", {})),
        time_selection=parse_time_selection_config(config.get("time_selection", {})),
        bubble=parse_bubble_config(config.get("bubble", {})),
        applicant=applicant,
        applicant_error=applicant_error,
        artifacts_dir=BOOKING_ARTIFACTS_DIR,
    )


def cookie_header_to_playwright_cookies(cookie_header: str) -> List[Dict[str, str]]:
    cookies: List[Dict[str, str]] = []
    for cookie_pair in cookie_header.split(";"):
        cookie_pair = cookie_pair.strip()
        if "=" not in cookie_pair:
            continue
        name, value = cookie_pair.split("=", 1)
        name = name.strip()
        value = value.strip()
        if not name:
            continue
        cookies.append(
            {
                "name": name,
                "value": value,
                "url": BASE_ACS_URL,
            }
        )
    return cookies


def parse_runtime_config_values(config: Dict[str, Any]) -> RuntimeConfigValues:
    months = resolve_months_from_config(config)
    booking_raw = config.get("booking", {})
    if booking_raw is None:
        booking_raw = {}
    if not isinstance(booking_raw, dict):
        raise RuntimeError("config.json 中的 booking 必须是对象")
    for field_name in ("date_selection", "time_selection", "applicant", "bubble"):
        if field_name in booking_raw and booking_raw[field_name] is not None and not isinstance(
            booking_raw[field_name], dict
        ):
            raise RuntimeError(f"booking.{field_name} 必须是对象")

    interval_minutes = int(config.get("interval_minutes", DEFAULT_INTERVAL_MINUTES))
    if interval_minutes < 0:
        raise RuntimeError("config.json 中的 interval_minutes 不能小于 0")

    timeout_seconds = int(config.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS))
    if timeout_seconds <= 0:
        raise RuntimeError("config.json 中的 timeout_seconds 必须大于 0")

    check_once_max_seconds = int(
        config.get("check_once_max_seconds", DEFAULT_CHECK_ONCE_MAX_SECONDS)
    )
    if check_once_max_seconds <= 0:
        raise RuntimeError("config.json 中的 check_once_max_seconds 必须大于 0")

    action_delay_ms = DEFAULT_ACTION_DELAY_MS

    calendar_request_delay_seconds = DEFAULT_CALENDAR_REQUEST_DELAY_SECONDS

    city_raw = config.get("city")
    if city_raw is None or not str(city_raw).strip():
        raise RuntimeError("config.json 需要配置 city")
    city_value = normalize_city_value(str(city_raw))
    if not city_value:
        raise RuntimeError("config.json 需要配置 city")

    service_index_raw = config.get("service_index")
    service_index = int(service_index_raw) if service_index_raw is not None else None

    service_indexs_raw = config.get("service_indexs")
    service_indexs: Tuple[int, ...] = ()
    if service_indexs_raw is not None:
        if not isinstance(service_indexs_raw, list):
            raise RuntimeError("config.json 中的 service_indexs 必须是数组")
        parsed_service_indexs: List[int] = []
        for raw_item in service_indexs_raw:
            index_value = int(raw_item)
            if index_value <= 0:
                raise RuntimeError("config.json 中的 service_indexs 元素必须大于 0")
            parsed_service_indexs.append(index_value)
        service_indexs = tuple(parsed_service_indexs)

    if service_index is not None and service_indexs:
        raise RuntimeError("config.json 中 service_index 和 service_indexs 不能同时配置")
    if service_index is None and not service_indexs:
        raise RuntimeError("config.json 需要配置 service_index 或 service_indexs")
    if service_index is not None and service_index <= 0:
        raise RuntimeError("config.json 中的 service_index 必须大于 0")

    booking_config = parse_booking_config(booking_raw)
    if (
        booking_config.bubble.enabled
        and booking_config.date_selection.filter_mode not in {"none", "weight"}
    ):
        raise RuntimeError(
            "booking.bubble.enabled 为 true 时, "
            "booking.date_selection.filter_mode 只能是 none 或 weight"
        )
    if booking_config.enabled and booking_config.applicant_error:
        raise BookingConfigError(booking_config.applicant_error)

    return RuntimeConfigValues(
        months=months,
        interval_minutes=interval_minutes,
        timeout_seconds=timeout_seconds,
        check_once_max_seconds=check_once_max_seconds,
        action_delay_ms=action_delay_ms,
        calendar_request_delay_seconds=calendar_request_delay_seconds,
        browser_channel="chrome",
        city_value=city_value,
        service_index=service_index,
        service_indexs=service_indexs,
        booking_config=booking_config,
        show_browser=coerce_bool(config.get("show_browser"), default=False),
        user_agent=DEFAULT_USER_AGENT,
    )


class PassportAppointmentScraper:
    def __init__(
        self,
        location: Location,
        months: Sequence[str],
        interval_minutes: int,
        service_index: Optional[int],
        service_indexs: Sequence[int],
        headless: bool,
        timeout_seconds: int,
        check_once_max_seconds: int,
        action_delay_ms: int,
        calendar_request_delay_seconds: float,
        browser_channel: Optional[str],
        booking_config: BookingConfig,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        self.location = location
        self.months = tuple(months)
        self._resolved_target_months: Tuple[MonthTarget, ...] = ()
        self.interval_minutes = interval_minutes
        self.service_index = service_index
        self.service_indexs = tuple(service_indexs)
        self.headless = headless
        self.timeout_seconds = timeout_seconds
        self.check_once_max_seconds = check_once_max_seconds
        self.action_delay_ms = action_delay_ms
        self.calendar_request_delay_seconds = calendar_request_delay_seconds
        self.browser_channel = browser_channel
        self.booking = booking_config
        self.user_agent = user_agent
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._cached_calendar_year: Optional[int] = None
        self._cached_calendar_month: Optional[int] = None
        self._cached_service_labels: Tuple[str, ...] = ()
        self._cached_selected_service_label: Optional[str] = None
        self._cached_cookie_header: Optional[str] = None
        self._cached_csrf_token: Optional[str] = None
        self._cached_appointment_type: Optional[str] = None
        self._cached_service_type: Optional[str] = None
        self._cached_citizenship_options: Tuple[str, ...] = ()
        self._cached_birth_country_options: Tuple[str, ...] = ()
        self.current_appointment_date: Optional[dt.date] = None
        self.current_appointment_password: str = ""
        self.bubble_password_checked: bool = False
        if not self.booking.bubble.password:
            self.bubble_password_checked = True
        self._last_logged_page_state: Optional[PageState] = None
        self._last_detected_page_key: Optional[Tuple[PageState, str]] = None
        self._page_state_entered_at: Optional[float] = None
        self._check_once_started_at: Optional[float] = None
        self._check_once_deadline_at: Optional[float] = None
        self.page_state_timeout_seconds = max(
            DEFAULT_TIMEOUT_SECONDS,
            self.timeout_seconds,
        )

    def default_calendar_url(
        self,
        request_context: CalendarRequestContext,
        target_month: MonthTarget,
    ) -> str:
        query = urlencode(
            {
                "CSRFToken": request_context.csrf_token,
                "nMonth": target_month.month,
                "nYear": target_month.year,
                "type": request_context.appointment_type,
                "servicetype": request_context.service_type,
                "pc": self.location.post_code,
            }
        )
        return urljoin(BASE_ACS_URL, f"make_calendar.asp?{query}")

    def service_page_url(self, csrf_token: str) -> str:
        return urljoin(
            BASE_ACS_URL,
            f"make_default.asp?pc={self.location.post_code}&CSRFToken={csrf_token}",
        )

    def update_display_name(self, page_html: str) -> None:
        self.location.display_name = extract_display_name(
            page_html=page_html,
            fallback_city=self.location.city,
        )

    def current_cached_service_label(self) -> Optional[str]:
        if self.service_index is not None and self._cached_service_labels:
            index = self.service_index - 1
            if 0 <= index < len(self._cached_service_labels):
                label = self._cached_service_labels[index]
                if label:
                    return label
        if self.service_indexs and self._cached_service_labels:
            labels = [
                self._cached_service_labels[index - 1]
                for index in self.service_indexs
                if 1 <= index <= len(self._cached_service_labels)
                and self._cached_service_labels[index - 1]
            ]
            if labels:
                return ", ".join(labels)
        return self._cached_selected_service_label

    def cache_service_labels(self, labels: Sequence[str]) -> None:
        normalized = tuple(normalize_whitespace(label) if label else "" for label in labels)
        if not any(normalized):
            return
        self._cached_service_labels = normalized

        current_label = self.current_cached_service_label()
        if current_label:
            self._cached_selected_service_label = current_label

    def get_service_selection_inputs(self, page: Page) -> Any:
        service_inputs = page.locator("input[name='chkservice'], input[name='chkservicespec']")
        if service_inputs.count() > 0:
            return service_inputs
        return page.locator("input[type='radio'], input[type='checkbox']")

    def merge_request_context_with_cache(
        self,
        request_context: CalendarRequestContext,
    ) -> CalendarRequestContext:
        calendar_year = request_context.calendar_year
        calendar_month = request_context.calendar_month
        if calendar_year is None or calendar_month is None:
            calendar_year = self._cached_calendar_year if calendar_year is None else calendar_year
            calendar_month = self._cached_calendar_month if calendar_month is None else calendar_month

        service_label = request_context.service_label or self.current_cached_service_label()

        merged_context = CalendarRequestContext(
            cookie_header=request_context.cookie_header,
            csrf_token=request_context.csrf_token,
            appointment_type=request_context.appointment_type,
            service_type=request_context.service_type,
            service_label=service_label,
            calendar_year=calendar_year,
            calendar_month=calendar_month,
        )

        if merged_context.calendar_year is not None and merged_context.calendar_month is not None:
            self._cached_calendar_year = merged_context.calendar_year
            self._cached_calendar_month = merged_context.calendar_month
        if merged_context.service_label:
            self._cached_selected_service_label = merged_context.service_label
        self._cached_cookie_header = merged_context.cookie_header
        self._cached_csrf_token = merged_context.csrf_token
        self._cached_appointment_type = merged_context.appointment_type
        self._cached_service_type = merged_context.service_type

        return merged_context

    def current_context_cache_payload(self) -> Dict[str, Any]:
        return {
            "cookie_header": self._cached_cookie_header,
            "csrf_token": self._cached_csrf_token,
            "calendar_year": self._cached_calendar_year,
            "calendar_month": self._cached_calendar_month,
            "service_labels": list(self._cached_service_labels),
            "selected_service_label": self._cached_selected_service_label,
            "appointment_type": self._cached_appointment_type,
            "service_type": self._cached_service_type,
        }

    def current_bubble_state_payload(self) -> Dict[str, Any]:
        return {
            "current_appointment_date": (
                self.current_appointment_date.isoformat()
                if self.current_appointment_date is not None
                else None
            ),
            "current_appointment_password": self.current_appointment_password,
            "bubble_password_checked": self.bubble_password_checked,
        }

    def apply_context_cache_payload(self, payload: Dict[str, Any]) -> None:
        cookie_header = payload.get("cookie_header")
        csrf_token = payload.get("csrf_token")
        if cookie_header:
            self._cached_cookie_header = str(cookie_header)
        if csrf_token:
            self._cached_csrf_token = str(csrf_token)

        calendar_year = parse_optional_int(str(payload.get("calendar_year"))) if payload.get("calendar_year") is not None else None
        calendar_month = parse_optional_int(str(payload.get("calendar_month"))) if payload.get("calendar_month") is not None else None
        if calendar_year is not None:
            self._cached_calendar_year = calendar_year
        if calendar_month is not None:
            self._cached_calendar_month = calendar_month

        raw_labels = payload.get("service_labels")
        if isinstance(raw_labels, list):
            labels = [str(item) for item in raw_labels]
            self.cache_service_labels(labels)

        selected_service_label = payload.get("selected_service_label")
        if selected_service_label:
            self._cached_selected_service_label = str(selected_service_label)

        appointment_type = payload.get("appointment_type")
        service_type = payload.get("service_type")
        if appointment_type:
            self._cached_appointment_type = str(appointment_type)
        if service_type:
            self._cached_service_type = str(service_type)

    def apply_bubble_state_payload(self, payload: Dict[str, Any]) -> None:
        date_raw = payload.get("current_appointment_date")
        if date_raw:
            try:
                self.current_appointment_date = parse_iso_date(str(date_raw))
            except Exception:
                self.current_appointment_date = None
        else:
            self.current_appointment_date = None

        password = payload.get("current_appointment_password")
        self.current_appointment_password = str(password or "")
        self.bubble_password_checked = bool(payload.get("bubble_password_checked", False))

    def current_cached_request_context(self) -> Optional[CalendarRequestContext]:
        if (
            not self._cached_cookie_header
            or not self._cached_csrf_token
            or not self._cached_appointment_type
            or not self._cached_service_type
        ):
            return None

        return CalendarRequestContext(
            cookie_header=self._cached_cookie_header,
            csrf_token=self._cached_csrf_token,
            appointment_type=self._cached_appointment_type,
            service_type=self._cached_service_type,
            service_label=self.current_cached_service_label(),
            calendar_year=self._cached_calendar_year,
            calendar_month=self._cached_calendar_month,
        )

    def clear_cached_request_context(self) -> None:
        self._cached_cookie_header = None
        self._cached_csrf_token = None
        self._cached_appointment_type = None
        self._cached_service_type = None
        self._cached_calendar_year = None
        self._cached_calendar_month = None
        self._cached_selected_service_label = None
        self._cached_service_labels = ()

    def human_pause(
        self,
        minimum_seconds: float = 0.25,
        maximum_seconds: float = 0.75,
    ) -> None:
        if maximum_seconds <= 0:
            return
        minimum = max(0.0, minimum_seconds)
        maximum = max(minimum, maximum_seconds)
        time.sleep(random.uniform(minimum, maximum))

    def launch_browser(self, playwright: Playwright) -> Browser:
        launch_args = ["--disable-blink-features=AutomationControlled"]
        if should_disable_linux_sandbox():
            launch_args.extend(["--no-sandbox", "--disable-dev-shm-usage"])

        launch_kwargs: Dict[str, Any] = {
            "headless": self.headless,
            "args": launch_args,
        }
        if self.action_delay_ms > 0:
            launch_kwargs["slow_mo"] = self.action_delay_ms

        if self.browser_channel and not self.headless:
            try:
                return playwright.chromium.launch(channel=self.browser_channel, **launch_kwargs)
            except Exception as exc:
                print(
                    f"\n浏览器通道 {self.browser_channel} 启动失败, "
                    f"改用 Playwright Chromium\n====\n{exc}"
                )

        return playwright.chromium.launch(**launch_kwargs)

    def describe_page_state(self, state: PageState) -> str:
        labels = {
            PageState.EXPIRED_ID: "过期链接页",
            PageState.BAD_SUBMIT: "错误提交页",
            PageState.BAD_SUBMIT_CHANGE: "错误提交修改页",
            PageState.CANCEL_BOOKING: "取消预约页",
            PageState.CANCEL_SUBMIT: "取消预约提交页",
            PageState.APPOINTMENT_CANCEL_QUERY: "取消预约查询页",
            PageState.APPOINTMENT_DETAIL: "预约详情页",
            PageState.VERIFICATION: "验证码页",
            PageState.APPOINTMENT_SELECTION: "预约选择页",
            PageState.SERVICE_SELECTION_LOADING: "服务选择加载页",
            PageState.SERVICE_SELECTION: "服务选择页",
            PageState.CALENDAR: "日历页",
            PageState.BOOKING_FORM: "预约表单页",
            PageState.RETRY: "重试页",
            PageState.CONFIRMATION: "预约确认页",
            PageState.UNKNOWN: "未定义页面",
        }
        return labels.get(state, state.value)

    def build_service_selection_snapshot(self, page: Page) -> ServiceSelectionSnapshot:
        service_inputs = self.get_service_selection_inputs(page)
        service_count = service_inputs.count()
        regex_labels, regex_selection_mode = extract_service_options_from_html(page.content())
        label_script = """(element) => {
            const row = element.closest('tr');
            const source = row ? row.innerText : (element.parentElement ? element.parentElement.innerText : '');
            return source.replace(/\\s+/g, ' ').trim();
        }"""
        service_labels: List[str] = []
        input_types: List[str] = []
        for index in range(service_count):
            label = ""
            try:
                label = normalize_whitespace(service_inputs.nth(index).evaluate(label_script))
            except Exception:
                label = ""
            input_types.append(
                normalize_whitespace(service_inputs.nth(index).get_attribute("type") or "").lower()
            )
            if not label and index < len(regex_labels):
                label = regex_labels[index]
            if not label and index < len(self._cached_service_labels):
                label = self._cached_service_labels[index]
            service_labels.append(label or f"Service {index + 1}")
        if not service_labels and regex_labels:
            service_labels = list(regex_labels)
        if service_labels:
            self.cache_service_labels(service_labels)
        selection_mode = "checkbox" if any(input_type == "checkbox" for input_type in input_types) else regex_selection_mode
        return ServiceSelectionSnapshot(
            service_inputs=service_inputs,
            service_labels=tuple(service_labels),
            selection_mode=selection_mode,
        )

    def print_available_services(self, page: Page) -> None:
        service_snapshot = self.build_service_selection_snapshot(page)
        service_labels = service_snapshot.service_labels
        if not service_labels:
            print("\n当前页未解析到可用服务")
            return

        print("\n当前页可用服务:")
        for index, label in enumerate(service_labels, start=1):
            if service_snapshot.selection_mode == "checkbox":
                current_marker = " [当前使用]" if index in self.service_indexs else ""
            else:
                current_marker = " [当前使用]" if self.service_index == index else ""
            print(f"{index}. {label}{current_marker}")

        if service_snapshot.selection_mode == "checkbox":
            if not self.service_indexs:
                print("当前使用的服务: 未配置 service_indexs")
            else:
                selected_labels = [
                    f"{index}. {service_labels[index - 1]}"
                    for index in self.service_indexs
                    if 1 <= index <= service_snapshot.input_count
                ]
                if selected_labels:
                    print(f"当前使用的服务: {', '.join(selected_labels)}")
                else:
                    print(f"当前使用的服务: service_indexs={list(self.service_indexs)} 超出范围")
        elif self.service_index is None:
            print("当前使用的服务: 未配置 service_index")
        elif 1 <= self.service_index <= service_snapshot.input_count:
            print(f"当前使用的服务: {self.service_index}. {service_labels[self.service_index - 1]}")
        else:
            print(f"当前使用的服务: service_index={self.service_index} 超出范围")

    def log_page_state_if_changed(self, page: Page, snapshot: PageSnapshot) -> None:
        if snapshot.state == self._last_logged_page_state:
            return
        self._last_logged_page_state = snapshot.state
        print(f"\n当前页面: {self.describe_page_state(snapshot.state)}")
        print(f"URL: {snapshot.url}")
        if snapshot.state == PageState.SERVICE_SELECTION:
            self.print_available_services(page)

    def begin_check_once_window(self) -> None:
        started_at = time.monotonic()
        self._check_once_started_at = started_at
        self._check_once_deadline_at = started_at + self.check_once_max_seconds

    def end_check_once_window(self) -> None:
        self._check_once_started_at = None
        self._check_once_deadline_at = None
        self._last_detected_page_key = None
        self._page_state_entered_at = None

    def ensure_check_once_within_timeout(self) -> None:
        if self._check_once_deadline_at is None:
            return
        remaining = self._check_once_deadline_at - time.monotonic()
        if remaining <= 0:
            raise RuntimeError(
                f"check_once 超过最大停留时间 {self.check_once_max_seconds} 秒"
            )

    def ensure_page_within_timeout(self, snapshot: PageSnapshot) -> None:
        page_key = (snapshot.state, snapshot.url)
        now = time.monotonic()
        if page_key != self._last_detected_page_key:
            self._last_detected_page_key = page_key
            self._page_state_entered_at = now
            return

        if self._page_state_entered_at is None:
            self._page_state_entered_at = now
            return

        elapsed = now - self._page_state_entered_at
        page_state_timeout_seconds = self.page_state_timeout_seconds
        if snapshot.state in {PageState.VERIFICATION, PageState.RETRY}:
            page_state_timeout_seconds = max(page_state_timeout_seconds, self.timeout_seconds * 3)

        if elapsed > page_state_timeout_seconds:
            raise RuntimeError(
                f"{self.describe_page_state(snapshot.state)} 停留超过 "
                f"page_state_timeout_seconds={page_state_timeout_seconds} 秒"
            )

    def ensure_browser_session(self) -> Tuple[BrowserContext, Page]:
        if self._playwright is None:
            self._playwright = sync_playwright().start()
        if self._browser is None:
            self._browser = self.launch_browser(self._playwright)
        if self._context is None:
            self._context = self._browser.new_context(
                user_agent=self.user_agent,
                locale="en-US",
                viewport={"width": 1366, "height": 768},
                extra_http_headers=windows_like_http_headers(),
            )
        if self._page is None or self._page.is_closed():
            self._page = self._context.new_page()
            apply_windows_ua_overrides(self._context, self._page, self.user_agent)
            STEALTH.apply_stealth_sync(self._page)
        return self._context, self._page

    def close_browser_session(self) -> None:
        if self._context is not None:
            try:
                self._context.close()
            except Exception:
                pass
            self._context = None
            self._page = None

        if self._browser is not None:
            try:
                self._browser.close()
            except Exception:
                pass
            self._browser = None

        if self._playwright is not None:
            try:
                self._playwright.stop()
            except Exception:
                pass
            self._playwright = None
        self._last_logged_page_state = None

    def close_current_page(self) -> None:
        if self._page is None:
            return
        try:
            if not self._page.is_closed():
                self._page.close()
        except Exception:
            pass
        self._page = None
        self._last_logged_page_state = None
        self._last_detected_page_key = None
        self._page_state_entered_at = None

    def reset_browser_session_for_recovery(self) -> None:
        self.close_current_page()
        self.close_browser_session()

    def resolve_target_months(
        self,
        request_context: CalendarRequestContext,
    ) -> Tuple[MonthTarget, ...]:
        resolved: List[MonthTarget] = []
        warned_using_cached_month = False

        for month_value in self.months:
            base_year = request_context.calendar_year
            base_month = request_context.calendar_month
            if base_year is None or base_month is None:
                if self._cached_calendar_year is not None and self._cached_calendar_month is not None:
                    base_year = self._cached_calendar_year
                    base_month = self._cached_calendar_month
                    if not warned_using_cached_month:
                        print("\n警告\n====\n基准年月解析失败, 已沿用缓存值")
                        warned_using_cached_month = True
                else:
                    raise RuntimeError("months 中使用 +N 时, 当前流程无法解析基准年月")

            offset = int(month_value[1:])
            resolved.append(
                add_month_offset(
                    base_year=base_year,
                    base_month=base_month,
                    offset=offset,
                )
            )

        self._resolved_target_months = tuple(resolved)
        return self._resolved_target_months

    def _resolve_with_browser(self) -> CalendarRequestContext:
        context, page = self.ensure_browser_session()
        page.goto(
            urljoin(
                BASE_ACS_URL,
                f"default.asp?appcode=1&postcode={self.location.post_code}",
            ),
            wait_until="networkidle",
            timeout=self.timeout_seconds * 1000,
        )
        for _ in range(10):
            snapshot = self.detect_page_snapshot(page)
            if snapshot.state != PageState.VERIFICATION:
                break
            if self.handle_verification_page(page) == "retry":
                raise RuntimeError("verification page retries exceeded while bootstrapping session")
        else:
            raise RuntimeError("page state machine exceeded transitions while bootstrapping session")
        page_html = page.content()
        self.update_display_name(page_html)
        csrf_token = extract_csrf_token(page_html)

        if self.service_index is None and not self.service_indexs:
            raise RuntimeError("config.json 需要设置 service_index 或 service_indexs")

        return self._resolve_service_selection_in_browser(
            page=page,
            context=context,
            make_appointment_url=self.service_page_url(csrf_token),
        )

    def get_page_body_text(self, page: Page) -> str:
        return normalize_whitespace(page.locator("body").inner_text())

    def is_verification_body_text(self, body_text_lower: str) -> bool:
        return "type the characters as they appear in the picture" in body_text_lower or "what code is in the image" in body_text_lower

    def has_inline_verification_prompt_text(self, body_text_lower: str) -> bool:
        return "retype the code from the picture" in body_text_lower

    def is_retry_text(self, body_text_lower: str) -> bool:
        return "please go back and retry" in body_text_lower

    def is_existing_appointment_cancel_text(self, body_text_lower: str) -> bool:
        return "it appears that you already have an appointment scheduled" in body_text_lower

    def is_bubble_enabled(self) -> bool:
        return (
            self.booking.enabled
            and self.booking.bubble.enabled
            and self.booking.date_selection.filter_mode in {"none", "weight"}
        )

    def cancel_query_url(self, csrf_token: str) -> str:
        query = urlencode(
            {
                "pc": self.location.post_code,
                "CSRFToken": csrf_token,
            }
        )
        return urljoin(BASE_ACS_URL, f"make_cancel_main.asp?{query}")

    def appointment_selection_url(self) -> str:
        return urljoin(
            BASE_ACS_URL,
            f"default.asp?appcode=1&postcode={self.location.post_code}",
        )

    def extract_page_csrf_token(self, page: Page) -> str:
        query = parse_qs(urlparse(page.url).query)
        csrf_token = first_query_value(query, "CSRFToken")
        if csrf_token:
            return csrf_token
        return extract_csrf_token(page.content())

    def resolve_verification_pages(self, page: Page, context_label: str) -> PageSnapshot:
        for _ in range(10):
            snapshot = self.detect_page_snapshot(page)
            if snapshot.state != PageState.VERIFICATION:
                return snapshot
            if self.handle_verification_page(page) == "retry":
                raise RuntimeError(f"verification page retries exceeded while {context_label}")
        raise RuntimeError(f"page state machine exceeded transitions while {context_label}")

    def has_cancel_query_form_fields(self, page: Page) -> bool:
        if page.locator("input[name='lastName1'], input[name='FirstName1'], input[name='Telephone1'], input[name='Password1']").count() > 0:
            return True
        visible_text_input_count = 0
        inputs = page.locator("input")
        for input_index in range(inputs.count()):
            input_box = inputs.nth(input_index)
            input_type = normalize_whitespace(input_box.get_attribute("type") or "text").lower()
            if input_type not in {"", "text", "password", "tel"}:
                continue
            try:
                if input_box.is_visible() and input_box.is_enabled():
                    visible_text_input_count += 1
            except Exception:
                continue
        return visible_text_input_count >= 4

    def wait_for_cancel_query_form(self, page: Page) -> None:
        deadline = time.monotonic() + max(8, self.timeout_seconds)
        while time.monotonic() < deadline:
            snapshot = self.resolve_verification_pages(page, "waiting for cancel query form")
            if snapshot.state in {PageState.BAD_SUBMIT, PageState.BAD_SUBMIT_CHANGE}:
                return
            if self.has_cancel_query_form_fields(page):
                return
            page.wait_for_timeout(500)

        try:
            body_preview = self.extract_body_preview(page.locator("body").inner_text(), limit=500)
        except Exception:
            body_preview = ""
        input_names = []
        inputs = page.locator("input")
        for input_index in range(inputs.count()):
            input_names.append(inputs.nth(input_index).get_attribute("name") or "")
        raise RuntimeError(
            "取消预约查询页表单未加载完成或被异常页面替代; "
            f"URL: {page.url}; input name: {input_names}; 页面内容预览: {body_preview}"
        )

    def open_cancel_query_page(self, page: Page) -> None:
        if self._cached_csrf_token:
            page.goto(
                self.cancel_query_url(self._cached_csrf_token),
                wait_until="networkidle",
                timeout=self.timeout_seconds * 1000,
            )
            self.resolve_verification_pages(page, "opening cancel query page")
            self.wait_for_cancel_query_form(page)
            return

        page.goto(
            self.appointment_selection_url(),
            wait_until="networkidle",
            timeout=self.timeout_seconds * 1000,
        )
        self.resolve_verification_pages(page, "opening appointment selection page")

        csrf_token = self.extract_page_csrf_token(page)
        self._cached_csrf_token = csrf_token
        cancel_button = page.locator(
            "input[value='Cancel Appointment!'], button:has-text('Cancel Appointment!')"
        ).first
        if cancel_button.count() > 0:
            try:
                with page.expect_navigation(
                    wait_until="networkidle",
                    timeout=self.timeout_seconds * 1000,
                ):
                    cancel_button.click()
                self.resolve_verification_pages(page, "opening cancel query page")
                self.wait_for_cancel_query_form(page)
                return
            except Exception:
                pass

        page.goto(
            self.cancel_query_url(csrf_token),
            wait_until="networkidle",
            timeout=self.timeout_seconds * 1000,
        )
        self.resolve_verification_pages(page, "opening cancel query page")
        self.wait_for_cancel_query_form(page)

    def fill_cancel_query_form(self, page: Page, password: str) -> None:
        applicant = self.booking.applicant
        if applicant is None:
            raise BookingConfigError("booking.applicant 不完整")

        fields = (
            (("lastName1", "LastName1", "lastName", "LastName"), applicant.last_name),
            (("FirstName1", "firstName1", "FirstName", "firstName"), applicant.first_name),
            (("Telephone1", "telephone1", "Telephone", "telephone"), applicant.telephone),
            (("Password1", "password1", "Password", "password"), password),
        )
        missing_indexes: List[int] = []
        for index, (name_candidates, value) in enumerate(fields):
            control = None
            for name in name_candidates:
                candidate = page.locator(f"input[name='{name}']").first
                if candidate.count() > 0:
                    control = candidate
                    break
            if control is None:
                missing_indexes.append(index)
                continue
            control.fill(value)

        if not missing_indexes:
            return

        visible_text_inputs: List[Any] = []
        inputs = page.locator("input")
        for input_index in range(inputs.count()):
            input_box = inputs.nth(input_index)
            input_type = normalize_whitespace(input_box.get_attribute("type") or "text").lower()
            if input_type not in {"", "text", "password", "tel"}:
                continue
            try:
                if input_box.is_visible() and input_box.is_enabled():
                    visible_text_inputs.append(input_box)
            except Exception:
                continue

        if len(visible_text_inputs) >= 4:
            values = (
                applicant.last_name,
                applicant.first_name,
                applicant.telephone,
                password,
            )
            for input_index, value in enumerate(values):
                visible_text_inputs[input_index].fill(value)
            return

        field_names = [
            inputs.nth(input_index).get_attribute("name") or ""
            for input_index in range(inputs.count())
        ]
        raise RuntimeError(
            "取消预约查询页缺少可识别的姓名/电话/password 字段; "
            f"当前 input name: {field_names}"
        )

    def submit_cancel_query_form(self, page: Page) -> None:
        submit_button = page.locator(
            "input[type='submit'][value='Submit'], button:has-text('Submit')"
        ).first
        if submit_button.count() == 0:
            raise RuntimeError("取消预约查询页缺少 Submit 按钮")
        self.human_pause(0.2, 0.6)
        with page.expect_navigation(
            wait_until="networkidle",
            timeout=self.timeout_seconds * 1000,
        ):
            submit_button.click()
        self.resolve_verification_pages(page, "submitting cancel query form")

    def print_unknown_bubble_page(self, page: Page, title: str) -> None:
        try:
            body_preview = self.extract_body_preview(page.locator("body").inner_text(), limit=500)
        except Exception:
            body_preview = ""
        print(f"\n{title}")
        print(f"URL: {page.url}")
        if body_preview:
            print(f"页面内容预览: {body_preview}")

    def check_bubble_password_appointment(self) -> None:
        if not self.is_bubble_enabled():
            return
        password = self.booking.bubble.password
        if not password:
            self.bubble_password_checked = True
            return

        print("\nBubble: 检测 booking.bubble.password 对应的预约")
        context, page = self.ensure_browser_session()
        try:
            self.open_cancel_query_page(page)
            self.fill_cancel_query_form(page, password)
            self.submit_cancel_query_form(page)
            snapshot = self.detect_page_snapshot(page)

            if snapshot.state == PageState.APPOINTMENT_DETAIL:
                details = self.extract_confirmation_details(page)
                appointment_date = self.appointment_date_from_details(details)
                if appointment_date is not None:
                    self.current_appointment_date = appointment_date
                    self.current_appointment_password = password
                    self.bubble_password_checked = True
                    print(f"\nBubble: 已确认当前预约日期 {appointment_date.isoformat()}")
                    return

                self.print_unknown_bubble_page(page, "Bubble: 预约详情页未解析到 Appointment Date")
                return

            if snapshot.state == PageState.BAD_SUBMIT_CHANGE:
                self.current_appointment_date = None
                self.current_appointment_password = ""
                self.bubble_password_checked = True
                print("\nBubble: booking.bubble.password 查询无效, 当前预约状态已清空")
                return

            self.print_unknown_bubble_page(page, "Bubble: booking.bubble.password 查询结果未知")
        except BookingConfigError:
            raise
        except Exception as exc:
            print(f"\nBubble: booking.bubble.password 查询失败, 保持未确认状态\n====\n{exc}")
        finally:
            self.close_current_page()

    def submit_cancel_appointment_from_detail(self, page: Page) -> None:
        cancel_button = page.locator(
            "input[type='submit'][value='Cancel Appointment'], button:has-text('Cancel Appointment')"
        ).first
        if cancel_button.count() == 0:
            raise RuntimeError("预约详情页缺少 Cancel Appointment 按钮")
        self.human_pause(0.2, 0.6)
        try:
            with page.expect_navigation(
                wait_until="networkidle",
                timeout=self.timeout_seconds * 1000,
            ):
                cancel_button.click()
            self.resolve_verification_pages(page, "submitting cancel appointment")
        except PlaywrightTimeoutError:
            page.wait_for_timeout(800)
            self.resolve_verification_pages(page, "submitting cancel appointment")

    def cancel_current_appointment(self, password: Optional[str] = None) -> None:
        password_to_use = str(password or self.current_appointment_password or "").strip()
        if not password_to_use:
            return

        print("\nBubble: 尝试取消当前预约")
        context, page = self.ensure_browser_session()
        try:
            self.open_cancel_query_page(page)
            self.fill_cancel_query_form(page, password_to_use)
            self.submit_cancel_query_form(page)
            snapshot = self.detect_page_snapshot(page)
            if snapshot.state == PageState.APPOINTMENT_DETAIL:
                self.submit_cancel_appointment_from_detail(page)
                print("\nBubble: 已提交取消预约请求")
                return
            self.print_unknown_bubble_page(page, "Bubble: 取消预约查询未进入预约详情页")
        except Exception as exc:
            print(f"\nBubble: 取消预约流程失败, 将继续后续预约流程\n====\n{exc}")
        finally:
            self.close_current_page()

    def has_calendar_controls(self, page: Page) -> bool:
        selectors = (
            "input[name='nMonth']",
            "input[name='nYear']",
            "select[name='nMonth']",
            "select[name='nYear']",
            "a[href*='make_default_day.asp']",
            "a[href*='make_calendar.asp']",
        )
        for selector in selectors:
            if page.locator(selector).count() > 0:
                return True
        return False

    def has_verification_controls(self, page: Page) -> bool:
        if self.find_verification_input_box(page) is None:
            return False
        if page.locator("img").count() == 0:
            return False
        return page.locator(
            "input[type='submit'], button[type='submit'], input[type='button'], button"
        ).count() > 0

    def is_service_selection_url(self, url_lower: str) -> bool:
        return (
            "make_default.asp" in url_lower
            and f"pc={self.location.post_code.lower()}" in url_lower
            and "csrftoken=" in url_lower
        )

    def wait_for_service_selection_options(self, page: Page) -> None:
        deadline = time.monotonic() + max(3, self.timeout_seconds)
        while time.monotonic() < deadline:
            if self.get_service_selection_inputs(page).count() > 0:
                return
            if self.has_verification_controls(page):
                return
            if self.has_calendar_controls(page):
                return
            page.wait_for_timeout(500)

    def refresh_request_context_from_calendar_page(self, page: Page) -> None:
        page_html = page.content()
        try:
            cookie_header = ""
            if self._context is not None:
                cookie_header = "; ".join(
                    f"{cookie['name']}={cookie['value']}" for cookie in self._context.cookies()
                )
            request_context = extract_calendar_request_context(
                current_url=page.url,
                cookie_header=cookie_header,
                fallback_html=page_html,
                fallback_service_label=self.current_cached_service_label(),
            )
            self.merge_request_context_with_cache(request_context)
        except Exception:
            calendar_year, calendar_month = extract_calendar_year_month_from_html(page_html)
            if calendar_year is None or calendar_month is None:
                query = parse_qs(urlparse(page.url).query)
                calendar_year = parse_optional_int(first_query_value(query, "nYear"))
                calendar_month = parse_optional_int(first_query_value(query, "nMonth"))

            if calendar_year is not None and calendar_month is not None and 1 <= calendar_month <= 12:
                self._cached_calendar_year = calendar_year
                self._cached_calendar_month = calendar_month

    def detect_page_snapshot(self, page: Page) -> PageSnapshot:
        body_text = self.get_page_body_text(page)
        body_text_lower = body_text.lower()
        url = page.url
        url_lower = url.lower()

        has_booking_form = (
            page.locator("input[name='availTimeSlot']").count() > 0
            and page.locator("input[name='txtLastName']").count() > 0
        )
        has_retry_controls = (
            page.locator("input[type='button'][value='Back']").count() > 0
            or page.locator("a:has-text('Back')").count() > 0
        )
        service_selection_inputs = self.get_service_selection_inputs(page)
        has_service_selection = (
            not has_booking_form
            and page.locator("input[name='txtLastName']").count() == 0
            and page.locator("input[name='availTimeSlot']").count() == 0
            and service_selection_inputs.count() > 0
            and page.locator("input[type='submit'], button[type='submit']").count() > 0
        )
        has_expired_id_prompt = is_expired_id_page_text(body_text_lower)
        has_calendar_controls = self.has_calendar_controls(page)
        has_verification_controls = self.has_verification_controls(page)
        has_badsubmit_controls = "badsubmit.asp" in url_lower
        has_badsubmitchange_controls = "badsubmitchange.asp" in url_lower
        has_cancel_booking_controls = "make_submit_cancel.asp" in url_lower

        has_verification_prompt = self.is_verification_body_text(body_text_lower) or (
            "make_check_validate.asp" in url_lower and has_verification_controls
        )

        if self.is_retry_text(body_text_lower) and has_retry_controls:
            state = PageState.RETRY
        elif has_verification_prompt:
            state = PageState.VERIFICATION
        elif "make_cancel_detail.asp" in url_lower:
            state = PageState.APPOINTMENT_DETAIL
        elif "make_cancel_main.asp" in url_lower:
            state = PageState.APPOINTMENT_CANCEL_QUERY
        elif "make_cancel_submit.asp" in url_lower:
            state = PageState.CANCEL_SUBMIT
        elif "appointment uid:" in body_text_lower and "appointment password:" in body_text_lower:
            state = PageState.CONFIRMATION
        elif has_booking_form:
            state = PageState.BOOKING_FORM
        elif "default.asp" in url_lower and "postcode=" in url_lower:
            state = PageState.APPOINTMENT_SELECTION
        elif "make_calendar.asp" in url_lower or has_calendar_controls:
            state = PageState.CALENDAR
        elif has_service_selection:
            state = PageState.SERVICE_SELECTION
        elif self.is_service_selection_url(url_lower):
            state = PageState.SERVICE_SELECTION_LOADING
        elif has_cancel_booking_controls:
            state = PageState.CANCEL_BOOKING
        elif has_badsubmit_controls:
            state = PageState.BAD_SUBMIT
        elif has_badsubmitchange_controls:
            state = PageState.BAD_SUBMIT_CHANGE
        elif has_expired_id_prompt:
            state = PageState.EXPIRED_ID
        else:
            state = PageState.UNKNOWN

        snapshot = PageSnapshot(
            state=state,
            url=url,
            body_text=body_text,
            has_inline_verification_prompt=self.has_inline_verification_prompt_text(body_text_lower),
        )
        if snapshot.state == PageState.CALENDAR:
            self.refresh_request_context_from_calendar_page(page)
        self.ensure_check_once_within_timeout()
        self.ensure_page_within_timeout(snapshot)
        self.log_page_state_if_changed(page, snapshot)
        return snapshot

    def find_verification_input_box(self, page: Page) -> Optional[Dict[str, float]]:
        inputs = page.locator("input")
        for index in range(inputs.count()):
            input_box = inputs.nth(index)
            input_type = (input_box.get_attribute("type") or "text").strip().lower()
            if input_type in {"hidden", "submit", "button", "checkbox", "radio", "image", "reset"}:
                continue

            try:
                if input_box.is_visible() and input_box.is_enabled():
                    return input_box.bounding_box()
            except Exception:
                continue

        return None

    def choose_verification_image(self, page: Page):
        input_box = self.find_verification_input_box(page)
        images = page.locator("img")
        best_image = None
        best_score = None

        for index in range(images.count()):
            image = images.nth(index)
            try:
                if not image.is_visible():
                    continue
                box = image.bounding_box()
                if not box:
                    continue
            except Exception:
                continue

            width = box["width"]
            height = box["height"]
            alt = (image.get_attribute("alt") or "").lower()
            title = (image.get_attribute("title") or "").lower()

            if alt in {"red dot", "captcha"} or title in {"red dot", "captcha"}:
                best_image = image
                break

            if any(keyword in alt for keyword in {"refresh", "reload", "rotate", "speak"}) or any(keyword in title for keyword in {"refresh", "reload", "rotate", "speak"}):
                continue

            if width > 700 or height > 200 or width < 50 or height < 20:
                continue

            aspect_ratio = width / max(height, 1)
            if aspect_ratio < 1.3:
                continue

            score = width * height
            if input_box is not None:
                center_x = box["x"] + width / 2
                center_y = box["y"] + height / 2
                input_center_x = input_box["x"] + input_box["width"] / 2
                input_center_y = input_box["y"] + input_box["height"] / 2
                distance = abs(center_x - input_center_x) + abs(center_y - input_center_y)
                score -= distance * 5

            if best_score is None or score > best_score:
                best_image = image
                best_score = score

        return best_image

    def fill_verification_text(self, page: Page, verification_text: str) -> None:
        inputs = page.locator("input")
        candidates = []
        for index in range(inputs.count()):
            input_box = inputs.nth(index)
            input_type = (input_box.get_attribute("type") or "text").strip().lower()
            if input_type in {"hidden", "submit", "button", "checkbox", "radio", "image", "reset"}:
                continue

            try:
                if input_box.is_visible() and input_box.is_enabled():
                    candidates.append(input_box)
            except Exception:
                continue

        if candidates:
            captcha_input = candidates[-1]
            captcha_input.click()
            captcha_input.fill("")
            if verification_text:
                captcha_input.type(verification_text, delay=max(35, self.action_delay_ms))
            return

        raise RuntimeError("未找到验证码输入框")

    def submit_verification_page(self, page: Page) -> None:
        submit_button = page.locator(
            "input[type='submit'], button[type='submit'], input[type='button'], button"
        )
        for index in range(submit_button.count()):
            button = submit_button.nth(index)
            try:
                if button.is_visible() and button.is_enabled():
                    self.human_pause(0.2, 0.6)
                    with page.expect_navigation(
                        wait_until="networkidle",
                        timeout=self.timeout_seconds * 1000,
                    ):
                        button.click()
                    return
            except Exception:
                continue

        raise RuntimeError("未找到验证码提交按钮")

    def solve_verification_challenge(self, page: Page) -> None:
        chosen_image = self.choose_verification_image(page)
        if chosen_image is not None:
            image_bytes = chosen_image.screenshot()
        else:
            image_bytes = page.screenshot(full_page=True)
        verification_text = solve_verification_image(image_bytes)
        self.fill_verification_text(page, verification_text)

    def handle_verification_page(self, page: Page) -> Optional[str]:
        captcha_retry_count = 0
        max_captcha_retries = 5
        while self.detect_page_snapshot(page).state == PageState.VERIFICATION:
            self.solve_verification_challenge(page)
            self.submit_verification_page(page)
            captcha_retry_count += 1
            print(f"\n验证码尝试次数: {captcha_retry_count}")
            if captcha_retry_count >= max_captcha_retries:
                return "retry"

    def return_from_retry_page(self, page: Page) -> bool:
        back_button = page.locator("input[type='button'][value='Back']").first
        if back_button.count() > 0:
            try:
                with page.expect_navigation(
                    wait_until="networkidle",
                    timeout=self.timeout_seconds * 1000,
                ):
                    back_button.click()
                return True
            except Exception:
                pass

        back_link = page.locator("a:has-text('Back')").first
        if back_link.count() > 0:
            try:
                with page.expect_navigation(
                    wait_until="networkidle",
                    timeout=self.timeout_seconds * 1000,
                ):
                    back_link.click()
                return True
            except Exception:
                pass

        try:
            page.go_back(
                wait_until="networkidle",
                timeout=self.timeout_seconds * 1000,
            )
            return True
        except Exception:
            return False

    def _resolve_service_selection_in_browser(
        self,
        page: Page,
        context: BrowserContext,
        make_appointment_url: str,
    ) -> CalendarRequestContext:
        selected_service_label: Optional[str] = None

        def try_extract_context_using_cached_values() -> Optional[CalendarRequestContext]:
            cookie_header_local = "; ".join(
                f"{cookie['name']}={cookie['value']}"
                for cookie in context.cookies()
            )
            fallback_service_label = selected_service_label or self.current_cached_service_label()
            try:
                parsed_context = extract_calendar_request_context(
                    current_url=page.url,
                    cookie_header=cookie_header_local,
                    fallback_html=page.content(),
                    fallback_service_label=fallback_service_label,
                )
                return self.merge_request_context_with_cache(parsed_context)
            except Exception:
                query = parse_qs(urlparse(page.url).query)
                csrf_token = first_query_value(query, "CSRFToken")
                if not csrf_token:
                    try:
                        csrf_token = extract_csrf_token(page.content())
                    except Exception:
                        csrf_token = None

                appointment_type = first_query_value(query, "type") or self._cached_appointment_type
                service_type = first_query_value(query, "servicetype") or self._cached_service_type
                if not csrf_token or not appointment_type or not service_type:
                    return None

                fallback_context = CalendarRequestContext(
                    cookie_header=cookie_header_local,
                    csrf_token=csrf_token,
                    appointment_type=appointment_type,
                    service_type=service_type,
                    service_label=fallback_service_label,
                    calendar_year=self._cached_calendar_year,
                    calendar_month=self._cached_calendar_month,
                )
                return self.merge_request_context_with_cache(fallback_context)

        page.goto(
            make_appointment_url,
            wait_until="networkidle",
            timeout=self.timeout_seconds * 1000,
        )
        for _ in range(12):
            snapshot = self.detect_page_snapshot(page)

            if snapshot.state == PageState.EXPIRED_ID:
                raise RuntimeError(
                    "detected expired_id page while resolving service selection"
                )

            if snapshot.state == PageState.VERIFICATION:
                if self.handle_verification_page(page) == "retry":
                    raise RuntimeError("verification page retries exceeded while resolving service selection")
                continue

            if snapshot.state == PageState.SERVICE_SELECTION_LOADING:
                self.wait_for_service_selection_options(page)
                continue

            if snapshot.state == PageState.SERVICE_SELECTION:
                selected_service_label = self.submit_service_selection_page(page)
                continue

            request_context = try_extract_context_using_cached_values()
            if request_context is not None:
                return request_context

            if snapshot.state == PageState.UNKNOWN:
                body_preview = normalize_whitespace(page.locator("body").inner_text())[:300]
                raise RuntimeError(
                    f"unrecognized page while resolving service selection: {page.url}\nbody: {body_preview}"
                )

            raise RuntimeError(f"unexpected page state while resolving service selection: {snapshot.state.value}")

        raise RuntimeError("page state machine exceeded transitions while resolving service selection")

    def submit_service_selection_page(self, page: Page) -> str:
        service_snapshot = self.build_service_selection_snapshot(page)
        if service_snapshot.input_count == 0:
            raise RuntimeError("service selection page has no selectable service inputs")

        if service_snapshot.selection_mode == "checkbox":
            if self.service_index is not None:
                raise RuntimeError("当前服务页为多选 checkbox, 只能配置 service_indexs")
            if not self.service_indexs:
                raise RuntimeError("当前服务页为多选 checkbox, 需要配置 service_indexs")
            invalid_indexes = [
                index for index in self.service_indexs
                if index < 1 or index > service_snapshot.input_count
            ]
            if invalid_indexes:
                raise RuntimeError(
                    f"service_indexs={list(self.service_indexs)} 超出范围, "
                    f"页面只有 {service_snapshot.input_count} 个选项"
                )

            self.human_pause(0.2, 0.6)
            for index in range(service_snapshot.input_count):
                checkbox = service_snapshot.service_inputs.nth(index)
                try:
                    if checkbox.is_checked():
                        checkbox.uncheck(force=True)
                except Exception:
                    pass

            selected_labels: List[str] = []
            for service_index in self.service_indexs:
                selected_checkbox = service_snapshot.service_inputs.nth(service_index - 1)
                selected_checkbox.check(force=True)
                label = service_snapshot.service_labels[service_index - 1]
                if label:
                    selected_labels.append(label)
            service_label = ", ".join(selected_labels) if selected_labels else (self.current_cached_service_label() or "")
        else:
            if self.service_index is None:
                raise RuntimeError("当前服务页为单选 radio, 需要配置 service_index")
            if self.service_indexs:
                raise RuntimeError("当前服务页为单选 radio, 只能配置 service_index")
            if self.service_index < 1 or self.service_index > service_snapshot.input_count:
                raise RuntimeError(
                    f"service_index={self.service_index} is out of range, "
                    f"page only has {service_snapshot.input_count} options"
                )

            selected_radio = service_snapshot.service_inputs.nth(self.service_index - 1)
            service_label = service_snapshot.service_labels[self.service_index - 1]
            if not service_label:
                service_label = self.current_cached_service_label() or ""

            self.human_pause(0.2, 0.6)
            selected_radio.check(force=True)

        instruction_checkbox = page.locator("input[name='chkbox01']").first
        if instruction_checkbox.count() > 0:
            try:
                if instruction_checkbox.is_visible() and instruction_checkbox.is_enabled():
                    instruction_checkbox.check(force=True)
            except Exception:
                pass

        submit_button = page.locator("input[type='submit'], button[type='submit']").first
        if submit_button.count() == 0:
            raise RuntimeError("service selection page has no submit button")

        self.human_pause(0.3, 0.8)
        with page.expect_navigation(
            wait_until="networkidle",
            timeout=self.timeout_seconds * 1000,
        ):
            submit_button.click()

        return service_label

    def _fetch_month_html(
        self,
        request_context: CalendarRequestContext,
        target_month: MonthTarget,
    ) -> str:
        url = self.default_calendar_url(request_context, target_month)

        if self._context is not None:
            response = self._context.request.get(
                url,
                headers={
                    "Cookie": request_context.cookie_header,
                    "Referer": self.service_page_url(request_context.csrf_token),
                },
                timeout=self.timeout_seconds * 1000,
            )
            if response.status >= 400:
                raise RuntimeError(
                    f"月份 {target_month.year}-{target_month.month:02d} 的日历请求失败, HTTP 状态码: {response.status}"
                )
            return response.text()

        headers = build_default_headers(
            self.user_agent,
            referer=url,
        )
        headers["Cookie"] = request_context.cookie_header
        request = Request(url, headers=headers)

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                return decode_response_body(response)
        except HTTPError as exc:
            raise RuntimeError(
                f"月份 {target_month.year}-{target_month.month:02d} 的日历请求失败, HTTP 状态码: {exc.code}"
            ) from exc
        except URLError as exc:
            raise RuntimeError(
                f"月份 {target_month.year}-{target_month.month:02d} 的日历请求失败: {exc.reason}"
            ) from exc

    def fetch_months(self, request_context: CalendarRequestContext) -> List[MonthAvailability]:
        target_months = self.resolve_target_months(request_context)
        month_html_by_month: Dict[MonthTarget, str] = {}
        consecutive_month_fetch_errors = 0
        content_abnormal_message = "检测到过期链接页"
        for index, month in enumerate(target_months):
            self.ensure_check_once_within_timeout()
            try:
                month_html_by_month[month] = self._fetch_month_html(request_context, month)
                html_text = month_html_by_month[month].lower()
                if (
                    not any(
                        token in html_text
                        for token in ("appointment date available", "appointment date fully booked")
                    )
                    and is_expired_id_page_text(html_text)
                ):
                    raise RuntimeError(
                        f"月份 {month.year}-{month.month:02d} 的{content_abnormal_message}"
                    )
                consecutive_month_fetch_errors = 0
            except Exception as exc:
                print(f"\n警告\n====\n{exc}")
                month_html_by_month[month] = ""
                if isinstance(exc, RuntimeError) and content_abnormal_message in str(exc):
                    raise
                consecutive_month_fetch_errors += 1
                if (
                    consecutive_month_fetch_errors
                    >= REQUEST_CONTEXT_EXPIRED_CONSECUTIVE_MONTH_FETCH_ERRORS
                ):
                    raise RuntimeError(
                        "获取月份可用日期连续失败, 判定 request_context 过期"
                    ) from exc

            is_last = index == len(target_months) - 1
            if not is_last and self.calendar_request_delay_seconds > 0:
                self.human_pause(
                    self.calendar_request_delay_seconds * 0.7,
                    self.calendar_request_delay_seconds * 1.4,
                )

        return [
            self.parse_month_html(month.year, month.month, month_html_by_month[month])
            for month in target_months
        ]

    @staticmethod
    def parse_month_html(year: int, month: int, month_html: str) -> MonthAvailability:
        days: List[AppointmentDay] = []
        available_cells = AVAILABLE_CELL_RE.findall(month_html)
        saw_non_empty_available_cell = False

        for cell_html in available_cells:
            cell_text = strip_html(cell_html)
            if cell_text:
                saw_non_empty_available_cell = True

            day_match = DAY_LINK_RE.search(cell_html)
            if not day_match:
                continue

            href_match = HREF_RE.search(cell_html)
            count_match = AVAILABLE_COUNT_RE.search(cell_text)
            booking_url = None
            if href_match:
                booking_url = urljoin(BASE_ACS_URL, href_match.group(1))

            days.append(
                AppointmentDay(
                    year=year,
                    month=month,
                    day=int(day_match.group(1)),
                    count=int(count_match.group(1)) if count_match else None,
                    booking_url=booking_url,
                )
            )

        return MonthAvailability(
            year=year,
            month=month,
            available=bool(days) or saw_non_empty_available_cell,
            days=tuple(days),
        )

    def summarize_results(self, results: Iterable[MonthAvailability]) -> List[str]:
        lines: List[str] = []
        for result in results:
            for slot in result.days:
                suffix = f" ({slot.count})" if slot.count is not None else ""
                lines.append(f"{slot.iso_date}{suffix}")
        return lines

    def summarize_target_months(self) -> str:
        if self._resolved_target_months:
            return ", ".join(
                f"{target.year}-{target.month:02d}" for target in self._resolved_target_months
            )
        return ", ".join(self.months)

    def save_available_date_records(
        self,
        request_context: CalendarRequestContext,
        results: Sequence[MonthAvailability],
    ) -> None:
        timestamp = dt.datetime.now().astimezone()
        output_dir = Path(AVAILABLE_DATE_RECORDS_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)

        stem = f"available_dates_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}"
        json_path = output_dir / f"{stem}.json"
        txt_path = output_dir / f"{stem}.txt"

        payload = {
            "checked_at": timestamp.isoformat(),
            "location": self.location.display_name,
            "service": request_context.service_label,
            "months": self.summarize_target_months(),
            "available_dates": [
                {
                    "date": day.iso_date,
                    "count": day.count
                }
                for result in results
                for day in result.days
            ],
        }
        json_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        text_lines = [
            f"checked_at: {payload['checked_at']}",
            f"location: {self.location.display_name}",
            f"service: {request_context.service_label or ''}",
            f"months: {self.summarize_target_months()}",
            "available_dates:",
        ]
        for result in results:
            for day in result.days:
                suffix = f" ({day.count})" if day.count is not None else ""
                text_lines.append(f"{day.iso_date}{suffix}")
        txt_path.write_text("\n".join(text_lines) + "\n", encoding="utf-8")

    def print_check_summary(
        self,
        title: str,
        request_context: CalendarRequestContext,
        available_lines: Sequence[str],
    ) -> None:
        print(f"\n{title}")
        print(f"地点: {self.location.display_name}")
        if request_context.service_label:
            print(f"服务: {request_context.service_label}")
        print(f"月份: {self.summarize_target_months()}")
        print("可预约日期 (剩余名额):")
        if available_lines:
            for line in available_lines:
                print(line)
        else:
            print("无")

    def all_available_days(self, results: Iterable[MonthAvailability]) -> List[AppointmentDay]:
        days: List[AppointmentDay] = []
        for result in results:
            days.extend(result.days)
        return days

    def select_booking_day(self, all_days: Sequence[AppointmentDay]) -> Optional[AppointmentDay]:
        if not all_days:
            return None

        candidates = list(all_days)
        rules = self.booking.date_selection.rules
        if rules:
            candidates = [
                day for day in candidates
                if any(rule.matches(day.date_value) for rule in rules)
            ]

        if not candidates:
            return None

        if self.booking.date_selection.filter_mode == "weight":
            weighted: List[Tuple[AppointmentDay, int]] = []
            for day in candidates:
                matched_weights = [
                    rule.weight for rule in rules if rule.matches(day.date_value)
                ]
                if matched_weights:
                    weighted.append((day, max(matched_weights)))
            if not weighted:
                return None
            best_weight = max(weight for _, weight in weighted)
            candidates = [day for day, weight in weighted if weight == best_weight]
        elif self.booking.date_selection.filter_mode == "max_available":
            max_count = max((day.count or -1) for day in candidates)
            candidates = [day for day in candidates if (day.count or -1) == max_count]

        if self.booking.date_selection.final_pick == "latest":
            return max(candidates, key=lambda day: day.date_value)
        return min(candidates, key=lambda day: day.date_value)

    def date_selection_targets_current_appointment(self) -> bool:
        if self.current_appointment_date is None:
            return False
        rules = self.booking.date_selection.rules
        if not rules:
            return True
        return any(rule.matches(self.current_appointment_date) for rule in rules)

    def virtual_current_appointment_day(self) -> Optional[AppointmentDay]:
        if self.current_appointment_date is None:
            return None
        return AppointmentDay(
            year=self.current_appointment_date.year,
            month=self.current_appointment_date.month,
            day=self.current_appointment_date.day,
            count=None,
            booking_url=None,
        )

    def select_bubble_better_day(
        self,
        all_days: Sequence[AppointmentDay],
    ) -> Optional[AppointmentDay]:
        selected_day = self.select_booking_day(all_days)
        if self.current_appointment_date is None:
            return selected_day

        if not all_days:
            return None

        if self.date_selection_targets_current_appointment():
            candidates = list(all_days)
            current_day = self.virtual_current_appointment_day()
            if current_day is not None and not any(
                day.date_value == current_day.date_value for day in candidates
            ):
                candidates.append(current_day)
            selected_with_current = self.select_booking_day(candidates)
            if (
                selected_with_current is None
                or selected_with_current.date_value == self.current_appointment_date
            ):
                return None
            selected_day = next(
                (
                    day for day in all_days
                    if day.date_value == selected_with_current.date_value
                    and day.booking_url
                ),
                selected_with_current,
            )

        if selected_day is None:
            return None
        if selected_day.date_value == self.current_appointment_date:
            return None
        return selected_day

    def extract_time_slots_from_page(self, page: Page) -> List[TimeSlot]:
        slots: List[TimeSlot] = []
        radios = page.locator("input[name='availTimeSlot']")
        for index in range(radios.count()):
            radio = radios.nth(index)
            value = radio.get_attribute("value") or ""
            row_text = normalize_whitespace(
                radio.evaluate(
                    """(element) => {
                        const row = element.closest('tr');
                        return row ? row.innerText : '';
                    }"""
                )
            )
            label_match = TIME_TEXT_RE.search(row_text)
            count_match = TIME_COUNT_RE.search(row_text)
            label = label_match.group(1) if label_match else value
            slots.append(
                TimeSlot(
                    value=value,
                    label=label,
                    count=int(count_match.group(1)) if count_match else None,
                )
            )
        return slots

    def select_time_slot(self, time_slots: Sequence[TimeSlot]) -> Optional[TimeSlot]:
        if not time_slots:
            return None

        candidates = list(time_slots)
        if self.booking.time_selection.filter_mode == "max_available":
            max_count = max((slot.count or -1) for slot in candidates)
            candidates = [slot for slot in candidates if (slot.count or -1) == max_count]

        if self.booking.time_selection.final_pick == "latest":
            return max(candidates, key=lambda slot: slot.time_value)
        return min(candidates, key=lambda slot: slot.time_value)

    def extract_booking_select_options(
        self,
        page: Page,
        selector: str,
        field_name: str,
        field_label: str,
    ) -> Tuple[str, ...]:
        dom_options: List[str] = []
        select = page.locator(selector)
        if select.count() > 0:
            option_nodes = select.locator("option")
            for index in range(option_nodes.count()):
                dom_options.append(option_nodes.nth(index).inner_text())

        page_html = page.content()
        select_pattern = re.compile(
            GENERIC_SELECT_RE_TEMPLATE.format(name=re.escape(field_name)),
            re.IGNORECASE | re.DOTALL,
        )
        match = select_pattern.search(page_html)
        regex_options: List[str] = []
        if match:
            for _, raw_label in OPTION_TAG_RE.findall(match.group("body")):
                regex_options.append(strip_html(raw_label))

        return choose_preferred_option_values(field_label, dom_options, regex_options)

    def refresh_booking_reference_options(self, page: Page) -> None:
        citizenship_options = self.extract_booking_select_options(
            page,
            "select[name='fNat']",
            "fNat",
            "Country of Citizenship",
        )
        if citizenship_options:
            self._cached_citizenship_options = citizenship_options
            save_single_column_markdown(
                BOOKING_CITIZENSHIP_CACHE_FILE,
                "Country of Citizenship",
                citizenship_options,
            )
        else:
            self._cached_citizenship_options = ()

        birth_country_options = self.extract_booking_select_options(
            page,
            "select[name='fPOB']",
            "fPOB",
            "Country of Birth",
        )
        if birth_country_options:
            self._cached_birth_country_options = birth_country_options
            save_single_column_markdown(
                BOOKING_BIRTH_COUNTRY_CACHE_FILE,
                "Country of Birth",
                birth_country_options,
            )
        else:
            self._cached_birth_country_options = ()

    def validate_booking_reference_options(self, applicant: ApplicantConfig) -> None:
        if (
            self._cached_citizenship_options
            and applicant.citizenship not in self._cached_citizenship_options
            and applicant.citizenship
        ):
            raise BookingConfigError(
                "booking.applicant.citizenship 不在预约页解析到的 Country of Citizenship 选项中"
            )
        if (
            self._cached_birth_country_options
            and applicant.birth_country not in self._cached_birth_country_options
            and applicant.birth_country
        ):
            raise BookingConfigError(
                "booking.applicant.birth_country 不在预约页解析到的 Country of Birth 选项中"
            )

    def get_usable_form_control(self, page: Page, selector: str) -> Optional[Any]:
        locator = page.locator(selector)
        count = locator.count()
        for index in range(count):
            control = locator.nth(index)
            try:
                tag_name = str(control.evaluate("(element) => element.tagName")).strip().upper()
                input_type = normalize_whitespace(control.get_attribute("type") or "").lower()
                hidden_attr = control.get_attribute("hidden")
                readonly_attr = control.get_attribute("readonly")
                if tag_name == "INPUT" and input_type == "hidden":
                    continue
                if hidden_attr is not None:
                    continue
                if tag_name in {"INPUT", "TEXTAREA"} and readonly_attr is not None:
                    continue
                if not control.is_enabled():
                    continue
                if not control.is_visible():
                    continue
                return control
            except Exception:
                continue
        return None

    def fill_text_field_if_present(
        self,
        page: Page,
        selector: str,
        value: str,
        config_key: str,
    ) -> None:
        control = self.get_usable_form_control(page, selector)
        if control is None:
            return
        if not value:
            return
        control.fill(value)

    def fill_optional_text_field_if_present(
        self,
        page: Page,
        selector: str,
        value: str,
    ) -> None:
        control = self.get_usable_form_control(page, selector)
        if control is None:
            return
        if not value:
            return
        control.fill(value)

    def select_option_if_present(
        self,
        page: Page,
        selector: str,
        candidates: Sequence[str],
        config_key: str,
    ) -> bool:
        if self.get_usable_form_control(page, selector) is None:
            return False
        if not any(normalize_whitespace(candidate) for candidate in candidates):
            return False
        self.select_option_by_candidates(page, selector, candidates, config_key)
        return True

    def has_usable_radio_group(self, page: Page, selector: str) -> bool:
        locator = page.locator(selector)
        count = locator.count()
        for index in range(count):
            try:
                radio = locator.nth(index)
                input_type = normalize_whitespace(radio.get_attribute("type") or "").lower()
                if input_type == "hidden":
                    continue
                if not radio.is_enabled():
                    continue
                if not radio.is_visible():
                    continue
                return True
            except Exception:
                continue
        return False

    def select_option_by_candidates(
        self,
        page: Page,
        selector: str,
        candidates: Sequence[str],
        config_key: str,
    ) -> None:
        field_name_match = re.search(r"name=['\"]([^'\"]+)['\"]", selector)
        field_name = field_name_match.group(1) if field_name_match else None
        select = page.locator(selector)
        if select.count() == 0 and field_name:
            select = page.locator(f"select[name='{field_name}']")
        if select.count() == 0 and field_name:
            select = page.locator(f"[name='{field_name}']")

        if select.count() > 0:
            options = select.locator("option")
            labels: List[str] = []
            values: List[str] = []
            for index in range(options.count()):
                option = options.nth(index)
                labels.append(normalize_whitespace(option.inner_text()))
                values.append((option.get_attribute("value") or "").strip())

            for candidate in candidates:
                if candidate in labels:
                    select.select_option(label=candidate)
                    return
                if candidate in values:
                    select.select_option(value=candidate)
                    return

            preview = ", ".join(labels[:10])
            raise BookingConfigError(
                f"{config_key} 不匹配页面选项, 当前可选值示例: {preview}"
            )

        if not field_name:
            raise RuntimeError(f"未找到表单字段: {selector}")

        js_result = page.evaluate(
            """({ fieldName, candidates }) => {
                const controls = Array.from(document.getElementsByName(fieldName));
                const select = controls.find((element) => element && element.tagName === "SELECT");
                if (!select) {
                    return { found: false, labels: [] };
                }

                const options = Array.from(select.options || []);
                const labels = options.map((option) => (option.text || "").replace(/\\s+/g, " ").trim());
                const values = options.map((option) => (option.value || "").trim());
                for (const candidate of candidates) {
                    const labelIndex = labels.indexOf(candidate);
                    if (labelIndex >= 0) {
                        select.selectedIndex = labelIndex;
                        select.dispatchEvent(new Event("change", { bubbles: true }));
                        return { found: true, matched: true, labels };
                    }

                    const valueIndex = values.indexOf(candidate);
                    if (valueIndex >= 0) {
                        select.selectedIndex = valueIndex;
                        select.dispatchEvent(new Event("change", { bubbles: true }));
                        return { found: true, matched: true, labels };
                    }
                }

                return { found: true, matched: false, labels };
            }""",
            {"fieldName": field_name, "candidates": list(candidates)},
        )
        if not isinstance(js_result, dict) or not js_result.get("found"):
            raise RuntimeError(f"未找到表单字段: {selector}")

        if js_result.get("matched"):
            return

        labels = js_result.get("labels")
        preview = ", ".join(labels[:10]) if isinstance(labels, list) else ""
        raise BookingConfigError(
            f"{config_key} 不匹配页面选项, 当前可选值示例: {preview}"
        )

    def open_booking_page(
        self,
        request_context: CalendarRequestContext,
        booking_day: AppointmentDay,
    ) -> Page:
        if not booking_day.booking_url:
            raise RuntimeError(f"{booking_day.iso_date} 没有可用的预约跳转链接")

        context, page = self.ensure_browser_session()
        cookies = cookie_header_to_playwright_cookies(request_context.cookie_header)
        if cookies:
            context.add_cookies(cookies)

        page.goto(
            booking_day.booking_url,
            referer=self.default_calendar_url(
                request_context,
                MonthTarget(year=booking_day.year, month=booking_day.month),
            ),
            wait_until="networkidle",
            timeout=self.timeout_seconds * 1000,
        )
        return page

    def fill_booking_form(
        self,
        page: Page,
        applicant: ApplicantConfig,
        selected_time: TimeSlot,
    ) -> None:
        self.refresh_booking_reference_options(page)
        self.validate_booking_reference_options(applicant)

        time_radio = page.locator(f"input[name='availTimeSlot'][value='{selected_time.value}']")
        if time_radio.count() == 0:
            raise RuntimeError(f"未找到预约时间: {selected_time.value}")
        time_radio.check(force=True)

        self.fill_text_field_if_present(
            page,
            "input[name='txtLastName']",
            applicant.last_name,
            "booking.applicant.last_name",
        )
        self.fill_text_field_if_present(
            page,
            "input[name='txtFirstName']",
            applicant.first_name,
            "booking.applicant.first_name",
        )
        if (
            applicant.dob_day is not None
            and applicant.dob_month is not None
            and applicant.dob_year is not None
        ):
            self.select_option_if_present(
                page,
                "select[name='txtDOBDay']",
                [str(applicant.dob_day), f"{applicant.dob_day:02d}"],
                "booking.applicant.date_of_birth",
            )
            self.select_option_if_present(
                page,
                "select[name='lstDOBMonth']",
                [
                    dt.date(2000, applicant.dob_month, 1).strftime("%b"),
                    dt.date(2000, applicant.dob_month, 1).strftime("%B"),
                    str(applicant.dob_month),
                    f"{applicant.dob_month:02d}",
                ],
                "booking.applicant.date_of_birth",
            )
            self.select_option_if_present(
                page,
                "select[name='lstDOBYear']",
                [str(applicant.dob_year)],
                "booking.applicant.date_of_birth",
            )
        self.fill_text_field_if_present(
            page,
            "input[name='txtTelephone']",
            applicant.telephone,
            "booking.applicant.telephone",
        )
        self.fill_text_field_if_present(
            page,
            "input[name='txtEmailAddress']",
            applicant.email,
            "booking.applicant.email",
        )
        self.select_option_if_present(
            page,
            "select[name='fNat']",
            [applicant.citizenship],
            "booking.applicant.citizenship",
        )
        self.select_option_if_present(
            page,
            "select[name='fPOB']",
            [applicant.birth_country],
            "booking.applicant.birth_country",
        )

        if self.has_usable_radio_group(page, "input[name='fGender']"):
            if not applicant.sex:
                pass
            else:
                gender_radio = page.locator(f"input[name='fGender'][value='{applicant.sex}']")
                if gender_radio.count() == 0:
                    raise BookingConfigError("booking.applicant.sex 不匹配页面选项")
                gender_radio.check(force=True)

        self.fill_text_field_if_present(
            page,
            "input[name='txtPassport']",
            applicant.passport_number,
            "booking.applicant.passport_number",
        )
        self.fill_optional_text_field_if_present(
            page,
            "textarea[name='txtNon1'], input[name='txtNon1']",
            applicant.non_applicant_1,
        )
        self.fill_optional_text_field_if_present(
            page,
            "textarea[name='txtNon2'], input[name='txtNon2']",
            applicant.non_applicant_2,
        )

        privacy = page.locator("input[name='privacy']")
        if privacy.count() == 0:
            raise RuntimeError("未找到隐私声明确认框")
        if not privacy.is_checked():
            privacy.check(force=True)

    def submit_booking_form(self, page: Page) -> bool:
        continue_button = page.locator(
            "input[type='submit'][value='Continue'], button:has-text('Continue')"
        ).first
        if continue_button.count() == 0:
            raise RuntimeError("未找到 Continue 按钮")

        self.human_pause(0.3, 0.9)
        try:
            with page.expect_navigation(
                wait_until="networkidle",
                timeout=self.timeout_seconds * 1000,
            ):
                continue_button.click()
            return True
        except PlaywrightTimeoutError:
            page.wait_for_timeout(800)
            return False

    def refresh_booking_captcha_if_present(self, page: Page) -> None:
        reload_button = page.locator(
            "a.LBD_ReloadLink, a[id$='ReloadLink'], a[title*='Reload the CAPTCHA code']"
        ).first
        if reload_button.count() == 0:
            return
        try:
            if not reload_button.is_visible() or not reload_button.is_enabled():
                return
            self.human_pause(0.1, 0.3)
            reload_button.click()
            page.wait_for_timeout(500)
            print("\n检测到验证码刷新按钮, 已刷新验证码")
        except Exception as exc:
            print(f"\n刷新预约表单验证码失败, 继续原流程\n====\n{exc}")

    def extract_confirmation_details(self, page: Page) -> Dict[str, str]:
        details: Dict[str, str] = {}
        rows = page.locator("tr")
        for index in range(rows.count()):
            row = rows.nth(index)
            cells = row.locator("td")
            if cells.count() < 2:
                continue

            label = normalize_whitespace(cells.nth(0).inner_text())
            value = normalize_whitespace(cells.nth(1).inner_text())
            if not label or not value:
                continue
            if CONFIRMATION_LABEL_RE.search(label):
                details[label.rstrip(":")] = value

        return details

    def detail_value(self, details: Dict[str, str], wanted_label: str) -> str:
        wanted = normalize_whitespace(wanted_label).rstrip(":").lower()
        for label, value in details.items():
            normalized_label = normalize_whitespace(label).rstrip(":").lower()
            if normalized_label == wanted:
                return value
        return ""

    def parse_appointment_detail_date(self, value: str) -> Optional[dt.date]:
        normalized = normalize_whitespace(value)
        if not normalized:
            return None
        for fmt in ("%A, %B %d, %Y", "%B %d, %Y", "%Y-%m-%d"):
            try:
                return dt.datetime.strptime(normalized, fmt).date()
            except ValueError:
                continue
        return None

    def appointment_date_from_details(self, details: Dict[str, str]) -> Optional[dt.date]:
        return self.parse_appointment_detail_date(
            self.detail_value(details, "Appointment Date")
        )

    def appointment_password_from_details(self, details: Dict[str, str]) -> str:
        return self.detail_value(details, "Appointment Password")

    def save_screenshot_as_pdf(
        self,
        screenshot_path: Path,
        pdf_path: Path,
    ) -> bool:
        try:
            with Image.open(screenshot_path) as image:
                image.convert("RGB").save(pdf_path, "PDF")
            return True
        except Exception as exc:
            print(f"\n保存确认页 PDF 失败\n====\n{exc}")
            return False

    def save_confirmation_artifacts(
        self,
        page: Page,
        details: Dict[str, str],
    ) -> Dict[str, str]:
        output_dir = Path(self.booking.artifacts_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        stamp = time.strftime("%Y%m%d_%H%M%S")
        screenshot_path = output_dir / f"booking_confirmation_{stamp}.png"
        pdf_path = output_dir / f"booking_confirmation_{stamp}.pdf"
        html_path = output_dir / f"booking_confirmation_{stamp}.html"
        json_path = output_dir / f"booking_confirmation_{stamp}.json"
        text_path = output_dir / f"booking_confirmation_{stamp}.txt"

        page.screenshot(path=str(screenshot_path), full_page=True)
        pdf_saved = self.save_screenshot_as_pdf(screenshot_path, pdf_path)
        html_path.write_text(page.content(), encoding="utf-8")
        json_path.write_text(
            json.dumps(details, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        text_path.write_text(page.locator("body").inner_text(), encoding="utf-8")

        return {
            "screenshot": str(screenshot_path),
            "pdf": str(pdf_path) if pdf_saved else "",
            "html": str(html_path),
            "json": str(json_path),
            "text": str(text_path),
        }

    def print_confirmation_summary(
        self,
        details: Dict[str, str],
        artifact_paths: Dict[str, str],
    ) -> None:
        print("\n预约成功")
        for key, value in details.items():
            print(f"{key}: {value}")
        print(f"截图: {artifact_paths['screenshot']}")
        if artifact_paths.get("pdf"):
            print(f"截图 PDF: {artifact_paths['pdf']}")
        print(f"HTML: {artifact_paths['html']}")
        print(f"信息 JSON: {artifact_paths['json']}")
        print(f"信息文本: {artifact_paths['text']}")

    def extract_body_preview(self, body_text: str, limit: int = 300) -> str:
        compact = normalize_whitespace(body_text)
        if len(compact) <= limit:
            return compact
        return compact[:limit].rstrip() + "..."

    def attempt_booking(
        self,
        request_context: CalendarRequestContext,
        available_results: Sequence[MonthAvailability],
        selected_day: Optional[AppointmentDay] = None,
    ) -> str:
        if not self.booking.enabled:
            self.close_current_page()
            return "wait"

        if self.booking.applicant_error:
            print(f"\n预约配置错误\n====\n{self.booking.applicant_error}")
            self.close_current_page()
            return "wait"

        if self.booking.applicant is None:
            print("\n预约配置错误\n====\nbooking.applicant 不完整")
            self.close_current_page()
            return "wait"

        if selected_day is None:
            selected_day = self.select_booking_day(self.all_available_days(available_results))
        if selected_day is None:
            print("\n未找到符合预约规则的日期")
            self.close_current_page()
            return "wait"

        if not selected_day.booking_url:
            print(f"\n日期 {selected_day.iso_date} 没有可用的预约跳转链接, 立即重试")
            return "retry"

        booking_form_submitted = False
        try:
            page = self.open_booking_page(request_context, selected_day)
            selected_time: Optional[TimeSlot] = None
            captcha_retry_count = 0
            max_captcha_retries = 5
            for _ in range(20):
                snapshot = self.detect_page_snapshot(page)

                if snapshot.state == PageState.EXPIRED_ID:
                    print("\n检测到过期链接页, 立即重试")
                    return "retry"

                if snapshot.state == PageState.VERIFICATION:
                    if self.handle_verification_page(page) == "retry":
                        print("\n验证码连续失败次数过多, 立即重试")
                        return "retry"
                    continue

                if snapshot.state == PageState.BOOKING_FORM:
                    self.refresh_booking_captcha_if_present(page)
                    if selected_time is None:
                        time_slots = self.extract_time_slots_from_page(page)
                        selected_time = self.select_time_slot(time_slots)
                        if selected_time is None:
                            print("\n当前预约页没有可用时间段, 立即重试")
                            return "retry"
                        print(f"\n准备预约, 日期: {selected_day.iso_date}, 时间: {selected_time.label}")
                    elif booking_form_submitted:
                        print("\n预约表单提交后仍停留在表单页, 可能信息不符合要求, 改为等待")
                        body_preview = self.extract_body_preview(snapshot.body_text)
                        if body_preview:
                            print(f"页面内容预览: {body_preview}")
                        self.close_current_page()
                        return "wait"

                    self.fill_booking_form(page, self.booking.applicant, selected_time)
                    if snapshot.has_inline_verification_prompt:
                        self.solve_verification_challenge(page)
                    booking_form_submitted = True
                    self.submit_booking_form(page)
                    continue

                if snapshot.state == PageState.CONFIRMATION:
                    details = self.extract_confirmation_details(page)
                    artifact_paths = self.save_confirmation_artifacts(page, details)
                    self.print_confirmation_summary(details, artifact_paths)
                    if self.is_bubble_enabled():
                        confirmed_date = self.appointment_date_from_details(details) or selected_day.date_value
                        confirmed_password = self.appointment_password_from_details(details)
                        self.current_appointment_date = confirmed_date
                        self.current_appointment_password = confirmed_password
                        self.bubble_password_checked = True
                        print(
                            f"\nBubble: 新预约已记录, 日期 {confirmed_date.isoformat()}, "
                            f"password: {confirmed_password}"
                        )
                        return "wait"
                    return "exit"

                if snapshot.state == PageState.CANCEL_BOOKING:
                    if self.is_existing_appointment_cancel_text(snapshot.body_text.lower()):
                        print("\n已有预约, 无法新预约, 直接退出程序")
                        self.close_current_page()
                        if self.is_bubble_enabled():
                            return "wait"
                        return "exit"
                    print("\n预约表单提交后进入取消预约页, 改为等待")
                    body_preview = self.extract_body_preview(snapshot.body_text)
                    if body_preview:
                        print(f"页面内容预览: {body_preview}")
                    self.close_current_page()
                    return "wait"

                if snapshot.state == PageState.RETRY:
                    captcha_retry_count += 1
                    if captcha_retry_count > max_captcha_retries:
                        print("\n连续失败次数过多, 立即重试")
                        return "retry"

                    print(f"\n错误, 返回重试 (第 {captcha_retry_count} 次)")
                    if not self.return_from_retry_page(page):
                        print("\n错误页返回失败, 立即重试")
                        return "retry"
                    booking_form_submitted = False
                    continue

                if booking_form_submitted:
                    print(
                        f"\n预约表单提交后进入{self.describe_page_state(snapshot.state)}, "
                        "未完成确认, 改为等待"
                    )
                    body_preview = self.extract_body_preview(snapshot.body_text)
                    if body_preview:
                        print(f"页面内容预览: {body_preview}")
                    self.close_current_page()
                    return "wait"

                if selected_time is None:
                    print("\n预约页面未正常打开, 立即重试")
                else:
                    print("\n预约提交后未进入确认页, 立即重试")
                return "retry"

            print("\n预约状态机跳转次数过多, 立即重试")
            return "retry"
        except BookingConfigError as exc:
            print(f"\n预约配置错误\n====\n{exc}")
            self.close_current_page()
            return "wait"
        except Exception as exc:
            if booking_form_submitted:
                print(f"\n预约表单提交后流程失败, 改为等待\n====\n{exc}")
                self.close_current_page()
                return "wait"
            print(f"\n预约流程失败, 立即重试\n====\n{exc}")
            return "retry"

    def attempt_bubble_booking(
        self,
        request_context: CalendarRequestContext,
        available_results: Sequence[MonthAvailability],
    ) -> str:
        all_days = self.all_available_days(available_results)
        better_day = self.select_bubble_better_day(all_days)
        if better_day is None:
            if self.current_appointment_date is None:
                print("\nBubble: 未发现符合规则的可预约日期")
            else:
                print(
                    "\nBubble: 未发现更优日期, 当前预约日期 "
                    f"{self.current_appointment_date.isoformat()}"
                )
            self.close_current_page()
            return "wait"

        print(f"\nBubble: 发现更优日期 {better_day.iso_date}")

        if not self.bubble_password_checked:
            self.check_bubble_password_appointment()
            if self.bubble_password_checked:
                return "retry"

        if self.current_appointment_password:
            self.cancel_current_appointment()
        elif not self.bubble_password_checked:
            self.cancel_current_appointment(password=self.booking.bubble.password)

        return self.attempt_booking(
            request_context=request_context,
            available_results=available_results,
            selected_day=better_day,
        )

    def check_once(self) -> str:
        now = dt.datetime.now().astimezone()
        print(f"\n当前时间: {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
        directive = "wait"
        self.begin_check_once_window()
        try:
            if self.is_bubble_enabled() and not self.bubble_password_checked:
                self.check_bubble_password_appointment()

            try:
                self.ensure_check_once_within_timeout()
                cached_request_context = self.current_cached_request_context()
                used_cached_request_context = cached_request_context is not None
                if used_cached_request_context:
                    print("\n使用缓存 request_context")
                    request_context = cached_request_context
                else:
                    request_context = self._resolve_with_browser()
                self.ensure_check_once_within_timeout()
                try:
                    results = self.fetch_months(request_context)
                except Exception as exc:
                    if not used_cached_request_context:
                        raise

                    print(f"\n缓存 request_context 失效, 重新开始整个流程\n====\n{exc}")
                    self.clear_cached_request_context()
                    self.reset_browser_session_for_recovery()
                    self.ensure_check_once_within_timeout()
                    request_context = self._resolve_with_browser()
                    self.ensure_check_once_within_timeout()
                    results = self.fetch_months(request_context)
            except Exception as exc:
                print("\n错误\n====")
                print(exc)
                directive = "wait"
                return directive

            available_results = [result for result in results if result.days]
            if available_results:
                self.print_check_summary(
                    title="发现可预约日期",
                    request_context=request_context,
                    available_lines=self.summarize_results(available_results),
                )
                try:
                    self.save_available_date_records(request_context, available_results)
                except Exception as exc:
                    print(f"\n保存可预约日期记录失败\n====\n{exc}")
                if self.is_bubble_enabled():
                    directive = self.attempt_bubble_booking(request_context, available_results)
                else:
                    directive = self.attempt_booking(request_context, available_results)
                return directive

            self.print_check_summary(
                title="未发现可预约日期",
                request_context=request_context,
                available_lines=[],
            )
            directive = "wait"
            return directive
        finally:
            self.end_check_once_window()
            self.close_browser_session()

    @staticmethod
    def _check_once_process_entry(
        scraper: "PassportAppointmentScraper",
        result_queue: Any,
    ) -> None:
        initialize_output_logging()
        try:
            directive = scraper.check_once()
            result_queue.put(
                {
                    "directive": directive,
                    "context_cache": scraper.current_context_cache_payload(),
                    "bubble_state": scraper.current_bubble_state_payload(),
                }
            )
        except Exception as exc:
            print(f"\ncheck_once 子进程异常\n====\n{exc}")
            result_queue.put(
                {
                    "directive": "wait",
                    "context_cache": scraper.current_context_cache_payload(),
                    "bubble_state": scraper.current_bubble_state_payload(),
                }
            )

    @staticmethod
    def _close_process_queue(result_queue: Any) -> None:
        try:
            result_queue.close()
            result_queue.join_thread()
        except Exception:
            pass

    def run_check_once_with_timeout(self) -> str:
        ctx = mp.get_context("spawn")
        result_queue = ctx.Queue(maxsize=1)
        process = ctx.Process(
            target=PassportAppointmentScraper._check_once_process_entry,
            args=(self, result_queue),
        )
        process.start()
        process.join(timeout=self.check_once_max_seconds)

        if process.is_alive():
            print(
                f"\n单次检查超过最大运行时间 {self.check_once_max_seconds} 秒, "
                "已强制中止, 等待下一次执行"
            )
            process.terminate()
            process.join(timeout=5)
            if process.is_alive():
                process.kill()
                process.join(timeout=1)
            self._close_process_queue(result_queue)
            return "wait"

        directive = "wait"
        try:
            result = result_queue.get_nowait()
            if isinstance(result, dict):
                cache_payload = result.get("context_cache")
                if isinstance(cache_payload, dict):
                    self.apply_context_cache_payload(cache_payload)
                bubble_payload = result.get("bubble_state")
                if isinstance(bubble_payload, dict):
                    self.apply_bubble_state_payload(bubble_payload)
                directive_candidate = str(result.get("directive", "wait"))
                if directive_candidate in {"wait", "retry", "exit"}:
                    directive = directive_candidate
            elif isinstance(result, str) and result in {"wait", "retry", "exit"}:
                directive = result
        except Empty:
            if process.exitcode not in (0, None):
                print(f"\ncheck_once 子进程异常退出, exitcode={process.exitcode}")
        finally:
            self._close_process_queue(result_queue)

        if directive in {"wait", "retry", "exit"}:
            return directive
        return "wait"

    def run_forever(self) -> int:
        retry_streak = 0
        while True:
            directive = self.run_check_once_with_timeout() if self.headless else self.check_once()

            if directive == "exit":
                return 0

            if directive == "retry":
                retry_streak += 1
                if self.interval_minutes == 0:
                    return 0

                backoff_seconds = min(
                    MAX_RETRY_BACKOFF_SECONDS,
                    DEFAULT_RETRY_BACKOFF_SECONDS * (2 ** (retry_streak - 1)),
                )
                jitter_seconds = random.uniform(
                    0.0,
                    backoff_seconds * RETRY_BACKOFF_JITTER_RATIO,
                )
                sleep_seconds = backoff_seconds + jitter_seconds
                print(
                        f"\n立即重试前等待 {sleep_seconds:.1f} 秒 "
                        f"(第 {retry_streak} 次)"
                    )
                time.sleep(sleep_seconds)
                continue

            retry_streak = 0

            if self.interval_minutes == 0:
                return 0

            time.sleep(self.interval_minutes * 60)


def build_scraper_from_config(config: Dict[str, Any]) -> PassportAppointmentScraper:
    settings = parse_runtime_config_values(config)

    location = resolve_location_from_city(
        city=settings.city_value,
        headless=not settings.show_browser,
        timeout_seconds=settings.timeout_seconds,
        user_agent=settings.user_agent,
    )

    return PassportAppointmentScraper(
        location=location,
        months=settings.months,
        interval_minutes=settings.interval_minutes,
        service_index=settings.service_index,
        service_indexs=settings.service_indexs,
        headless=not settings.show_browser,
        timeout_seconds=settings.timeout_seconds,
        check_once_max_seconds=settings.check_once_max_seconds,
        action_delay_ms=settings.action_delay_ms,
        calendar_request_delay_seconds=settings.calendar_request_delay_seconds,
        browser_channel=settings.browser_channel,
        booking_config=settings.booking_config,
        user_agent=settings.user_agent,
    )


def main(config_path: str | Path = DEFAULT_CONFIG_PATH) -> int:
    initialize_output_logging()
    try:
        config = load_config(config_path)
        parse_runtime_config_values(config)
        scraper = build_scraper_from_config(config)
    except Exception as exc:
        print(exc)
        return 2

    return scraper.run_forever()


if __name__ == "__main__":
    raise SystemExit(main())
