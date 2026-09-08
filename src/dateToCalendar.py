# DateToCalendar Written By Bryan Chang in Python 3.12 in PyCharm on 9/8/2026
# Assistance and reference from ChatGPT GPT-5.6 Luna and Gemini 3.6 Flash

from datetime import timedelta, datetime  # Used to define event duration
from tzlocal import get_localzone_name  # Detects local system timezone name
from dateparser.search import search_dates
import pytz

from dateparser import parse #parser for dates
from ics import Calendar, Event # Library to make ics objects

def get_system_timezone() -> str:
    """Detects and returns the system's local IANA timezone name (e.g., 'America/New_York')."""
    try:
        return get_localzone_name()
    except Exception:
        return "UTC"  # Fallback if system timezone cannot be resolved

def preview_and_confirm_events(results):
    """Prints a structured preview of found dates and prompts user for confirmation."""
    print("\n" + "=" * 60)
    print(" PARSED EVENTS PREVIEW")
    print("=" * 60)
    print(f"{'#':<4} | {'EXTRACTED TEXT':<25} | {'PARSED DATE & TIME':<25}")
    print("-" * 60)

    for idx, (matched_text, start_dt) in enumerate(results, start=1):
        # Format datetime string for easy reading
        formatted_dt = start_dt.strftime("%Y-%m-%d %I:%M %p (%Z)")
        print(f"{idx:<4} | {matched_text[:25]:<25} | {formatted_dt:<25}")

    print("=" * 60)

    # Prompt user for confirmation
    while True:
        response = (
            input("\nDo you want to create .ics files for these events? (y/n): ")
            .strip()
            .lower()
        )
        if response in ["y", "yes"]:
            return True
        elif response in ["n", "no"]:
            return False
        else:
            print("Please enter 'y' for yes or 'n' for no.")

def extract_events_and_generate_ics(
        email_text: str,
        default_duration_hours: int = 1,
        user_timezone: str = None, #Default to none to trigger auto-detection
):
    """Parses email text for date and time and creates .ics files using local system timezone."""

    # Auto-detect local system timezone if none is explicitly provided
    if user_timezone is None:
        user_timezone = get_system_timezone()

    print(f"Using detected timezone: {user_timezone}")

    # Fetch user's local timezone and current time (add try/catch exception later)
    tz = pytz.timezone(user_timezone)
    now = datetime.now(tz)

    # Create setting dictionary for dateparser search_dates function
    settings = {
        # Assumes dates are in the future
        'PREFER_DATES_FROM': 'future',
        # Establish and base time in user time zone
        "TIMEZONE": user_timezone,
        "TO_TIMEZONE": user_timezone,
        "RETURN_AS_TIMEZONE_AWARE": True,
        "RELATIVE_BASE": now,
    }

    # Scan the text for natural language date and time phrases
    # search_dates returns tuples of (matched_text_string, datetime_object)
    raw_results = search_dates(email_text, settings=settings)

    # Stop execution if dateparser did not find any dates or times in the text
    if not raw_results:
        print("No date/time information found in the provided text.")
        return []

    # Filter out false positives (e.g., stray single digits or short fragments)
    valid_results = []
    for matched_text, _ in raw_results:
        # Filter out short fragments or pure numbers
        if len(matched_text.strip()) < 3 or matched_text.strip().isdigit():
            continue

        # Reparsed the exact matched text snippet to combine tommorow  + 9am accurately
        parsed_dt = parse(matched_text, settings=settings)

        if parsed_dt:
            valid_results.append((matched_text, parsed_dt))

    if not valid_results:
        print("No valid event dates remained after filtering.")
        return []

    # Call the display preview function and wait for user confirmation
    if not preview_and_confirm_events(valid_results):
        print("Operation cancelled. No .ics files were created.")
        return []

    # Clean and split the email into non-empty lines
    lines = [line.strip() for line in email_text.splitlines() if line.strip()]
    # Grab the first line (up to 50 chars) to use as a fallback event title
    default_summary = lines[0][:50] if lines else "Calendar Event"

    # Store the list of generated file paths
    created_files = []



    # Loop through each extracted date/time match found in the text
    for idx, (matched_text, start_dt) in enumerate(valid_results, start=1):
        # Initialize a new calendar object
        cal = Calendar()
        # Initialize a new event object
        event = Event()

        # Set the title of the event
        event.name = f"Event: {default_summary}"
        # Set the starting date and time of the event
        event.begin = start_dt
        # Attach the matched phrase and original text to the event description
        event.description = (
            f"Extracted from email:\n'{matched_text}'\n\nFull Text:\n{email_text}"
        )# Set the length of the event (defaults to 1 hour)
        event.duration = timedelta(hours=default_duration_hours)

        # Add the constructed event to the calendar object
        cal.events.add(event)

        # Generate a unique filename using the index and start timestamp
        filename = f"event_{idx}_{start_dt.strftime('%Y%m%d_%H%M')}.ics"

        # Open the file and write the formatted ICS calendar data to disk
        with open(filename, "w", encoding="utf-8") as f:
            f.writelines(cal.serialize_iter())

        # Track created filename and display output log
        created_files.append(filename)
        print(f"Created: {filename} -> Begins {start_dt}")

    # Return the list of created file paths
    return created_files


# Execute sample usage only when this script is run directly (not imported as a module)
if __name__ == "__main__":
    # Sample input string simulating an email
    user_input_email_text = input("Enter email text here: \n")
    # Call the main function with the sample text
    extract_events_and_generate_ics(user_input_email_text)