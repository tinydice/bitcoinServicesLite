import imaplib
import email
from email.header import decode_header
from email.message import EmailMessage
from src.helpers import *
from bitcoinUtils.src.FORMATutils import *

IMAP_SERVER = "imap.gmail.com"
EMAIL_ADDR = "raspi5bolt@gmail.com"
EMAIL_PASS = "numz ppfb mdeo gbvo"
TO_EMAIL = "tyler.rterhune@gmail.com"

def send_email(subject, body):
    appendToDatalog(f"Sending email: {subject}")
    msg = EmailMessage()
    msg.set_content(body)
    msg['From'] = EMAIL_ADDR
    msg['To'] = TO_EMAIL
    msg['Subject'] = subject

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()

    try:
        server.login(EMAIL_ADDR, EMAIL_PASS)
        server.send_message(msg)
    except smtplib.SMTPAuthenticationError:
        appendToDatalog("Authentication failed! Check email & app password.")
    except smtplib.SMTPException as e:
        appendToDatalog(f"SMTP error: {e}")
    finally:
        server.quit()

def checkEmail():
    appendToDatalog(f"Checking raspi5bolt@gmail.com")
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ADDR, EMAIL_PASS)
        mail.select("inbox")

        status, messages = mail.search(None, "UNSEEN")
        mailIds = messages[0].split()

        if not mailIds:
            print("No new emails.")
            return None

        emailParts = []
        for mailId in mailIds:
            status, msgData = mail.fetch(mailId, "(RFC822)")
            for responsePart in msgData:
                if isinstance(responsePart, tuple):
                    msg = email.message_from_bytes(responsePart[1])
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or "utf-8").strip()

                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode("utf-8", errors="ignore").strip()
                                emailParts.append((subject, body))
                                break
                    else:
                        body = msg.get_payload(decode=True).decode("utf-8", errors="ignore").strip()

        mail.logout()

        return emailParts
    except Exception as e:
        print(f"Error: {e}")

def datalogEmail():
    datalog = ''.join(readDatalog())
    send_email(f"Raspi5Bolt Datalog", datalog)

def helpEmail():
    send_email(f"Raspi5Bolt Help", 
        f"log: Gets bitcoinService's datalog.\n\n"
        f"status: Gets raspi5bolt node's blockheight status.\n\n"
        f"help: Gets list of commands and explanations.\n\n"
    )
