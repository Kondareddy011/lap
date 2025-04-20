"""
Command Processing Module for Personal Voice Assistant

This module interprets recognized speech and determines appropriate actions.
It includes intent parsing, command routing, and context management.
"""

import os
import re
import json
import logging
import datetime
import importlib
import pkgutil
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('command_processing')

class IntentParser:
    """Extracts meaning and intent from recognized text."""
    
    def __init__(self, intent_patterns=None):
        """
        Initialize the intent parser.
        
        Args:
            intent_patterns (dict): Dictionary mapping intents to regex patterns
        """
        self.intent_patterns = intent_patterns or {}
        self._load_default_patterns()
        
    def _load_default_patterns(self):
        """Load default intent patterns if none provided."""
        if not self.intent_patterns:
            self.intent_patterns = {
                # System intents
                "help": [r"help( me)?", r"what can (you|I) do", r"what commands"],
                "stop": [r"stop( listening)?", r"exit", r"quit", r"bye"],
                "cancel": [r"cancel( that)?", r"never ?mind", r"forget( it)?"],
                
                # Information intents
                "time": [r"what('s| is) the time", r"current time", r"tell me the time"],
                "date": [r"what('s| is) the date", r"what day is( it)?", r"current date"],
                "weather": [r"what('s| is) the weather( like)?", r"weather (forecast|today|tomorrow)"],
                "search": [r"search for (.+)", r"look up (.+)", r"find (.+)"],
                
                # Media intents
                "play": [r"play (.+)", r"start playing (.+)", r"listen to (.+)"],
                "pause": [r"pause( music| playback)?", r"stop playing"],
                "next": [r"next( track| song)?", r"skip( this)?"],
                "previous": [r"previous( track| song)?", r"go back"],
                
                # Timer/alarm intents
                "set_timer": [r"set( a)? timer for (.+)", r"timer for (.+)"],
                "set_alarm": [r"set( an)? alarm for (.+)", r"wake me up at (.+)"],
                "check_timer": [r"how much time (left|remaining)", r"check timer"],
                
                # System control intents
                "volume_up": [r"(turn|volume) up", r"increase volume", r"louder"],
                "volume_down": [r"(turn|volume) down", r"decrease volume", r"quieter"],
                "mute": [r"mute( volume)?", r"silence"],
                
                # Fallback intent
                "unknown": [r".*"]  # Match anything as unknown intent
            }
    
    def parse(self, text):
        """
        Parse text to determine intent and extract entities.
        
        Args:
            text (str): Text to parse
            
        Returns:
            dict: Intent information with intent name, confidence, and entities
        """
        if not text:
            return {
                "intent": "unknown",
                "confidence": 0.0,
                "entities": {},
                "text": text
            }
        
        # Normalize text
        normalized_text = text.lower().strip()
        
        # Check each intent pattern
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                match = re.match(pattern, normalized_text, re.IGNORECASE)
                if match:
                    # Extract entities from regex groups
                    entities = {}
                    for i, group in enumerate(match.groups()):
                        if group:
                            entities[f"entity_{i+1}"] = group
                    
                    # Calculate confidence based on specificity of match
                    match_length = match.end() - match.start()
                    text_length = len(normalized_text)
                    confidence = match_length / text_length if text_length > 0 else 0
                    
                    # Boost confidence for more specific intents
                    if intent != "unknown":
                        confidence *= 1.5
                        confidence = min(confidence, 1.0)
                    
                    return {
                        "intent": intent,
                        "confidence": confidence,
                        "entities": entities,
                        "text": text
                    }
        
        # Fallback to unknown intent
        return {
            "intent": "unknown",
            "confidence": 0.1,
            "entities": {},
            "text": text
        }
    
    def add_intent_pattern(self, intent, pattern):
        """
        Add a new pattern for an intent.
        
        Args:
            intent (str): Intent name
            pattern (str): Regex pattern for the intent
        """
        if intent not in self.intent_patterns:
            self.intent_patterns[intent] = []
        
        self.intent_patterns[intent].append(pattern)
        logger.info(f"Added pattern for intent '{intent}': {pattern}")
    
    def remove_intent_pattern(self, intent, pattern=None):
        """
        Remove a pattern or all patterns for an intent.
        
        Args:
            intent (str): Intent name
            pattern (str, optional): Specific pattern to remove, or None to remove all
        """
        if intent not in self.intent_patterns:
            logger.warning(f"Intent '{intent}' not found")
            return
        
        if pattern is None:
            self.intent_patterns[intent] = []
            logger.info(f"Removed all patterns for intent '{intent}'")
        elif pattern in self.intent_patterns[intent]:
            self.intent_patterns[intent].remove(pattern)
            logger.info(f"Removed pattern for intent '{intent}': {pattern}")
        else:
            logger.warning(f"Pattern not found for intent '{intent}': {pattern}")


class ContextManager:
    """Maintains conversation context for natural interactions."""
    
    def __init__(self, context_timeout=300):
        """
        Initialize the context manager.
        
        Args:
            context_timeout (int): Seconds before context expires
        """
        self.context = {}
        self.context_timeout = context_timeout
        self.last_update = datetime.datetime.now()
    
    def update_context(self, key, value):
        """
        Update a context value.
        
        Args:
            key (str): Context key
            value (any): Context value
        """
        self.context[key] = value
        self.last_update = datetime.datetime.now()
        logger.debug(f"Updated context: {key}={value}")
    
    def get_context(self, key, default=None):
        """
        Get a context value.
        
        Args:
            key (str): Context key
            default (any): Default value if key not found
            
        Returns:
            any: Context value or default
        """
        self._check_timeout()
        return self.context.get(key, default)
    
    def clear_context(self, key=None):
        """
        Clear context for a key or all context.
        
        Args:
            key (str, optional): Specific key to clear, or None to clear all
        """
        if key is None:
            self.context = {}
            logger.debug("Cleared all context")
        elif key in self.context:
            del self.context[key]
            logger.debug(f"Cleared context: {key}")
    
    def _check_timeout(self):
        """Check if context has timed out and clear if needed."""
        now = datetime.datetime.now()
        elapsed = (now - self.last_update).total_seconds()
        
        if elapsed > self.context_timeout:
            self.context = {}
            self.last_update = now
            logger.debug("Context timed out and was cleared")
    
    def get_all_context(self):
        """
        Get all current context.
        
        Returns:
            dict: All context values
        """
        self._check_timeout()
        return self.context.copy()


class Skill:
    """Base class for all assistant skills."""
    
    def __init__(self, command_processor):
        """
        Initialize the skill.
        
        Args:
            command_processor (CommandProcessor): Reference to command processor
        """
        self.command_processor = command_processor
        self.name = self.__class__.__name__
        self.intents = []
        self.register_intents()
    
    def register_intents(self):
        """Register intents handled by this skill. Override in subclasses."""
        pass
    
    def handle(self, intent_data):
        """
        Handle an intent. Override in subclasses.
        
        Args:
            intent_data (dict): Intent data from parser
            
        Returns:
            dict: Response data
        """
        return {
            "success": False,
            "message": f"Skill {self.name} does not implement handling for {intent_data['intent']}",
            "data": {}
        }


class SystemSkill(Skill):
    """System control and information skill."""
    
    def register_intents(self):
        """Register system intents."""
        self.intents = ["help", "stop", "cancel"]
        
        # Register patterns for these intents
        for intent in self.intents:
            if intent == "help":
                self.command_processor.intent_parser.add_intent_pattern(
                    "help", r"(what can you do|help( me)?|show( me)? commands|list commands)"
                )
    
    def handle(self, intent_data):
        """Handle system intents."""
        intent = intent_data["intent"]
        
        if intent == "help":
            # Get all available commands from registered skills
            available_commands = {}
            for skill in self.command_processor.skills.values():
                for intent in skill.intents:
                    if intent not in available_commands:
                        patterns = self.command_processor.intent_parser.intent_patterns.get(intent, [])
                        if patterns:
                            # Use the first pattern as an example
                            available_commands[intent] = patterns[0].replace(r"(.+)", "<item>")
            
            return {
                "success": True,
                "message": "Here are the commands I understand:",
                "data": {
                    "commands": available_commands
                }
            }
        
        elif intent == "stop":
            return {
                "success": True,
                "message": "Stopping assistant",
                "data": {
                    "action": "stop"
                }
            }
        
        elif intent == "cancel":
            # Clear current context
            self.command_processor.context_manager.clear_context()
            
            return {
                "success": True,
                "message": "Cancelled current operation",
                "data": {}
            }
        
        return {
            "success": False,
            "message": f"Unhandled system intent: {intent}",
            "data": {}
        }


class TimeSkill(Skill):
    """Time and date information skill."""
    
    def register_intents(self):
        """Register time intents."""
        self.intents = ["time", "date"]
    
    def handle(self, intent_data):
        """Handle time intents."""
        intent = intent_data["intent"]
        now = datetime.datetime.now()
        
        if intent == "time":
            time_str = now.strftime("%I:%M %p")
            return {
                "success": True,
                "message": f"The current time is {time_str}",
                "data": {
                    "time": time_str,
                    "hour": now.hour,
                    "minute": now.minute
                }
            }
        
        elif intent == "date":
            date_str = now.strftime("%A, %B %d, %Y")
            return {
                "success": True,
                "message": f"Today is {date_str}",
                "data": {
                    "date": date_str,
                    "day": now.day,
                    "month": now.month,
                    "year": now.year,
                    "weekday": now.strftime("%A")
                }
            }
        
        return {
            "success": False,
            "message": f"Unhandled time intent: {intent}",
            "data": {}
        }


class TimerSkill(Skill):
    """Timer and alarm skill."""
    
    def register_intents(self):
        """Register timer intents."""
        self.intents = ["set_timer", "check_timer", "set_alarm"]
    
    def handle(self, intent_data):
        """Handle timer intents."""
        intent = intent_data["intent"]
        
        if intent == "set_timer":
            # Extract duration from entities
            duration_text = intent_data["entities"].get("entity_1", "")
            
            if not duration_text:
                return {
                    "success": False,
                    "message": "I didn't catch how long to set the timer for",
                    "data": {}
                }
            
            # Parse duration (simple implementation)
            minutes = 0
            seconds = 0
            
            # Look for patterns like "5 minutes and 30 seconds", "5 minutes", "30 seconds"
            min_match = re.search(r"(\d+)\s*min(ute)?s?", duration_text)
            sec_match = re.search(r"(\d+)\s*sec(ond)?s?", duration_text)
            
            if min_match:
                minutes = int(min_match.group(1))
            if sec_match:
                seconds = int(sec_match.group(1))
            
            # If no specific units found, try to interpret as minutes or seconds
            if not min_match and not sec_match:
                try:
                    # Assume it's just a number of minutes
                    minutes = int(re.search(r"(\d+)", duration_text).group(1))
                except (AttributeError, ValueError):
                    return {
                        "success": False,
                        "message": "I couldn't understand that duration",
                        "data": {}
                    }
            
            total_seconds = minutes * 60 + seconds
            
            # Store timer in context
            self.command_processor.context_manager.update_context(
                "timer", {
                    "start_time": datetime.datetime.now(),
                    "duration": total_seconds,
                    "end_time": datetime.datetime.now() + datetime.timedelta(seconds=total_seconds)
                }
            )
            
            return {
                "success": True,
                "message": f"Timer set for {minutes} minutes and {seconds} seconds",
                "data": {
                    "action": "set_timer",
                    "minutes": minutes,
                    "seconds": seconds,
                    "total_seconds": total_seconds
                }
            }
        
        elif intent == "check_timer":
            # Get timer from context
            timer = self.command_processor.context_manager.get_context("timer")
            
            if not timer:
                return {
                    "success": False,
                    "message": "No timer is currently set",
                    "data": {}
                }
            
            # Calculate remaining time
            now = datetime.datetime.now()
            end_time = timer["end_time"]
            
            if now >= end_time:
                return {
                    "success": True,
                    "message": "The timer has finished",
                    "data": {
                        "remaining": 0,
                        "status": "finished"
                    }
                }
            
            remaining = (end_time - now).total_seconds()
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            
            return {
                "success": True,
                "message": f"Timer has {minutes} minutes and {seconds} seconds remaining",
                "data": {
                    "remaining": remaining,
                    "minutes": minutes,
                    "seconds": seconds,
                    "status": "running"
                }
            }
        
        elif intent == "set_alarm":
            # Extract time from entities
            time_text = intent_data["entities"].get("entity_1", "")
            
            if not time_text:
                return {
                    "success": False,
                    "message": "I didn't catch what time to set the alarm for",
                    "data": {}
                }
            
            # Parse time (simple implementation)
            try:
                # Try to parse various time formats
                formats = ["%I:%M %p", "%H:%M", "%I %p"]
                parsed_time = None
                
                for fmt in formats:
                    try:
                        parsed_time = datetime.datetime.strptime(time_text, fmt).time()
                        break
                    except ValueError:
                        continue
                
                if not parsed_time:
                    # Try to handle special cases like "6 in the morning"
                    morning_match = re.search(r"(\d+)\s*(in the morning|am)", time_text, re.IGNORECASE)
                    evening_match = re.search(r"(\d+)\s*(in the evening|pm)", time_text, re.IGNORECASE)
                    
                    if morning_match:
                        hour = int(morning_match.group(1))
                        parsed_time = datetime.time(hour=hour)
                    elif evening_match:
                        hour = int(evening_match.group(1))
                        if hour < 12:
                            hour += 12
                        parsed_time = datetime.time(hour=hour)
                
                if not parsed_time:
                    return {
                        "success": False,
                        "message": "I couldn't understand that time format",
                        "data": {}
                    }
                
                # Create alarm datetime (for today)
                now = datetime.datetime.now()
                alarm_datetime = datetime.datetime.combine(now.date(), parsed_time)
                
                # If the time has already passed today, set for tomorrow
                if alarm_datetime < now:
                    alarm_datetime += datetime.timedelta(days=1)
                
                # Store alarm in context
                self.command_processor.context_manager.update_context(
                    "alarm", {
                        "time": parsed_time,
                        "datetime": alarm_datetime
                    }
                )
                
                time_str = alarm_datetime.strftime("%I:%M %p")
                return {
                    "success": True,
                    "message": f"Alarm set for {time_str}",
                    "data": {
                        "action": "set_alarm",
                        "time": time_str,
                        "hour": parsed_time.hour,
                        "minute": parsed_time.minute,
                        "timestamp": alarm_datetime.timestamp()
                    }
                }
                
            except Exception as e:
                logger.error(f"Error parsing alarm time: {e}")
                return {
                    "success": False,
                    "message": "I had trouble setting that alarm",
                    "data": {}
                }
        
        return {
            "success": False,
            "message": f"Unhandled timer intent: {intent}",
            "data": {}
        }


class CommandRouter:
    """Routes commands to appropriate skill handlers."""
    
    def __init__(self, command_processor):
        """
        Initialize the command router.
        
        Args:
            command_processor (CommandProcessor): Reference to command processor
        """
        self.command_processor = command_processor
        self.intent_to_skill = {}
    
    def register_skill(self, skill):
        """
        Register a skill and its intents.
        
        Args:
            skill (Skill): Skill instance to register
        """
        for intent in skill.intents:
            self.intent_to_skill[intent] = skill
        
        logger.info(f"Registered skill {skill.name} for intents: {skill.intents}")
    
    def route_command(self, intent_data):
        """
        Route a command to the appropriate skill.
        
        Args:
            intent_data (dict): Intent data from parser
            
        Returns:
            dict: Response from skill handler
        """
        intent = intent_data["intent"]
        
        if intent in self.intent_to_skill:
            skill = self.intent_to_skill[intent]
            logger.info(f"Routing intent '{intent}' to skill '{skill.name}'")
            return skill.handle(intent_data)
        else:
            logger.warning(f"No skill registered for intent '{intent}'")
            return {
                "success": False,
                "message": "I'm not sure how to help with that",
                "data": {}
            }


class CommandProcessor:
    """Main command processing module that coordinates intent parsing, context management, and command routing."""
    
    def __init__(self, custom_skills_dir=None):
        """
        Initialize the command processor.
        
        Args:
            custom_skills_dir (str): Directory path for custom skills
        """
        self.intent_parser = IntentParser()
        self.context_manager = ContextManager()
        self.command_router = CommandRouter(self)
        self.skills = {}
        self.custom_skills_dir = custom_skills_dir
        
        # Load built-in skills
        self._load_builtin_skills()
        
        # Load custom skills if directory provided
        if custom_skills_dir:
            self._load_custom_skills()
    
    def _load_builtin_skills(self):
        """Load built-in skills."""
        # Initialize built-in skills
        builtin_skills = [
            SystemSkill(self),
            TimeSkill(self),
            TimerSkill(self)
        ]
        
        # Register each skill
        for skill in builtin_skills:
            self.register_skill(skill)
    
    def _load_custom_skills(self):
        """Load custom skills from directory."""
        if not os.path.exists(self.custom_skills_dir):
            logger.warning(f"Custom skills directory not found: {self.custom_skills_dir}")
            return
        
        try:
            # Add custom skills directory to path
            import sys
            if self.custom_skills_dir not in sys.path:
                sys.path.append(os.path.dirname(self.custom_skills_dir))
            
            # Get the package name
            package_name = os.path.basename(self.custom_skills_dir)
            
            # Import all modules in the package
            package = importlib.import_module(package_name)
            for _, name, is_pkg in pkgutil.iter_modules(package.__path__):
                if not is_pkg:
                    # Import the module
                    module = importlib.import_module(f"{package_name}.{name}")
                    
                    # Find all Skill subclasses in the module
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and 
                            issubclass(attr, Skill) and 
                            attr is not Skill):
                            
                            # Initialize and register the skill
                            skill = attr(self)
                            self.register_skill(skill)
        
        except Exception as e:
            logger.error(f"Error loading custom skills: {e}")
    
    def register_skill(self, skill):
        """
        Register a skill with the command processor.
        
        Args:
            skill (Skill): Skill instance to register
        """
        self.skills[skill.name] = skill
        self.command_router.register_skill(skill)
        logger.info(f"Registered skill: {skill.name}")
    
    def process_command(self, text):
        """
        Process a command from text.
        
        Args:
            text (str): Command text to process
            
        Returns:
            dict: Processing result with response and action data
        """
        # Parse intent
        intent_data = self.intent_parser.parse(text)
        logger.info(f"Parsed intent: {intent_data['intent']} (confidence: {intent_data['confidence']:.2f})")
        
        # Route to appropriate skill
        response = self.command_router.route_command(intent_data)
        
        # Add metadata to response
        response["intent"] = intent_data["intent"]
        response["text"] = text
        response["timestamp"] = datetime.datetime.now().isoformat()
        
        return response
    
    def add_custom_intent(self, intent_name, patterns, skill_class):
        """
        Add a custom intent and associate it with a skill.
        
        Args:
            intent_name (str): Name of the intent
            patterns (list): List of regex patterns for the intent
            skill_class (class): Skill class to handle the intent
        """
        # Add patterns to intent parser
        for pattern in patterns:
            self.intent_parser.add_intent_pattern(intent_name, pattern)
        
        # Check if skill is already registered
        skill_name = skill_class.__name__
        if skill_name in self.skills:
            # Add intent to existing skill
            skill = self.skills[skill_name]
            if intent_name not in skill.intents:
                skill.intents.append(intent_name)
                self.command_router.intent_to_skill[intent_name] = skill
                logger.info(f"Added intent '{intent_name}' to existing skill '{skill_name}'")
        else:
            # Create and register new skill
            skill = skill_class(self)
            if intent_name not in skill.intents:
                skill.intents.append(intent_name)
            self.register_skill(skill)
            logger.info(f"Created new skill '{skill_name}' for intent '{intent_name}'")


# Example usage
if __name__ == "__main__":
    # Create command processor
    processor = CommandProcessor()
    
    # Process some example commands
    test_commands = [
        "what time is it",
        "what's the date today",
        "set a timer for 5 minutes",
        "how much time is left on my timer",
        "help me",
        "what can you do",
        "cancel that",
        "unknown command"
    ]
    
    for command in test_commands:
        print(f"\nProcessing: '{command}'")
        result = processor.process_command(command)
        print(f"Intent: {result['intent']}")
        print(f"Success: {result['success']}")
        print(f"Response: {result['message']}")
        if result['data']:
            print(f"Data: {result['data']}")
