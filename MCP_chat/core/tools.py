import json
from typing import Optional, Literal, List, Dict, Any
from mcp.types import CallToolResult, Tool, TextContent
from mcp_client import MCPClient


class ToolManager:
    @classmethod
    async def get_all_tools(cls, clients: dict[str, MCPClient]) -> list[Dict[str, Any]]:
        """Gets all tools from the provided clients."""
        tools = []
        
        if not clients:
            print(f"[WARNING] ToolManager.get_all_tools: No clients provided")
            return []
        
        for client_name, client in clients.items():
            try:
                tool_models = await client.list_tools()
                
                for i, t in enumerate(tool_models):
                    try:
                        tool_name = getattr(t, 'name', f'unknown_tool_{i}')
                        
                        # Handle inputSchema - it might be a string (JSON) or dict
                        input_schema = getattr(t, 'inputSchema', None)
                        input_schema_type = type(input_schema).__name__
                        
                        if isinstance(input_schema, str):
                            try:
                                input_schema = json.loads(input_schema)
                            except json.JSONDecodeError as e:
                                print(f"[ERROR] ToolManager.get_all_tools: Failed to parse JSON for tool '{tool_name}': {e}")
                                input_schema = {}
                            except TypeError as e:
                                print(f"[ERROR] ToolManager.get_all_tools: TypeError parsing JSON for tool '{tool_name}': {e}")
                                input_schema = {}
                            except Exception as e:
                                print(f"[ERROR] ToolManager.get_all_tools: Unexpected error parsing JSON for tool '{tool_name}': {type(e).__name__}: {e}")
                                input_schema = {}
                        elif input_schema is None:
                            print(f"[WARNING] ToolManager.get_all_tools: Tool '{tool_name}' has None inputSchema")
                            input_schema = {}
                        elif not isinstance(input_schema, dict):
                            print(f"[WARNING] ToolManager.get_all_tools: Tool '{tool_name}' inputSchema is not dict or string, type: {input_schema_type}")
                            # Try to convert if possible
                            try:
                                if hasattr(input_schema, '__dict__'):
                                    input_schema = dict(input_schema.__dict__)
                                else:
                                    input_schema = {}
                            except Exception as e:
                                print(f"[ERROR] ToolManager.get_all_tools: Failed to convert inputSchema for tool '{tool_name}': {e}")
                                input_schema = {}
                        
                        # Ensure we have required attributes
                        if not hasattr(t, 'name'):
                            print(f"[ERROR] ToolManager.get_all_tools: Tool {i} from client '{client_name}' missing 'name' attribute")
                            continue
                        
                        tool_dict = {
                            "name": t.name,
                            "description": getattr(t, 'description', ''),
                            "input_schema": input_schema,
                        }
                        tools.append(tool_dict)
                    except AttributeError as e:
                        print(f"[ERROR] ToolManager.get_all_tools: AttributeError processing tool {i} from client '{client_name}': {e}")
                        continue
                    except Exception as e:
                        print(f"[ERROR] ToolManager.get_all_tools: Unexpected error processing tool {i} from client '{client_name}': {type(e).__name__}: {e}")
                        continue
            except Exception as e:
                print(f"[ERROR] ToolManager.get_all_tools: Error getting tools from client '{client_name}': {type(e).__name__}: {e}")
                continue
        
        return tools

    @classmethod
    async def _find_client_with_tool(
        cls, clients: list[MCPClient], tool_name: str
    ) -> Optional[MCPClient]:
        """Finds the first client that has the specified tool."""
        for client in clients:
            tools = await client.list_tools()
            tool = next((t for t in tools if t.name == tool_name), None)
            if tool:
                return client
        return None

    @classmethod
    def _build_tool_result_part(
        cls,
        function_name: str,
        result: Any,
        status: Literal["success"] | Literal["error"],
    ) -> Dict[str, Any]:
        """Builds a tool result part dictionary for Gemini function response format."""
        # Gemini expects functionResponse with name and response
        # The response field needs to be properly formatted for protobuf conversion
        # If result is a string, we need to ensure it's handled correctly
        # If result is already a dict/list, use it as-is
        # For simple types, wrap them appropriately
        
        # Ensure response is in a format that protobuf can handle
        if isinstance(result, str):
            # For strings, we can pass them directly, but sometimes need to wrap
            # Check if it's JSON - if so, parse it
            if result.strip().startswith('{') or result.strip().startswith('['):
                try:
                    result = json.loads(result)
                except (json.JSONDecodeError, TypeError):
                    # Not JSON, keep as string
                    pass
        
        # Build the function response part
        # Use snake_case for consistency with Gemini SDK expectations
        return {
            "function_response": {
                "name": function_name,
                "response": result
            }
        }

    @classmethod
    async def execute_tool_requests(
        cls, clients: dict[str, MCPClient], response: Any
    ) -> List[Dict[str, Any]]:
        """Executes function calls from a Gemini response."""
        try:
            # Extract function calls from Gemini response
            function_calls = []
            if hasattr(response, 'parts'):
                try:
                    for part in response.parts:
                        try:
                            if hasattr(part, 'function_call') and part.function_call is not None:
                                # Only add if it has a name (valid function call)
                                if hasattr(part.function_call, 'name') and part.function_call.name:
                                    function_calls.append(part.function_call)
                        except Exception as e:
                            print(f"[ERROR] ToolManager.execute_tool_requests: Error processing part: {type(e).__name__}: {e}")
                            continue
                except Exception as e:
                    print(f"[ERROR] ToolManager.execute_tool_requests: Error iterating response parts: {type(e).__name__}: {e}")
            
            
            # Return empty list if no function calls found
            if not function_calls:
                return []
            
            tool_result_blocks: List[Dict[str, Any]] = []
            
            for i, function_call in enumerate(function_calls):
                try:
                    function_name = getattr(function_call, 'name', f'unknown_function_{i}')
                    
                    # Handle args - it might be None, a dict, or need conversion
                    function_args = {}
                    try:
                        if hasattr(function_call, 'args') and function_call.args is not None:
                            if isinstance(function_call.args, dict):
                                function_args = function_call.args
                            else:
                                try:
                                    function_args = dict(function_call.args)
                                except (TypeError, ValueError) as e:
                                    print(f"[WARNING] ToolManager.execute_tool_requests: Could not convert args to dict for '{function_name}': {e}")
                                    function_args = {}
                    except Exception as e:
                        print(f"[ERROR] ToolManager.execute_tool_requests: Error processing args for '{function_name}': {type(e).__name__}: {e}")
                        function_args = {}
                    

                    client = await cls._find_client_with_tool(
                        list(clients.values()), function_name
                    )

                    if not client:
                        print(f"[WARNING] ToolManager.execute_tool_requests: Could not find client for tool '{function_name}'")
                        tool_result_part = cls._build_tool_result_part(
                            function_name, {"error": "Could not find that tool"}, "error"
                        )
                        tool_result_blocks.append(tool_result_part)
                        continue

                    try:
                        tool_output: CallToolResult | None = await client.call_tool(
                            function_name, function_args
                        )
                        
                        items = []
                        if tool_output:
                            try:
                                items = tool_output.content
                            except AttributeError as e:
                                print(f"[ERROR] ToolManager.execute_tool_requests: Tool output missing 'content' attribute: {e}")
                                items = []
                        
                        content_list = []
                        try:
                            content_list = [
                                item.text for item in items if isinstance(item, TextContent)
                            ]
                        except Exception as e:
                            print(f"[ERROR] ToolManager.execute_tool_requests: Error extracting text from tool output: {type(e).__name__}: {e}")
                            content_list = []
                        
                        # Convert to a result format
                        if len(content_list) == 1:
                            result = content_list[0]
                        else:
                            result = content_list
                        
                        # Try to parse as JSON if it looks like JSON
                        try:
                            if isinstance(result, str):
                                parsed = json.loads(result)
                                result = parsed
                        except (json.JSONDecodeError, TypeError):
                            # Not JSON, keep as string
                            pass
                        
                        tool_result_part = cls._build_tool_result_part(
                            function_name,
                            result,
                            "error" if (tool_output and tool_output.isError) else "success",
                        )
                    except Exception as e:
                        error_message = f"Error executing tool '{function_name}': {type(e).__name__}: {e}"
                        print(f"[ERROR] ToolManager.execute_tool_requests: {error_message}")
                        tool_result_part = cls._build_tool_result_part(
                            function_name,
                            {"error": error_message},
                            "error",
                        )

                    tool_result_blocks.append(tool_result_part)
                except Exception as e:
                    print(f"[ERROR] ToolManager.execute_tool_requests: Error processing function call {i}: {type(e).__name__}: {e}")
                    # Continue with next function call
                    continue
            
            return tool_result_blocks
        except Exception as e:
            print(f"[ERROR] ToolManager.execute_tool_requests: Fatal error: {type(e).__name__}: {e}")
            return []
