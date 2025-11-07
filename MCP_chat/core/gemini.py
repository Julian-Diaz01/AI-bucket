import google.generativeai as genai
from typing import Optional, List, Dict, Any
import json

# Try to import protobuf types for proper Part creation
try:
    from google.generativeai import protos
    HAS_PROTOS = True
except ImportError:
    HAS_PROTOS = False


class Gemini:
    def __init__(self, model: str, api_key: str):
        genai.configure(api_key=api_key)
        self.model = model
        self.client = genai.GenerativeModel(model)

    def add_user_message(self, messages: list, message):
        """Add a user message to the conversation history."""
        try:
            if isinstance(message, list):
                # List of tool result parts (function responses)
                # Ensure all parts are properly formatted
                formatted_parts = []
                for part in message:
                    if isinstance(part, dict):
                        # Handle function responses - ensure proper format
                        if "functionResponse" in part:
                            func_resp = part["functionResponse"]
                            response_value = func_resp.get("response", {})
                            
                            # FunctionResponse.response expects a struct (dict-like)
                            # Wrap strings and primitives in a dict
                            if isinstance(response_value, str):
                                response_value = {"result": response_value}
                            elif isinstance(response_value, (int, float, bool)):
                                response_value = {"result": response_value}
                            elif isinstance(response_value, list):
                                response_value = {"result": response_value}
                            elif response_value is None:
                                response_value = {}
                            elif not isinstance(response_value, dict):
                                response_value = {"result": str(response_value)}
                            
                            formatted_parts.append({
                                "function_response": {
                                    "name": func_resp.get("name", ""),
                                    "response": response_value
                                }
                            })
                        elif "function_response" in part:
                            # Already in snake_case, just ensure response is valid
                            func_resp = part["function_response"]
                            response_value = func_resp.get("response", {})
                            
                            # FunctionResponse.response expects a struct (dict-like)
                            # Wrap strings and primitives in a dict
                            if isinstance(response_value, str):
                                response_value = {"result": response_value}
                                part["function_response"]["response"] = response_value
                            elif isinstance(response_value, (int, float, bool)):
                                response_value = {"result": response_value}
                                part["function_response"]["response"] = response_value
                            elif isinstance(response_value, list):
                                response_value = {"result": response_value}
                                part["function_response"]["response"] = response_value
                            elif response_value is None:
                                part["function_response"]["response"] = {}
                            elif not isinstance(response_value, dict):
                                response_value = {"result": str(response_value)}
                                part["function_response"]["response"] = response_value
                            
                            formatted_parts.append(part)
                        else:
                            formatted_parts.append(part)
                    else:
                        formatted_parts.append({"text": str(part)})
                
                user_message = {
                    "role": "user",
                    "parts": formatted_parts
                }
            elif isinstance(message, dict):
                # Single tool result part or message dict
                if "functionResponse" in message:
                    # Convert camelCase to snake_case and ensure response is valid
                    func_resp = message["functionResponse"]
                    response_value = func_resp.get("response", {})
                    
                    # FunctionResponse.response expects a struct (dict-like)
                    # Wrap strings and primitives in a dict
                    if isinstance(response_value, str):
                        response_value = {"result": response_value}
                    elif isinstance(response_value, (int, float, bool)):
                        response_value = {"result": response_value}
                    elif isinstance(response_value, list):
                        response_value = {"result": response_value}
                    elif response_value is None:
                        response_value = {}
                    elif not isinstance(response_value, dict):
                        response_value = {"result": str(response_value)}
                    
                    user_message = {
                        "role": "user",
                        "parts": [{
                            "function_response": {
                                "name": func_resp.get("name", ""),
                                "response": response_value
                            }
                        }]
                    }
                elif "function_response" in message:
                    # Already in correct format, ensure response is valid
                    func_resp = message["function_response"]
                    response_value = func_resp.get("response", {})
                    
                    # FunctionResponse.response expects a struct (dict-like)
                    # Wrap strings and primitives in a dict
                    if isinstance(response_value, str):
                        response_value = {"result": response_value}
                        message["function_response"]["response"] = response_value
                    elif isinstance(response_value, (int, float, bool)):
                        response_value = {"result": response_value}
                        message["function_response"]["response"] = response_value
                    elif isinstance(response_value, list):
                        response_value = {"result": response_value}
                        message["function_response"]["response"] = response_value
                    elif response_value is None:
                        message["function_response"]["response"] = {}
                    elif not isinstance(response_value, dict):
                        response_value = {"result": str(response_value)}
                        message["function_response"]["response"] = response_value
                    
                    user_message = {
                        "role": "user",
                        "parts": [message]
                    }
                elif "parts" in message:
                    user_message = {
                        "role": "user",
                        "parts": message.get("parts", [])
                    }
                else:
                    # Plain text message
                    user_message = {
                        "role": "user",
                        "parts": [{"text": str(message)}]
                    }
            else:
                user_message = {
                    "role": "user",
                    "parts": [{"text": str(message)}]
                }
            messages.append(user_message)
        except Exception as e:
            print(f"[ERROR] Gemini.add_user_message: Error adding user message: {type(e).__name__}: {e}")
            # Fallback to simple text message
            messages.append({
                "role": "user",
                "parts": [{"text": str(message)}]
            })

    def add_assistant_message(self, messages: list, message):
        """Add an assistant message to the conversation history."""
        if hasattr(message, 'parts'):
            # Response object from Gemini
            parts = []
            for part in message.parts:
                if hasattr(part, 'text') and part.text:
                    parts.append({"text": part.text})
                elif hasattr(part, 'function_call'):
                    # Store in snake_case format for compatibility with history
                    func_call = part.function_call
                    parts.append({
                        "function_call": {
                            "name": func_call.name if hasattr(func_call, 'name') else "",
                            "args": dict(func_call.args) if hasattr(func_call, 'args') and func_call.args else {}
                        }
                    })
            assistant_message = {
                "role": "model",
                "parts": parts
            }
        elif isinstance(message, dict):
            assistant_message = message
        else:
            assistant_message = {
                "role": "model",
                "parts": [{"text": str(message)}]
            }
        messages.append(assistant_message)

    def text_from_message(self, message) -> str:
        """Extract text content from a Gemini response message."""
        if hasattr(message, 'parts'):
            text_parts = []
            for part in message.parts:
                if hasattr(part, 'text') and part.text:
                    text_parts.append(part.text)
            return "\n".join(text_parts)
        elif isinstance(message, dict):
            text_parts = []
            for part in message.get("parts", []):
                if isinstance(part, dict) and "text" in part:
                    text_parts.append(part["text"])
            return "\n".join(text_parts)
        return str(message)

    def _clean_schema_for_gemini(self, schema: Any) -> Dict[str, Any]:
        """Remove fields from JSON Schema that Gemini doesn't support."""
        try:
            # Debug: Log the input type
            schema_type = type(schema).__name__
            if schema_type not in ['dict', 'str', 'NoneType']:
                print(f"[DEBUG] _clean_schema_for_gemini: Unexpected schema type: {schema_type}, value: {str(schema)[:100]}")
            
            # Handle string schemas (JSON strings from MCP)
            if isinstance(schema, str):
                try:
                    schema = json.loads(schema)
                    print(f"[DEBUG] _clean_schema_for_gemini: Parsed JSON string schema")
                except json.JSONDecodeError as e:
                    print(f"[ERROR] _clean_schema_for_gemini: Failed to parse JSON string schema: {e}")
                    print(f"[DEBUG] Schema string (first 200 chars): {schema[:200]}")
                    return {}
                except TypeError as e:
                    print(f"[ERROR] _clean_schema_for_gemini: TypeError parsing schema: {e}, type: {type(schema)}")
                    return {}
                except Exception as e:
                    print(f"[ERROR] _clean_schema_for_gemini: Unexpected error parsing schema: {type(e).__name__}: {e}")
                    return {}
            
            # If it's not a dict after parsing, return empty dict
            if not isinstance(schema, dict):
                if schema is None:
                    return {}
                print(f"[WARNING] _clean_schema_for_gemini: Schema is not a dict after parsing. Type: {type(schema).__name__}, Value: {str(schema)[:100]}")
                return {}
            
            # Fields that Gemini supports in function declaration parameters
            allowed_fields = {
                "type", "properties", "required", "items", "enum", 
                "description", "format", "minimum", "maximum", "pattern"
            }
            
            cleaned = {}
            
            # Final safety check - ensure schema is a dict and has items method
            if not isinstance(schema, dict):
                print(f"[ERROR] _clean_schema_for_gemini: Schema is not a dict before iteration. Type: {type(schema).__name__}")
                return {}
            
            if not hasattr(schema, 'items'):
                print(f"[ERROR] _clean_schema_for_gemini: Schema does not have 'items' method. Type: {type(schema).__name__}")
                return {}
            
            try:
                for key, value in schema.items():
                    try:
                        if key in allowed_fields:
                            if key == "properties":
                                # Handle properties - value might be a dict or string
                                if isinstance(value, str):
                                    try:
                                        value = json.loads(value)
                                    except (json.JSONDecodeError, TypeError) as e:
                                        print(f"[WARNING] _clean_schema_for_gemini: Failed to parse properties value: {e}")
                                        value = {}
                                
                                if isinstance(value, dict):
                                    # Recursively clean nested properties
                                    cleaned_props = {}
                                    try:
                                        for prop_key, prop_value in value.items():
                                            try:
                                                cleaned_props[prop_key] = self._clean_schema_for_gemini(prop_value)
                                            except Exception as e:
                                                print(f"[ERROR] _clean_schema_for_gemini: Error cleaning property '{prop_key}': {type(e).__name__}: {e}")
                                                # Continue with other properties
                                                cleaned_props[prop_key] = {}
                                    except AttributeError as e:
                                        print(f"[ERROR] _clean_schema_for_gemini: AttributeError iterating properties: {e}")
                                    except Exception as e:
                                        print(f"[ERROR] _clean_schema_for_gemini: Unexpected error processing properties: {type(e).__name__}: {e}")
                                    
                                    if cleaned_props:
                                        cleaned[key] = cleaned_props
                                # If properties is not a dict after parsing, skip it
                            elif key == "items":
                                # Handle items - value might be a dict or string
                                if isinstance(value, str):
                                    try:
                                        value = json.loads(value)
                                    except (json.JSONDecodeError, TypeError) as e:
                                        print(f"[WARNING] _clean_schema_for_gemini: Failed to parse items value: {e}")
                                        value = {}
                                if isinstance(value, dict):
                                    # Recursively clean items schema
                                    try:
                                        cleaned[key] = self._clean_schema_for_gemini(value)
                                    except Exception as e:
                                        print(f"[ERROR] _clean_schema_for_gemini: Error cleaning items: {type(e).__name__}: {e}")
                                        # Skip items if cleaning fails
                                # If items is not a dict after parsing, skip it
                            else:
                                cleaned[key] = value
                    except Exception as e:
                        print(f"[ERROR] _clean_schema_for_gemini: Error processing key '{key}': {type(e).__name__}: {e}")
                        # Continue with next key
                        continue
            except AttributeError as e:
                print(f"[ERROR] _clean_schema_for_gemini: AttributeError calling .items(): {e}")
                return {}
            except TypeError as e:
                print(f"[ERROR] _clean_schema_for_gemini: TypeError: {e}")
                return {}
            except Exception as e:
                print(f"[ERROR] _clean_schema_for_gemini: Unexpected error: {type(e).__name__}: {e}")
                import traceback
                return {}
            
            return cleaned
        except Exception as e:
            print(f"[ERROR] _clean_schema_for_gemini: Fatal error: {type(e).__name__}: {e}")
            import traceback
            return {}

    def _convert_tools_to_gemini_format(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert MCP tools to Gemini function declaration format."""
        function_declarations = []
        
        if not tools:
            return []
        
        
        for i, tool in enumerate(tools):
            try:
                tool_name = tool.get("name", f"unknown_tool_{i}")
                
                if not isinstance(tool, dict):
                    print(f"[ERROR] _convert_tools_to_gemini_format: Tool {i} is not a dict, type: {type(tool).__name__}")
                    continue
                
                input_schema = tool.get("input_schema", {})
                
                # Handle case where input_schema might be None
                if input_schema is None:
                    print(f"[WARNING] _convert_tools_to_gemini_format: Tool '{tool_name}' has None input_schema")
                    input_schema = {}
                
                # Clean the schema to remove unsupported fields like "title"
                try:
                    cleaned_schema = self._clean_schema_for_gemini(input_schema)
                except Exception as e:
                    print(f"[ERROR] _convert_tools_to_gemini_format: Error cleaning schema for tool '{tool_name}': {type(e).__name__}: {e}")
                    import traceback
                    cleaned_schema = {}
                
                # Ensure cleaned_schema is a dict (fallback to empty dict if cleaning failed)
                if not isinstance(cleaned_schema, dict):
                    print(f"[WARNING] _convert_tools_to_gemini_format: Tool '{tool_name}' cleaned_schema is not a dict, type: {type(cleaned_schema).__name__}")
                    cleaned_schema = {}
                
                if "name" not in tool:
                    print(f"[ERROR] _convert_tools_to_gemini_format: Tool {i} missing 'name' field")
                    continue
                
                function_decl = {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": cleaned_schema
                }
                function_declarations.append(function_decl)
            except KeyError as e:
                print(f"[ERROR] _convert_tools_to_gemini_format: Missing key in tool {i}: {e}")
                continue
            except Exception as e:
                print(f"[ERROR] _convert_tools_to_gemini_format: Unexpected error processing tool {i}: {type(e).__name__}: {e}")
                import traceback
                continue
        
        return function_declarations

    def chat(
        self,
        messages: List[Dict[str, Any]],
        system: Optional[str] = None,
        temperature: float = 1.0,
        stop_sequences: List[str] = [],
        tools: Optional[List[Dict[str, Any]]] = None,
        thinking: bool = False,
        thinking_budget: int = 1024,
    ):
        """Send a chat request to Gemini."""
        # Convert messages to Gemini format
        gemini_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                role = msg.get("role", "user")
                if role == "assistant":
                    role = "model"
                
                parts = msg.get("parts", [])
                if not parts and "content" in msg:
                    # Handle Anthropic-style content
                    content = msg["content"]
                    if isinstance(content, str):
                        parts = [{"text": content}]
                    elif isinstance(content, list):
                        parts = []
                        for block in content:
                            if isinstance(block, dict):
                                if block.get("type") == "text":
                                    parts.append({"text": block.get("text", "")})
                                elif block.get("type") == "tool_result":
                                    # Convert tool result to function response
                                    parts.append({
                                        "functionResponse": {
                                            "name": block.get("tool_use_id", ""),
                                            "response": {
                                                "result": block.get("content", "")
                                            }
                                        }
                                    })
                            else:
                                parts.append({"text": str(block)})
                
                # Process parts to ensure proper format for Gemini
                # When using start_chat(history=...), function calls need snake_case format
                processed_parts = []
                for part in parts:
                    if isinstance(part, dict):
                        # Handle function calls - convert camelCase to snake_case if needed
                        if "functionCall" in part:
                            # Convert camelCase to snake_case for history compatibility
                            func_call = part["functionCall"]
                            processed_parts.append({
                                "function_call": {
                                    "name": func_call.get("name", ""),
                                    "args": func_call.get("args", {})
                                }
                            })
                        elif "function_call" in part:
                            # Already in correct format
                            processed_parts.append(part)
                        # Handle function responses
                        elif "functionResponse" in part:
                            # Convert camelCase to snake_case
                            func_resp = part["functionResponse"]
                            response_value = func_resp.get("response", {})
                            
                            # FunctionResponse.response expects a struct (dict-like)
                            # Wrap strings and primitives in a dict
                            if isinstance(response_value, str):
                                # Wrap string in a struct
                                response_value = {"result": response_value}
                            elif isinstance(response_value, (int, float, bool)):
                                # Wrap primitive types
                                response_value = {"result": response_value}
                            elif isinstance(response_value, list):
                                # Lists are fine, but wrap for consistency
                                response_value = {"result": response_value}
                            elif response_value is None:
                                response_value = {}
                            elif not isinstance(response_value, dict):
                                # Convert other types to string and wrap
                                response_value = {"result": str(response_value)}
                            
                            processed_parts.append({
                                "function_response": {
                                    "name": func_resp.get("name", ""),
                                    "response": response_value
                                }
                            })
                        elif "function_response" in part:
                            # Already in correct format, but ensure response is properly formatted
                            func_resp = part["function_response"]
                            response_value = func_resp.get("response", {})
                            
                            # FunctionResponse.response expects a struct (dict-like)
                            # Wrap strings and primitives in a dict
                            if isinstance(response_value, str):
                                # Wrap string in a struct
                                response_value = {"result": response_value}
                                part["function_response"]["response"] = response_value
                            elif isinstance(response_value, (int, float, bool)):
                                # Wrap primitive types
                                response_value = {"result": response_value}
                                part["function_response"]["response"] = response_value
                            elif isinstance(response_value, list):
                                # Lists are fine, but wrap for consistency
                                response_value = {"result": response_value}
                                part["function_response"]["response"] = response_value
                            elif response_value is None:
                                part["function_response"]["response"] = {}
                            elif not isinstance(response_value, dict):
                                # Convert other types to string and wrap
                                response_value = {"result": str(response_value)}
                                part["function_response"]["response"] = response_value
                            
                            processed_parts.append(part)
                        elif "text" in part:
                            # Text part - keep as is
                            processed_parts.append(part)
                        else:
                            # Unknown format - try to convert to text
                            processed_parts.append({"text": str(part)})
                    else:
                        # Not a dict - convert to text
                        processed_parts.append({"text": str(part)})
                
                # Ensure parts is a list
                if not processed_parts:
                    processed_parts = [{"text": ""}]
                
                gemini_messages.append({
                    "role": role,
                    "parts": processed_parts
                })
            else:
                # Fallback for other message types
                gemini_messages.append({
                    "role": "user",
                    "parts": [{"text": str(msg)}]
                })

        # Prepare generation config
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=8192,
        )
        
        if stop_sequences:
            generation_config.stop_sequences = stop_sequences

        # Prepare tools if provided
        tools_config = None
        if tools:
            function_declarations = self._convert_tools_to_gemini_format(tools)
            tools_config = [{"function_declarations": function_declarations}]

        # Handle system prompt - Gemini supports system_instruction parameter
        system_instruction = system if system else None
        
        # Create model with tools and system instruction if needed
        model_kwargs = {
            "model_name": self.model,
            "generation_config": generation_config
        }
        
        if system_instruction:
            model_kwargs["system_instruction"] = system_instruction
        
        if tools_config:
            model_kwargs["tools"] = tools_config
        
        model = genai.GenerativeModel(**model_kwargs)
        
        # Prepare the chat history (all messages except the last one)
        history = gemini_messages[:-1] if len(gemini_messages) > 1 else []
        
        # Get the last message to send
        last_message_parts = gemini_messages[-1]["parts"] if gemini_messages else [{"text": ""}]
        
        # Convert function_response to proper format for sending
        # The SDK's send_message expects parts in a specific format
        # Function responses need to be converted using the SDK's content types
        converted_parts = []
        for part in last_message_parts:
            if isinstance(part, dict):
                if "function_response" in part:
                    # Function responses need special handling
                    func_resp = part["function_response"]
                    response_value = func_resp.get("response", {})
                    
                    # FunctionResponse.response expects a struct_pb2.Struct (dict-like)
                    # If response_value is a string, we need to wrap it properly
                    # For protobuf struct, strings should be in struct format
                    if isinstance(response_value, str):
                        # Wrap string in a struct with a "result" or "content" key
                        # Or use the string directly as struct value
                        response_value = {"result": response_value}
                    elif isinstance(response_value, (int, float, bool)):
                        # Wrap primitive types
                        response_value = {"result": response_value}
                    elif isinstance(response_value, list):
                        # Lists are fine as-is for struct
                        response_value = {"result": response_value}
                    elif response_value is None:
                        response_value = {}
                    elif not isinstance(response_value, dict):
                        # Convert other types to string and wrap
                        response_value = {"result": str(response_value)}
                    
                    # Ensure it's a dict at this point
                    if not isinstance(response_value, dict):
                        response_value = {"result": str(response_value)}
                    
                    # Try to use SDK's content types helper
                    try:
                        # Import content types helper
                        from google.generativeai.types import content_types
                        
                        # Create the function response dict in the format SDK expects
                        func_response_dict = {
                            "function_response": {
                                "name": func_resp.get("name", ""),
                                "response": response_value
                            }
                        }
                        
                        # Use SDK's to_part helper to convert
                        converted_part = content_types.to_part(func_response_dict)
                        converted_parts.append(converted_part)
                    except Exception as e:
                        print(f"[WARNING] Gemini.chat: Error using content_types.to_part: {type(e).__name__}: {e}")
                        # Fallback: try protobuf Part directly
                        try:
                            if HAS_PROTOS:
                                # Import struct_pb2 for proper struct creation
                                from google.protobuf import struct_pb2
                                
                                # Create a struct from the dict
                                struct_value = struct_pb2.Struct()
                                struct_value.update(response_value)
                                
                                proto_part = protos.Part(
                                    function_response=protos.FunctionResponse(
                                        name=func_resp.get("name", ""),
                                        response=struct_value
                                    )
                                )
                                converted_parts.append(proto_part)
                            else:
                                # Last resort: use dict but this might fail
                                print(f"[ERROR] Gemini.chat: Cannot create function response part, no protobuf available")
                                raise ValueError(f"Cannot format function response: {e}")
                        except Exception as e2:
                            print(f"[ERROR] Gemini.chat: Error creating protobuf Part: {type(e2).__name__}: {e2}")
                            import traceback
                            raise
                elif "function_call" in part:
                    # Function calls - convert to proper format
                    func_call = part["function_call"]
                    try:
                        from google.generativeai.types import content_types
                        func_call_dict = {
                            "function_call": {
                                "name": func_call.get("name", ""),
                                "args": func_call.get("args", {})
                            }
                        }
                        converted_part = content_types.to_part(func_call_dict)
                        converted_parts.append(converted_part)
                    except Exception as e:
                        print(f"[WARNING] Gemini.chat: Error converting function call: {e}")
                        # Keep as-is and let SDK handle it
                        converted_parts.append(part)
                else:
                    # Keep other parts as-is (text, etc.)
                    converted_parts.append(part)
            else:
                converted_parts.append(part)
        
        # Start chat with history
        if history:
            chat = model.start_chat(history=history)
        else:
            chat = model.start_chat()
        
        # Send the message
        try:
            response = chat.send_message(converted_parts)
        except Exception as e:
            import traceback
            raise
        
        return response

