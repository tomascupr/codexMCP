import asyncio
from fastmcp import Client
from fastmcp.client.transports import StdioTransport
import sys
import traceback

# For Python < 3.11, define a placeholder ExceptionGroup class for type checking
if sys.version_info >= (3, 11):
    # Python 3.11+ has built-in ExceptionGroup
    pass
else:
    # Define a dummy class that will never match in isinstance checks
    class ExceptionGroup:
        pass


# --- Configuration ---
SERVER_HOST = "localhost"
SERVER_PORT = 5555  # Default FastMCP port, adjust if needed

# Construct the command to run the server as a module via stdio
PYTHON_EXE = sys.executable  # Get current python interpreter path
SERVER_MODULE = "codexmcp.server"
SERVER_COMMAND = [PYTHON_EXE, "-m", SERVER_MODULE]

TOOL_NAME = "list_tools"
TOOL_ARGS = {}
# --- End Configuration ---


async def main():
    # Explicitly use PythonStdioTransport with the command list
    print(f"Using command for StdioTransport: {' '.join(SERVER_COMMAND)}")
    # Use StdioTransport with command, args, and set cwd to src so the local package is used
    transport = StdioTransport(
        command=SERVER_COMMAND[0], args=SERVER_COMMAND[1:], cwd="src"
    )
    client_instance = Client(transport)
    print(f"Client configured for command: {' '.join(SERVER_COMMAND)}")
    try:
        # The connection happens when entering the context manager
        async with client_instance as client:
            print("Connection successful (or established via context manager).")

            # List available tools on the server to verify it's responsive
            print("\nListing available tools on the server...")
            result = await client.list_tools()

            # Print the list of tools
            print("--- Available Tools ---")
            tool_names = [tool.name for tool in result]
            print(tool_names)
            print("--- End Available Tools ---")

            # Check and return exit code based on tool list
            if tool_names:
                print("Server responded with tool list. Test passed.")
                return 0
            else:
                print("Server returned empty tool list. Test failed.")
                return 1

    except (
        ConnectionRefusedError
    ):  # This might not be the right exception for stdio failure
        print(
            f"\nConnection Error: Could not start or connect to server command '{' '.join(SERVER_COMMAND)}'."
        )
        return 1
    except Exception as e:
        # Unwrap ExceptionGroup if present to print sub-exceptions
        print(f"\nAn unexpected error occurred: {e}")
        print(f"Error Type: {type(e)}")
        # ExceptionGroup is only available in Python 3.11+
        if sys.version_info >= (3, 11) and isinstance(e, ExceptionGroup):
            print("Encountered ExceptionGroup with sub-exceptions:")
            for idx, sub in enumerate(e.exceptions):
                print(f"  {idx + 1}. {type(sub).__name__}: {sub}")
        else:
            traceback.print_exception(type(e), e, e.__traceback__)
        return 1
        # No explicit client.close() needed when using async with


if __name__ == "__main__":
    # Server is started by the transport, no need to run separately
    # print("Ensure the CodexMCP server is running (`codexmcp`) in another terminal.")
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
