from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from typing import Dict, Optional, List
import structlog
from datetime import datetime
import json

from app.core.config import settings

logger = structlog.get_logger()

class WhatsAppService:
    """WhatsApp messaging service using Twilio"""
    
    def __init__(self):
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self.from_number = settings.TWILIO_PHONE_NUMBER
    
    def send_message(
        self, 
        to_number: str, 
        message: str, 
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Send WhatsApp message via Twilio"""
        
        try:
            # Format phone number (ensure it starts with country code)
            formatted_number = self._format_phone_number(to_number)
            
            # Send message
            message_obj = self.client.messages.create(
                from_=f"whatsapp:{self.from_number}",
                body=message,
                to=f"whatsapp:{formatted_number}"
            )
            
            logger.info("WhatsApp message sent", 
                       message_sid=message_obj.sid,
                       to_number=formatted_number,
                       status=message_obj.status)
            
            return {
                "message_sid": message_obj.sid,
                "status": message_obj.status,
                "to_number": formatted_number,
                "sent_at": datetime.utcnow(),
                "metadata": metadata or {}
            }
            
        except TwilioException as e:
            logger.error("Failed to send WhatsApp message", 
                        error=str(e),
                        to_number=to_number)
            raise
    
    def send_template_message(
        self, 
        to_number: str, 
        template_name: str, 
        template_variables: Dict,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Send WhatsApp template message"""
        
        try:
            formatted_number = self._format_phone_number(to_number)
            
            # Create message with template
            message_obj = self.client.messages.create(
                from_=f"whatsapp:{self.from_number}",
                body=self._build_template_message(template_name, template_variables),
                to=f"whatsapp:{formatted_number}"
            )
            
            logger.info("WhatsApp template message sent",
                       message_sid=message_obj.sid,
                       template_name=template_name)
            
            return {
                "message_sid": message_obj.sid,
                "status": message_obj.status,
                "template_name": template_name,
                "template_variables": template_variables,
                "sent_at": datetime.utcnow(),
                "metadata": metadata or {}
            }
            
        except TwilioException as e:
            logger.error("Failed to send template message", error=str(e))
            raise
    
    def get_message_status(self, message_sid: str) -> Dict:
        """Get status of a sent message"""
        
        try:
            message = self.client.messages(message_sid).fetch()
            
            return {
                "message_sid": message.sid,
                "status": message.status,
                "error_code": message.error_code,
                "error_message": message.error_message,
                "sent_at": message.date_sent,
                "delivered_at": message.date_delivered
            }
            
        except TwilioException as e:
            logger.error("Failed to get message status", 
                        message_sid=message_sid,
                        error=str(e))
            raise
    
    def validate_webhook_signature(
        self, 
        signature: str, 
        url: str, 
        params: Dict
    ) -> bool:
        """Validate Twilio webhook signature"""
        
        try:
            from twilio.request_validator import RequestValidator
            validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
            
            return validator.validate(url, params, signature)
            
        except Exception as e:
            logger.error("Failed to validate webhook signature", error=str(e))
            return False
    
    def parse_webhook_data(self, webhook_data: Dict) -> Dict:
        """Parse incoming webhook data from Twilio"""
        
        try:
            return {
                "message_sid": webhook_data.get("MessageSid"),
                "from_number": webhook_data.get("From", "").replace("whatsapp:", ""),
                "to_number": webhook_data.get("To", "").replace("whatsapp:", ""),
                "body": webhook_data.get("Body", ""),
                "message_status": webhook_data.get("MessageStatus"),
                "timestamp": webhook_data.get("MessageTimestamp"),
                "account_sid": webhook_data.get("AccountSid"),
                "num_media": webhook_data.get("NumMedia", "0"),
                "media_urls": webhook_data.get("MediaUrl0", "").split(",") if webhook_data.get("MediaUrl0") else [],
                "raw_data": webhook_data
            }
            
        except Exception as e:
            logger.error("Failed to parse webhook data", error=str(e))
            raise
    
    def send_bulk_messages(
        self, 
        messages: List[Dict]
    ) -> List[Dict]:
        """Send multiple messages in batch"""
        
        results = []
        
        for message_data in messages:
            try:
                result = self.send_message(
                    to_number=message_data["to_number"],
                    message=message_data["message"],
                    metadata=message_data.get("metadata")
                )
                results.append({
                    "success": True,
                    "data": result,
                    "original_data": message_data
                })
                
            except Exception as e:
                logger.error("Failed to send bulk message", 
                           to_number=message_data.get("to_number"),
                           error=str(e))
                results.append({
                    "success": False,
                    "error": str(e),
                    "original_data": message_data
                })
        
        return results
    
    def _format_phone_number(self, phone_number: str) -> str:
        """Format phone number for WhatsApp"""
        
        # Remove any non-digit characters
        cleaned = ''.join(filter(str.isdigit, phone_number))
        
        # Ensure it starts with country code
        if not cleaned.startswith('1') and len(cleaned) == 10:
            cleaned = '1' + cleaned  # Assume US number
        
        return cleaned
    
    def _build_template_message(self, template_name: str, variables: Dict) -> str:
        """Build template message with variables"""
        
        # Simple template system - in production, you'd use Twilio's template system
        templates = {
            "welcome": "Hi {name}! Welcome to {company}. Thanks for your interest in {service}.",
            "follow_up": "Hi {name}! Just following up on our conversation about {service}. Are you still interested?",
            "appointment": "Hi {name}! Your appointment with {company} is confirmed for {date} at {time}.",
            "reminder": "Hi {name}! Don't forget about your upcoming {service} consultation.",
            "thank_you": "Hi {name}! Thank you for choosing {company}. We appreciate your business!"
        }
        
        template = templates.get(template_name, "Hi {name}! Thank you for your interest.")
        
        try:
            return template.format(**variables)
        except KeyError as e:
            logger.error("Missing template variable", variable=str(e))
            return template.format(name="there", company="our company", service="our services")
    
    def get_account_info(self) -> Dict:
        """Get Twilio account information"""
        
        try:
            account = self.client.api.accounts(settings.TWILIO_ACCOUNT_SID).fetch()
            
            return {
                "account_sid": account.sid,
                "friendly_name": account.friendly_name,
                "status": account.status,
                "type": account.type,
                "date_created": account.date_created,
                "date_updated": account.date_updated
            }
            
        except TwilioException as e:
            logger.error("Failed to get account info", error=str(e))
            raise
    
    def get_usage_stats(self, start_date: str, end_date: str) -> Dict:
        """Get usage statistics for the account"""
        
        try:
            usage_records = self.client.usage.records.list(
                start_date=start_date,
                end_date=end_date
            )
            
            stats = {
                "total_messages": 0,
                "total_cost": 0,
                "by_category": {}
            }
            
            for record in usage_records:
                category = record.category
                if category not in stats["by_category"]:
                    stats["by_category"][category] = {
                        "count": 0,
                        "cost": 0
                    }
                
                stats["by_category"][category]["count"] += int(record.count)
                stats["by_category"][category]["cost"] += float(record.price)
                stats["total_messages"] += int(record.count)
                stats["total_cost"] += float(record.price)
            
            return stats
            
        except TwilioException as e:
            logger.error("Failed to get usage stats", error=str(e))
            raise 