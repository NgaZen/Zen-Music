"""
Random Joke Generator Module
Fetches jokes from external APIs and provides random joke generation
"""

import aiohttp
import asyncio
import logging
from typing import Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class JokeSource(Enum):
    """Available joke API sources"""
    OFFICIAL_JOKES = "https://official-joke-api.appspot.com/random_joke"
    JOKE_API = "https://v2.jokeapi.dev/joke/Any"
    USELESSFACTS = "https://uselessfacts.jsph.pl/random.json?language=en"


class JokeGenerator:
    """
    Random Joke Generator using external APIs
    Supports multiple joke sources for variety
    """

    def __init__(self, timeout: int = 10):
        """
        Initialize the joke generator
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def _ensure_session(self):
        """Ensure session is created"""
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def get_official_joke(self) -> Dict[str, Any]:
        """
        Fetch a joke from Official Joke API
        Returns dict with 'setup' and 'punchline'
        
        Returns:
            Dict containing joke data
        """
        await self._ensure_session()
        try:
            async with self.session.get(
                JokeSource.OFFICIAL_JOKES.value,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "setup": data.get("setup", ""),
                        "punchline": data.get("punchline", ""),
                        "type": "two-part",
                        "source": "Official Joke API"
                    }
        except asyncio.TimeoutError:
            logger.warning("Official Joke API request timed out")
        except Exception as e:
            logger.error(f"Error fetching from Official Joke API: {e}")
        
        return None

    async def get_jokeapi_joke(self) -> Dict[str, Any]:
        """
        Fetch a joke from JokeAPI
        Supports various joke types and categories
        
        Returns:
            Dict containing joke data
        """
        await self._ensure_session()
        try:
            async with self.session.get(
                JokeSource.JOKE_API.value,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("type") == "twopart":
                        return {
                            "setup": data.get("setup", ""),
                            "punchline": data.get("delivery", ""),
                            "type": "two-part",
                            "category": data.get("category", "General"),
                            "source": "JokeAPI"
                        }
                    else:
                        return {
                            "joke": data.get("joke", ""),
                            "type": "single",
                            "category": data.get("category", "General"),
                            "source": "JokeAPI"
                        }
        except asyncio.TimeoutError:
            logger.warning("JokeAPI request timed out")
        except Exception as e:
            logger.error(f"Error fetching from JokeAPI: {e}")
        
        return None

    async def get_random_fact(self) -> Dict[str, Any]:
        """
        Fetch a random useless fact (fun alternative to jokes)
        
        Returns:
            Dict containing fact data
        """
        await self._ensure_session()
        try:
            async with self.session.get(
                JokeSource.USELESSFACTS.value,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "fact": data.get("text", ""),
                        "type": "fact",
                        "source": "Useless Facts"
                    }
        except asyncio.TimeoutError:
            logger.warning("Useless Facts API request timed out")
        except Exception as e:
            logger.error(f"Error fetching from Useless Facts API: {e}")
        
        return None

    async def get_random_joke(self, source: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get a random joke from available sources
        
        Args:
            source: Specific source to use ('official', 'jokeapi', 'fact')
                   If None, randomly selects from available sources
        
        Returns:
            Dict containing joke/fact data, or None if all sources fail
        """
        await self._ensure_session()
        
        sources = {
            "official": self.get_official_joke,
            "jokeapi": self.get_jokeapi_joke,
            "fact": self.get_random_fact,
        }
        
        if source and source.lower() in sources:
            return await sources[source.lower()]()
        
        # Try all sources and return first successful result
        import random
        source_keys = list(sources.keys())
        random.shuffle(source_keys)
        
        for key in source_keys:
            result = await sources[key]()
            if result:
                return result
        
        return None

    async def format_joke(self, joke_data: Dict[str, Any]) -> str:
        """
        Format joke data into a readable string
        
        Args:
            joke_data: Joke data dictionary
        
        Returns:
            Formatted joke string
        """
        if not joke_data:
            return "😔 Sorry, couldn't fetch a joke right now. Try again later!"
        
        formatted = ""
        
        if joke_data.get("type") == "two-part":
            formatted = f"😄 **Setup:** {joke_data.get('setup', '')}\n\n"
            formatted += f"😂 **Punchline:** {joke_data.get('punchline', '')}"
        elif joke_data.get("type") == "single":
            formatted = f"😂 {joke_data.get('joke', '')}"
        elif joke_data.get("type") == "fact":
            formatted = f"🧠 **Fun Fact:** {joke_data.get('fact', '')}"
        
        source = joke_data.get("source", "")
        category = joke_data.get("category", "")
        
        if source:
            formatted += f"\n\n_Source: {source}_"
        if category:
            formatted += f" | _Category: {category}_"
        
        return formatted

    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()


# Example usage and testing
async def main():
    """Test the joke generator"""
    async with JokeGenerator() as generator:
        print("🎭 Testing Random Joke Generator\n")
        
        # Test Official Joke API
        print("1️⃣ Official Joke API:")
        joke = await generator.get_official_joke()
        if joke:
            print(await generator.format_joke(joke))
        print("\n" + "="*50 + "\n")
        
        # Test JokeAPI
        print("2️⃣ JokeAPI:")
        joke = await generator.get_jokeapi_joke()
        if joke:
            print(await generator.format_joke(joke))
        print("\n" + "="*50 + "\n")
        
        # Test Useless Facts
        print("3️⃣ Random Fact:")
        fact = await generator.get_random_fact()
        if fact:
            print(await generator.format_joke(fact))
        print("\n" + "="*50 + "\n")
        
        # Test random selection
        print("4️⃣ Random Source:")
        joke = await generator.get_random_joke()
        if joke:
            print(await generator.format_joke(joke))


if __name__ == "__main__":
    asyncio.run(main())
