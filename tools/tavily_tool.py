from tavily import TavilyClient
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("TAVILY_API_KEY")
if not api_key:
    raise ValueError("TAVILY_API_KEY not found in environment variables")

client = TavilyClient(api_key=api_key)


def tavily_search(query):
    if not query or not query.strip():
        return "Error: Query cannot be empty"
    
    try:
        response = client.search(
            query=query.strip(),
            max_results=5,
            include_raw_content=False 
        )
        
        if not response.get("results"):
            return "No results found for your query"
        
        results = []
        for i, r in enumerate(response["results"], 1):
            title = r.get("title", "Unknown Title").strip()
            url = r.get("url", "").strip()
            snippet = r.get("content", "").strip()
            
            # Truncate smartly at word boundary
            if len(snippet) > 300:
                snippet = snippet[:300].rsplit(" ", 1)[0] + "..."
            
            if url:  # Only add if URL exists
                results.append(f"{i}. **{title}**\n   {url}\n   {snippet}")
        
        return "\n\n".join(results) if results else "No valid results found"
    
    except Exception as e:
        return f"Search error: {str(e)}"