"""
OmniDev - Location Router
Endpoints for location services with optional Google Maps API support
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import geocoder
import httpx

router = APIRouter()


class LocationResponse(BaseModel):
    latitude: Optional[float]
    longitude: Optional[float]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    address: Optional[str]
    raw: Optional[dict] = None


async def google_geocode(address: str, api_key: str) -> dict:
    """Use Google Geocoding API for better results"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": address, "key": api_key}
        )
        data = response.json()
        
        if data.get("status") == "OK" and data.get("results"):
            result = data["results"][0]
            location = result["geometry"]["location"]
            
            # Extract address components
            components = {}
            for comp in result.get("address_components", []):
                types = comp.get("types", [])
                if "locality" in types:
                    components["city"] = comp["long_name"]
                elif "administrative_area_level_1" in types:
                    components["state"] = comp["long_name"]
                elif "country" in types:
                    components["country"] = comp["long_name"]
            
            return {
                "latitude": location["lat"],
                "longitude": location["lng"],
                "address": result.get("formatted_address"),
                "city": components.get("city"),
                "state": components.get("state"),
                "country": components.get("country"),
                "raw": result
            }
        raise Exception(f"Google Geocoding failed: {data.get('status')}")


async def google_reverse_geocode(lat: float, lng: float, api_key: str) -> dict:
    """Use Google Reverse Geocoding API"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"latlng": f"{lat},{lng}", "key": api_key}
        )
        data = response.json()
        
        if data.get("status") == "OK" and data.get("results"):
            result = data["results"][0]
            
            # Extract address components
            components = {}
            for comp in result.get("address_components", []):
                types = comp.get("types", [])
                if "locality" in types:
                    components["city"] = comp["long_name"]
                elif "administrative_area_level_1" in types:
                    components["state"] = comp["long_name"]
                elif "country" in types:
                    components["country"] = comp["long_name"]
                elif "postal_code" in types:
                    components["postal"] = comp["long_name"]
                elif "sublocality" in types or "neighborhood" in types:
                    components["neighborhood"] = comp["long_name"]
            
            return {
                "address": result.get("formatted_address"),
                "city": components.get("city"),
                "state": components.get("state"),
                "country": components.get("country"),
                "postal": components.get("postal"),
                "neighborhood": components.get("neighborhood"),
                "raw": result
            }
        raise Exception(f"Google Reverse Geocoding failed: {data.get('status')}")


@router.get("/current", response_model=LocationResponse)
async def get_current_location(api_key: Optional[str] = None):
    """
    Get current location based on IP address
    
    - **api_key**: Optional Google Maps API key for better results
    
    Note: This uses IP-based geolocation which may not be perfectly accurate
    Uses multiple fallback providers for reliability.
    """
    try:
        # Try primary: geocoder IP
        g = geocoder.ip('me')
        
        if g.ok:
            return LocationResponse(
                latitude=g.lat,
                longitude=g.lng,
                city=g.city,
                state=g.state,
                country=g.country,
                address=g.address,
                raw=g.json
            )
        
        # Fallback 1: Try ipinfo.io directly
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("https://ipinfo.io/json", timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    loc = data.get("loc", "0,0").split(",")
                    return LocationResponse(
                        latitude=float(loc[0]) if len(loc) > 0 else None,
                        longitude=float(loc[1]) if len(loc) > 1 else None,
                        city=data.get("city"),
                        state=data.get("region"),
                        country=data.get("country"),
                        address=f"{data.get('city', '')}, {data.get('region', '')}, {data.get('country', '')}",
                        raw=data
                    )
        except Exception as e:
            print(f"ipinfo.io fallback failed: {e}")
        
        # Fallback 2: Try ip-api.com
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://ip-api.com/json", timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        return LocationResponse(
                            latitude=data.get("lat"),
                            longitude=data.get("lon"),
                            city=data.get("city"),
                            state=data.get("regionName"),
                            country=data.get("country"),
                            address=f"{data.get('city', '')}, {data.get('regionName', '')}, {data.get('country', '')}",
                            raw=data
                        )
        except Exception as e:
            print(f"ip-api.com fallback failed: {e}")
            
        raise HTTPException(status_code=503, detail="Unable to determine location from any provider")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reverse")
async def reverse_geocode(lat: float, lng: float, api_key: Optional[str] = None):
    """
    Get address from coordinates (reverse geocoding)
    
    - **lat**: Latitude
    - **lng**: Longitude
    - **api_key**: Optional Google Maps API key for better results
    """
    try:
        # Try Google API if key provided
        if api_key:
            try:
                return await google_reverse_geocode(lat, lng, api_key)
            except Exception as e:
                print(f"Google API failed, falling back to OSM: {e}")
        
        # Fall back to OpenStreetMap
        g = geocoder.osm([lat, lng], method='reverse')
        
        if not g.ok:
            raise HTTPException(status_code=404, detail="Location not found")
        
        return {
            "address": g.address,
            "city": g.city,
            "state": g.state,
            "country": g.country,
            "postal": g.postal,
            "neighborhood": g.neighborhood,
            "raw": g.json
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_location(query: str, api_key: Optional[str] = None):
    """
    Search for a location by name
    
    - **query**: Location name (e.g., "Mumbai, India")
    - **api_key**: Optional Google Maps API key for better results
    """
    try:
        # Try Google API if key provided
        if api_key:
            try:
                result = await google_geocode(query, api_key)
                return {"query": query, **result}
            except Exception as e:
                print(f"Google API failed, falling back to OSM: {e}")
        
        # Fall back to OpenStreetMap
        g = geocoder.osm(query)
        
        if not g.ok:
            raise HTTPException(status_code=404, detail="Location not found")
        
        return {
            "query": query,
            "latitude": g.lat,
            "longitude": g.lng,
            "address": g.address,
            "city": g.city,
            "state": g.state,
            "country": g.country,
            "raw": g.json
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nearby")
async def get_nearby_places(lat: float, lng: float, api_key: Optional[str] = None):
    """
    Get nearby places for given coordinates
    
    - **lat**: Latitude
    - **lng**: Longitude
    - **api_key**: Optional Google Maps API key
    """
    try:
        # Try Google API if key provided
        if api_key:
            try:
                result = await google_reverse_geocode(lat, lng, api_key)
                return {
                    "coordinates": {"lat": lat, "lng": lng},
                    **result,
                    "nearby": {}
                }
            except Exception as e:
                print(f"Google API failed, falling back to OSM: {e}")
        
        g = geocoder.osm([lat, lng], method='reverse')
        
        if not g.ok:
            raise HTTPException(status_code=404, detail="Location not found")
        
        # Extract address components
        address_data = g.json.get('raw', {}).get('address', {})
        
        return {
            "coordinates": {"lat": lat, "lng": lng},
            "address": g.address,
            "neighborhood": address_data.get('neighbourhood') or address_data.get('suburb'),
            "city": g.city,
            "district": address_data.get('city_district') or address_data.get('district'),
            "state": g.state,
            "country": g.country,
            "nearby": {
                "road": address_data.get('road'),
                "suburb": address_data.get('suburb'),
                "locality": address_data.get('locality'),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def location_status():
    """Check Location service status"""
    return {
        "service": "Location Services",
        "provider": "OpenStreetMap + Google Maps (optional)",
        "status": "operational",
        "capabilities": [
            "ip-location",
            "reverse-geocoding", 
            "location-search", 
            "nearby-places",
            "google-api-support"
        ]
    }
