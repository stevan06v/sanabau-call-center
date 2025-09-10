import random
import smtplib
import string
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from urllib.parse import quote

from libs.models import VapiCallReport, Analysis, Call, Customer, StructuredDate


def classify_call(ended_reason: str) -> str:
    success_reasons = {
        "assistant-ended-call",
        "assistant-ended-call-after-message-spoken",
        "assistant-ended-call-with-hangup-task",
        "assistant-forwarded-call",
        "assistant-said-end-call-phrase",
        "customer-ended-call",
        "vonage-completed",
        "voicemail",
    }

    retry_reasons = {
        "customer-busy",
        "customer-did-not-answer",
        "customer-did-not-give-microphone-permission",
        "call.in-progress.error-assistant-did-not-receive-customer-audio",
        "phone-call-provider-closed-websocket",
        "phone-call-provider-bypass-enabled-but-no-call-received",
        "twilio-failed-to-connect-call",
        "twilio-reported-customer-misdialed",
        "vonage-disconnected",
        "vonage-failed-to-connect-call",
        "vonage-rejected",
        "call.in-progress.error-sip-telephony-provider-failed-to-connect-call",
        "call.forwarding.operator-busy",
        "silence-timed-out",
    }

    if ended_reason in success_reasons:
        return "success"
    elif ended_reason in retry_reasons:
        return "retry"
    else:
        return "error"


def render_confirmation_client(vapi_call_report: VapiCallReport):
    BASE_DIR = Path(__file__).resolve().parent.parent
    template_path = BASE_DIR / "resources" / "confirmation-client.html"
    html_template = template_path.read_text(encoding="utf-8")

    name = str(vapi_call_report.analysis.structuredData.name or "")
    email = str(vapi_call_report.analysis.structuredData.email or "")
    fax = str(vapi_call_report.analysis.structuredData.fax or "")
    branche = str(vapi_call_report.analysis.structuredData.branche or "")
    status = str(vapi_call_report.analysis.structuredData.status or "")

    html_filled = (
        html_template
        .replace("{{name}}", name)
        .replace("{{email}}", email)
        .replace("{{phone_or_fax}}", fax)
        .replace("{{branche}}", branche)
        .replace("{{status}}", status)
    )
    return html_filled


def render_notification_company(vapi_call_report: VapiCallReport):
    BASE_DIR = Path(__file__).resolve().parent.parent
    template_path = BASE_DIR / "resources" / "notification-sanabau.html"
    html_template = template_path.read_text(encoding="utf-8")

    call_id = str(vapi_call_report.call.id or "")
    name = str(vapi_call_report.analysis.structuredData.name or "")
    call_date = str(vapi_call_report.startedAt or "")
    status = str(vapi_call_report.analysis.structuredData.status or "")
    email = str(vapi_call_report.analysis.structuredData.email or "")
    branche = str(vapi_call_report.analysis.structuredData.branche or "")
    fax = str(vapi_call_report.analysis.structuredData.fax or "")
    summary = str(vapi_call_report.summary or "")
    audio_url = str(vapi_call_report.stereoRecordingUrl or "")

    html_filled = (
        html_template
        .replace("{{call_id}}", call_id)
        .replace("{{name}}", name)
        .replace("{{call_date}}", call_date)
        .replace("{{status}}", status)
        .replace("{{email}}", email)
        .replace("{{branche}}", branche)
        .replace("{{fax}}", fax)
        .replace("{{summary}}", summary)
        .replace("{{audio_url}}", audio_url or "")
    )

    return html_filled


TEMP_DIR = Path(__file__).resolve().parent.parent / "resources" / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


def save_temp_html(rendered_html: str, prefix: str = "email") -> Path:
    rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    filename = f"{prefix}_{rand_str}.html"
    file_path = TEMP_DIR / filename

    file_path.write_text(rendered_html, encoding="utf-8")

    return file_path


def send_html_email(smtp_server, smtp_port, sender_email, sender_password, recipient_email, subject, content):
    try:
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = recipient_email
        message['Subject'] = subject

        encoded_email = quote(recipient_email)

        with open(content, 'r', encoding='utf-8') as file:
            html_content = file.read()

        html_part = MIMEText(html_content, 'html', 'utf-8')
        message.attach(html_part)

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
            print(f"Email sent to {recipient_email}")
            return True  # Success
    except Exception as e:
        print(f"Failed to send email to {recipient_email}: {e}")
        return False


if __name__ == "__main__":

    dummy_report = VapiCallReport(
        stereoRecordingUrl="https://example.com/audio/test-call.mp3",
        customer=Customer(number="+49 151 12345678"),
        startedAt=datetime(2025, 9, 10, 14, 30),
        durationMinutes=12.5,
        call=Call(id="CALL-XYZ-98765"),
        endedReason="completed",
        analysis=Analysis(
            structuredData=StructuredDate(
                name="Max Mustermann",
                fax="030-1234567",
                email="max.mustermann@example.com",
                notes="Besonders interessiert an Sanierungsarbeiten",
                status="Interessiert",
                branche="Bauunternehmen"
            )
        ),
        summary="Der Kunde hat starkes Interesse an einem Angebot gezeigt. "
                "Er möchte weitere Informationen per E-Mail erhalten."
    )
    print(render_notification_company(dummy_report))
    print(render_confirmation_client(dummy_report))

    success = send_html_email(
        smtp_server="78.46.226.32",
        smtp_port=55587,
        sender_email="info@homa-bau.com",
        sender_password="8@B%eD>AGtd8LM:",
        recipient_email="jonathan@webhoch.com",
        subject="Test Email",
        content=save_temp_html(render_notification_company(dummy_report))
    )
    print(success)

