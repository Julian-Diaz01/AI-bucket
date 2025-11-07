from core.gemini import Gemini
from mcp_client import MCPClient
from core.tools import ToolManager
from typing import Dict, Any, List


class Chat:
    def __init__(self, gemini_service: Gemini, clients: dict[str, MCPClient]):
        self.gemini_service: Gemini = gemini_service
        self.clients: dict[str, MCPClient] = clients
        self.messages: list[Dict[str, Any]] = []

    async def _process_query(self, query: str):
        self.messages.append({"role": "user", "parts": [{"text": query}]})

    def _has_function_calls(self, response) -> bool:
        """Check if the response contains function calls."""
        if hasattr(response, 'parts'):
            for part in response.parts:
                if hasattr(part, 'function_call') and part.function_call is not None:
                    # Check if function_call has a name (valid function call)
                    if hasattr(part.function_call, 'name') and part.function_call.name:
                        return True
        return False

    async def run(
        self,
        query: str,
    ) -> str:
        final_text_response = ""

        try:
            await self._process_query(query)
        except Exception as e:
            print(f"[ERROR] Chat.run: Error processing query: {type(e).__name__}: {e}")
            import traceback
            print(f"[DEBUG] Traceback:\n{traceback.format_exc()}")
            return f"❌ Error processing query: {str(e)}"

        while True:
            try:
                tools = await ToolManager.get_all_tools(self.clients)
                
                response = self.gemini_service.chat(
                    messages=self.messages,
                    tools=tools,
                )
            except Exception as e:
                error_msg = str(e)
                error_type = type(e).__name__
                print(f"[ERROR] Chat.run: Error calling Gemini API: {error_type}: {error_msg}")
                import traceback
                print(f"[DEBUG] Traceback:\n{traceback.format_exc()}")
                
                if "quota" in error_msg.lower() or "billing" in error_msg.lower():
                    return f"❌ Error: {error_msg}\n\nPlease check your Google AI Studio account and ensure you have sufficient quota."
                elif "rate" in error_msg.lower() or "limit" in error_msg.lower():
                    return f"❌ Rate Limit Error: {error_msg}\n\nPlease wait a moment and try again."
                elif "connection" in error_msg.lower() or "network" in error_msg.lower():
                    return f"❌ Connection Error: {error_msg}\n\nPlease check your internet connection and try again."
                elif "permission" in error_msg.lower() or "api key" in error_msg.lower():
                    return f"❌ Authentication Error: {error_msg}\n\nPlease check your GEMINI_API_KEY in the .env file."
                else:
                    return f"❌ API Error ({error_type}): {error_msg}"

            try:
                self.gemini_service.add_assistant_message(self.messages, response)
            except Exception as e:
                print(f"[ERROR] Chat.run: Error adding assistant message: {type(e).__name__}: {e}")
                import traceback
                print(f"[DEBUG] Traceback:\n{traceback.format_exc()}")
                # Continue anyway, try to extract text

            # Check if response has function calls
            if self._has_function_calls(response):
                try:
                    text_content = self.gemini_service.text_from_message(response)
                    if text_content:
                        print(text_content)
                except Exception as e:
                    print(f"[ERROR] Chat.run: Error extracting text from message: {type(e).__name__}: {e}")
                    text_content = ""
                
                try:
                    tool_result_parts = await ToolManager.execute_tool_requests(
                        self.clients, response
                    )
                except Exception as e:
                    print(f"[ERROR] Chat.run: Error executing tool requests: {type(e).__name__}: {e}")
                    tool_result_parts = []

                # Only add tool results if we have any
                if tool_result_parts:
                    try:
                        self.gemini_service.add_user_message(
                            self.messages, tool_result_parts
                        )
                    except Exception as e:
                        print(f"[ERROR] Chat.run: Error adding tool results to messages: {type(e).__name__}: {e}")
                        import traceback
                        print(f"[DEBUG] Traceback:\n{traceback.format_exc()}")
                        # Break and return what we have
                        final_text_response = text_content or "No response generated."
                        break
                else:
                    # No tool results, break and return the text response
                    final_text_response = text_content or "No response generated."
                    break
            else:
                try:
                    final_text_response = self.gemini_service.text_from_message(
                        response
                    )
                except Exception as e:
                    print(f"[ERROR] Chat.run: Error extracting final text response: {type(e).__name__}: {e}")
                    final_text_response = "Error extracting response text."
                break

        return final_text_response
