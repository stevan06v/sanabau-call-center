import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Optional, List, Union
from dotenv import load_dotenv

class MailSender:
    """suppa mail sender"""
    
    def __init__(self):
        load_dotenv()
        self.smtp_server = os.getenv('SMTP_SERVER', 'gfra1000.siteground.eu')
        self.smtp_port = int(os.getenv('SMTP_PORT', '465'))
        self.email = os.getenv('EMAIL')
        self.password = os.getenv('EMAIL_PASSWORD')
        
        if not self.email or not self.password:
            raise ValueError("EMAIL and EMAIL_PASSWORD must be set in .env file")
    
    def send_html_email(
        self,
        to: Union[str, List[str]],
        subject: str,
        html_path: str,
        cc: Optional[Union[str, List[str]]] = None,
        bcc: Optional[Union[str, List[str]]] = None
    ) -> bool:
        """
        Send HTML email
        
        Args:
            to: Recipient email(s)
            subject: Email subject
            html_path: Path to HTML file
            cc: CC recipient(s) (optional)
            bcc: BCC recipient(s) (optional)
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            # Read HTML content
            html_content = Path(html_path).read_text(encoding='utf-8')
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email
            msg['To'] = self._format_recipients(to)
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = self._format_recipients(cc)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Prepare recipient list
            recipients = self._get_all_recipients(to, cc, bcc)
            
            # Send email
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.email, self.password)
                server.sendmail(self.email, recipients, msg.as_string())
            
            return True
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def send_text_email(
        self,
        to: Union[str, List[str]],
        subject: str,
        text: str,
        cc: Optional[Union[str, List[str]]] = None,
        bcc: Optional[Union[str, List[str]]] = None
    ) -> bool:
        """
        Send plain text email
        
        Args:
            to: Recipient email(s)
            subject: Email subject
            text: Email text content
            cc: CC recipient(s) (optional)
            bcc: BCC recipient(s) (optional)
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEText(text, 'plain', 'utf-8')
            msg['From'] = self.email
            msg['To'] = self._format_recipients(to)
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = self._format_recipients(cc)
            
            # Prepare recipient list
            recipients = self._get_all_recipients(to, cc, bcc)
            
            # Send email
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.email, self.password)
                server.sendmail(self.email, recipients, msg.as_string())
            
            return True
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def _format_recipients(self, recipients: Union[str, List[str]]) -> str:
        """Format recipients for email header"""
        if isinstance(recipients, str):
            return recipients
        return ', '.join(recipients)
    
    def _get_all_recipients(
        self,
        to: Union[str, List[str]],
        cc: Optional[Union[str, List[str]]] = None,
        bcc: Optional[Union[str, List[str]]] = None
    ) -> List[str]:
        """Get all recipients as a flat list"""
        recipients = []
        
        # Add TO recipients
        if isinstance(to, str):
            recipients.append(to)
        else:
            recipients.extend(to)
        
        # Add CC recipients
        if cc:
            if isinstance(cc, str):
                recipients.append(cc)
            else:
                recipients.extend(cc)
        
        # Add BCC recipients
        if bcc:
            if isinstance(bcc, str):
                recipients.append(bcc)
            else:
                recipients.extend(bcc)
        
        return recipients


# Convenience functions for easy usage
def send_html_email(to: Union[str, List[str]], subject: str, html_path: str, **kwargs) -> bool:
    """Quick function to send HTML email"""
    sender = MailSender()
    return sender.send_html_email(to, subject, html_path, **kwargs)


def send_text_email(to: Union[str, List[str]], subject: str, text: str, **kwargs) -> bool:
    """Quick function to send text email"""
    sender = MailSender()
    return sender.send_text_email(to, subject, text, **kwargs)


# Command line interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Perfect Mail Sender')
    parser.add_argument('to', help='Recipient email address')
    parser.add_argument('subject', help='Email subject')
    parser.add_argument('--html', help='Path to HTML file')
    parser.add_argument('--text', help='Text content')
    parser.add_argument('--cc', help='CC recipients (comma-separated)')
    parser.add_argument('--bcc', help='BCC recipients (comma-separated)')
    
    args = parser.parse_args()
    
    # Parse CC and BCC
    cc = args.cc.split(',') if args.cc else None
    bcc = args.bcc.split(',') if args.bcc else None
    
    sender = MailSender()
    
    if args.html:
        success = sender.send_html_email(args.to, args.subject, args.html, cc=cc, bcc=bcc)
    elif args.text:
        success = sender.send_text_email(args.to, args.subject, args.text, cc=cc, bcc=bcc)
    else:
        print("Error: Either --html or --text must be provided")
        exit(1)
    
    if success:
        print("Email sent successfully!")
    else:
        print("Failed to send email")
        exit(1)