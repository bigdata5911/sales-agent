import openai
from typing import Dict, List, Optional
import structlog
from datetime import datetime

from app.core.config import settings

logger = structlog.get_logger()

class AIAgent:
    """AI Agent for generating personalized sales messages"""
    
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE
    
    def generate_initial_message(
        self, 
        lead_data: Dict, 
        campaign_data: Dict,
        client_data: Dict
    ) -> str:
        """Generate initial personalized message for a new lead"""
        
        prompt = self._build_initial_prompt(lead_data, campaign_data, client_data)
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            message = response.choices[0].message.content.strip()
            logger.info("Generated initial message", lead_id=lead_data.get("id"), message_length=len(message))
            
            return message
            
        except Exception as e:
            logger.error("Failed to generate initial message", error=str(e))
            return self._get_fallback_message(lead_data, client_data)
    
    def generate_follow_up_message(
        self, 
        lead_data: Dict,
        campaign_data: Dict,
        client_data: Dict,
        conversation_history: List[Dict]
    ) -> str:
        """Generate follow-up message based on conversation history"""
        
        prompt = self._build_follow_up_prompt(
            lead_data, campaign_data, client_data, conversation_history
        )
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            message = response.choices[0].message.content.strip()
            logger.info("Generated follow-up message", lead_id=lead_data.get("id"))
            
            return message
            
        except Exception as e:
            logger.error("Failed to generate follow-up message", error=str(e))
            return self._get_fallback_follow_up(lead_data, client_data)
    
    def process_incoming_message(
        self, 
        message: str, 
        lead_data: Dict,
        campaign_data: Dict,
        client_data: Dict,
        conversation_history: List[Dict]
    ) -> Dict:
        """Process incoming message and determine next action"""
        
        prompt = self._build_processing_prompt(
            message, lead_data, campaign_data, client_data, conversation_history
        )
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_processing_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            result = response.choices[0].message.content.strip()
            
            # Parse the response to extract action and message
            action, response_message = self._parse_processing_response(result)
            
            logger.info("Processed incoming message", 
                       lead_id=lead_data.get("id"), 
                       action=action)
            
            return {
                "action": action,  # respond, schedule_call, convert, etc.
                "message": response_message,
                "confidence": 0.8  # Could be calculated based on response
            }
            
        except Exception as e:
            logger.error("Failed to process incoming message", error=str(e))
            return {
                "action": "respond",
                "message": "Thank you for your message. I'll have someone from our team contact you shortly.",
                "confidence": 0.5
            }
    
    def _build_initial_prompt(self, lead_data: Dict, campaign_data: Dict, client_data: Dict) -> str:
        """Build prompt for initial message generation"""
        
        return f"""
        Generate a personalized initial WhatsApp message for a sales lead.
        
        Lead Information:
        - Name: {lead_data.get('name', 'Unknown')}
        - Phone: {lead_data.get('phone', 'Unknown')}
        - Email: {lead_data.get('email', 'Unknown')}
        - Additional Data: {lead_data.get('lead_data', {})}
        
        Campaign Information:
        - Campaign Name: {campaign_data.get('name', 'Unknown')}
        - Description: {campaign_data.get('description', 'Unknown')}
        - Message Templates: {campaign_data.get('message_templates', {})}
        
        Client Information:
        - Company Name: {client_data.get('name', 'Unknown')}
        - Industry: {client_data.get('settings', {}).get('industry', 'Unknown')}
        - Services: {client_data.get('settings', {}).get('services', [])}
        
        Requirements:
        1. Keep the message under 160 characters
        2. Make it personal and engaging
        3. Include a clear call-to-action
        4. Be professional but friendly
        5. Mention the specific service/product they showed interest in
        
        Generate only the message content, no additional formatting.
        """
    
    def _build_follow_up_prompt(
        self, 
        lead_data: Dict, 
        campaign_data: Dict, 
        client_data: Dict, 
        conversation_history: List[Dict]
    ) -> str:
        """Build prompt for follow-up message generation"""
        
        history_text = "\n".join([
            f"{msg['direction']}: {msg['content']}" 
            for msg in conversation_history[-5:]  # Last 5 messages
        ])
        
        return f"""
        Generate a follow-up WhatsApp message based on the conversation history.
        
        Lead Information:
        - Name: {lead_data.get('name', 'Unknown')}
        - Current Status: {lead_data.get('status', 'Unknown')}
        
        Conversation History:
        {history_text}
        
        Campaign Information:
        - Campaign: {campaign_data.get('name', 'Unknown')}
        - Templates: {campaign_data.get('message_templates', {})}
        
        Client Information:
        - Company: {client_data.get('name', 'Unknown')}
        
        Requirements:
        1. Keep under 160 characters
        2. Reference previous conversation
        3. Provide value or new information
        4. Include clear next steps
        5. Be persistent but not pushy
        
        Generate only the message content.
        """
    
    def _build_processing_prompt(
        self, 
        message: str, 
        lead_data: Dict, 
        campaign_data: Dict, 
        client_data: Dict, 
        conversation_history: List[Dict]
    ) -> str:
        """Build prompt for processing incoming messages"""
        
        history_text = "\n".join([
            f"{msg['direction']}: {msg['content']}" 
            for msg in conversation_history[-5:]
        ])
        
        return f"""
        Analyze this incoming message and determine the appropriate response.
        
        Incoming Message: "{message}"
        
        Lead Information:
        - Name: {lead_data.get('name', 'Unknown')}
        - Status: {lead_data.get('status', 'Unknown')}
        
        Conversation History:
        {history_text}
        
        Client Information:
        - Company: {client_data.get('name', 'Unknown')}
        - Services: {client_data.get('settings', {}).get('services', [])}
        
        Determine the appropriate action and response:
        1. If they're interested in buying - respond with conversion message
        2. If they have questions - answer professionally
        3. If they want to speak to someone - schedule a call
        4. If they're not interested - politely end conversation
        5. If unclear - ask clarifying questions
        
        Respond in this format:
        ACTION: [action_type]
        MESSAGE: [response_message]
        """
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for message generation"""
        return """
        You are an AI sales agent for a digital marketing agency. Your role is to:
        1. Generate personalized WhatsApp messages for sales leads
        2. Be professional, friendly, and engaging
        3. Focus on the specific service/product the lead showed interest in
        4. Keep messages concise and actionable
        5. Use the client's brand voice and messaging guidelines
        6. Always include a clear next step or call-to-action
        """
    
    def _get_processing_system_prompt(self) -> str:
        """Get system prompt for message processing"""
        return """
        You are an AI sales agent analyzing incoming messages. Your role is to:
        1. Understand the lead's intent and sentiment
        2. Determine the appropriate response action
        3. Generate relevant and helpful responses
        4. Identify conversion opportunities
        5. Handle objections professionally
        6. Escalate to human when necessary
        """
    
    def _parse_processing_response(self, response: str) -> tuple:
        """Parse the processing response to extract action and message"""
        lines = response.strip().split('\n')
        action = "respond"
        message = "Thank you for your message. I'll be happy to help you."
        
        for line in lines:
            if line.startswith("ACTION:"):
                action = line.replace("ACTION:", "").strip()
            elif line.startswith("MESSAGE:"):
                message = line.replace("MESSAGE:", "").strip()
        
        return action, message
    
    def _get_fallback_message(self, lead_data: Dict, client_data: Dict) -> str:
        """Get fallback message when AI generation fails"""
        name = lead_data.get('name', 'there')
        company = client_data.get('name', 'our company')
        
        return f"Hi {name}! Thanks for your interest in {company}. I'd love to tell you more about our services. When would be a good time to chat?"
    
    def _get_fallback_follow_up(self, lead_data: Dict, client_data: Dict) -> str:
        """Get fallback follow-up message"""
        name = lead_data.get('name', 'there')
        
        return f"Hi {name}! Just following up on our previous conversation. Would you like to learn more about our services?" 