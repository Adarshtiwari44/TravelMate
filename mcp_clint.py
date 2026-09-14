import os 
import asyncio
import certifi 
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_groq import ChatGroq

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY") or ""
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY") or ""
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or ""


llm = ChatGroq(
    model="openai/gpt-oss-20b",
    api_key=GROQ_API_KEY
)




client = MultiServerMCPClient(
    {
       "tavily": {
            "transport": "streamable_http",
            "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"
        },

        "weather":{
            "transport": "stdio",
            "args": ["run", r"D:\Agentic_ai-Project\TripeMate-Ai\custom_wether_mcp.py"],
            "command": "python",
            "env":{
                "OPENWEATHER_API_KEY": OPENWEATHER_API_KEY
            }
        }
    }
)


async def get_all_tools():
    tools = await client.get_tools()
    print("\nAvailable MCP Tools:\n")

    for tool in tools:
        print(tool.name)



# This retuns tavily_search tool object
tavily_search_tool = None

async def get_tavily_search_tool():
    global tavily_search_tool
    if tavily_search_tool is not None:
        return

    tools = await client.get_tools()
    print("\nAvailable MCP Tools:")

    for tool in tools:
        print(tool.name)

    tavily_search_tool = next(
        tool
        for tool in tools
        if tool.name == "tavily_search"
    )



# This function can be used to call the tavily_search tool with a query in backend.py
async def tavily_mcp_search(query: str):
    if not query or not isinstance(query, str):
        return "Query must be a non-empty string."
    await get_tavily_search_tool()
    result = await tavily_search_tool.ainvoke(
        {
            "query": query
        }
    )
    return result


# ==========================================
# Weather MCP tools
# ==========================================

weather_tool = None
forecast_tool = None


async def initialize_weather_tools():
    global weather_tool
    global forecast_tool

    if weather_tool is not None:
        return

    tools = await client.get_tools()

    weather_tool = next(
        t for t in tools
        if t.name == "get_current_weather"
    )

    forecast_tool = next(
        t for t in tools
        if t.name == "get_forecast"
    )


async def wether_mcp_search(city:str):
    if not city or not isinstance(city, str):
        return "City must be a non-empty string."
    await initialize_weather_tools()

    return await weather_tool.ainvoke(
        {
            "city":city
        }
    )
   

async def forecast_mcp_search(city: str):
    if not city or not isinstance(city, str):
        return "City must be a non-empty string."
    await initialize_weather_tools()

    return await forecast_tool.ainvoke(
        {
            "city": city
        }
    )



# ==========================================
# Destination extractor
# ==========================================

def extract_destination(query: str):
    if not query or not isinstance(query, str):
        return ""

    prompt = f"""
    Extract only the destination city or country.

    Query:
    {query}

    Return only destination name.
    """

    response = llm.invoke(prompt)

    if response.content is None:
        return query.strip() if (query and isinstance(query, str)) else ""

    return response.content.strip()