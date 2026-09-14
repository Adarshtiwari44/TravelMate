import os
import sys
from pathlib import Path

import certifi
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_groq import ChatGroq


# ==========================================
# Environment configuration
# ==========================================

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# Automatically find the current project folder.
# This avoids hard-coded Windows paths.
PROJECT_DIR = Path(__file__).resolve().parent

WEATHER_SERVER_PATH = (
    PROJECT_DIR / "custom_weather_mcp_server.py"
)


# ==========================================
# Weather MCP Environment
# ==========================================

WEATHER_ENV = os.environ.copy()

WEATHER_ENV["OPENWEATHER_API_KEY"] = (
    OPENWEATHER_API_KEY or ""
)


# ==========================================
# LLM
# ==========================================

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY
)


# ==========================================
# MCP Client Configuration
# ==========================================

client = MultiServerMCPClient(
    {

        # ==================================
        # Tavily MCP
        # ==================================

        "tavily": {
            "transport": "streamable_http",
            "url": (
                "https://mcp.tavily.com/mcp/"
                f"?tavilyApiKey={TAVILY_API_KEY}"
            )
        },


        # ==================================
        # Weather MCP
        # ==================================

        "weather": {
            "transport": "stdio",

            # Use the same Python environment
            # that is running the application.
            "command": sys.executable,

            # Automatically use the weather MCP
            # server from the project directory.
            "args": [
                str(WEATHER_SERVER_PATH)
            ],

            "env": WEATHER_ENV
        }
    }
)


# ==========================================
# Diagnostic Function
# ==========================================

async def get_all_tools():

    """
    Load Tavily and Weather MCP separately.

    If one server fails, the other server
    can still be loaded.
    """

    all_tools = []

    for server_name in (
        "tavily",
        "weather"
    ):

        try:

            tools = await client.get_tools(
                server_name=server_name
            )

            all_tools.extend(tools)

            print(
                f"\nAvailable tools from "
                f"{server_name} MCP:\n"
            )

            for tool in tools:
                print(tool.name)

        except Exception as error:

            print(
                f"\nCould not connect to "
                f"{server_name} MCP:\n"
                f"{error}\n"
            )

    return all_tools


# ==========================================
# Tavily MCP
# ==========================================

search_tool = None


async def initialize_mcp():

    """
    Initialize only Tavily MCP.

    Weather MCP is initialized separately.
    """

    global search_tool

    if search_tool is not None:
        return

    tools = await client.get_tools(
        server_name="tavily"
    )

    tools_by_name = {
        tool.name: tool
        for tool in tools
    }

    search_tool = tools_by_name.get(
        "tavily_search"
    )

    if search_tool is None:

        available_tools = ", ".join(
            tools_by_name.keys()
        )

        raise RuntimeError(
            "Tavily MCP connected, but the "
            "'tavily_search' tool was not found. "
            f"Available tools: "
            f"{available_tools or 'none'}"
        )


async def tavily_mcp_search(query: str):

    await initialize_mcp()

    result = await search_tool.ainvoke(
        {
            "query": query
        }
    )

    return result


# ==========================================
# Weather MCP
# ==========================================

weather_tool = None
forecast_tool = None


async def initialize_weather_tools():

    global weather_tool
    global forecast_tool

    # Already initialized
    if (
        weather_tool is not None
        and forecast_tool is not None
    ):
        return

    # Check weather MCP file exists
    if not WEATHER_SERVER_PATH.exists():

        raise FileNotFoundError(
            "Weather MCP server file was not found: "
            f"{WEATHER_SERVER_PATH}"
        )

    # Load only Weather MCP
    tools = await client.get_tools(
        server_name="weather"
    )

    tools_by_name = {
        tool.name: tool
        for tool in tools
    }

    weather_tool = tools_by_name.get(
        "get_current_weather"
    )

    forecast_tool = tools_by_name.get(
        "get_forecast"
    )

    missing_tools = []

    if weather_tool is None:

        missing_tools.append(
            "get_current_weather"
        )

    if forecast_tool is None:

        missing_tools.append(
            "get_forecast"
        )

    if missing_tools:

        available_tools = ", ".join(
            tools_by_name.keys()
        )

        raise RuntimeError(
            "Missing Weather MCP tools: "
            f"{', '.join(missing_tools)}. "
            f"Available tools: "
            f"{available_tools or 'none'}"
        )


# ==========================================
# Current Weather
# ==========================================

async def weather_mcp_search(city: str):

    await initialize_weather_tools()

    result = await weather_tool.ainvoke(
        {
            "city": city
        }
    )

    return result


# ==========================================
# Weather Forecast
# ==========================================

async def forecast_mcp_search(city: str):

    await initialize_weather_tools()

    result = await forecast_tool.ainvoke(
        {
            "city": city
        }
    )

    return result


# ==========================================
# Destination Extractor
# ==========================================

def extract_destination(query: str):

    prompt = f"""
    Extract only the destination city or country.

    Query:
    {query}

    Return only destination name.
    """

    response = llm.invoke(prompt)

    return response.content.strip()