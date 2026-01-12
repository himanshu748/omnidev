"""
TechTrainingPro - Location Router
Endpoints for location services
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import geocoder

router = APIRouter()


class LocationResponse(BaseModel):
    latitude: Optional[float]
    longitude: Optional[float]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    address: Optional[str]
    raw: Optional[dict]


@router.get("/current", response_model=LocationResponse)
async def get_current_location():
    """
    Get current location based on IP address
    
    Note: This uses IP-based geolocation which may not be perfectly accurate
    """
    try:
        g = geocoder.ip('me')
        
        if not g.ok:
            raise HTTPException(status_code=503, detail="Unable to determine location")
        
        return LocationResponse(
            latitude=g.lat,
            longitude=g.lng,
            city=g.city,
            state=g.state,
            country=g.country,
            address=g.address,
            raw=g.json
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reverse")
async def reverse_geocode(lat: float, lng: float):
    """
    Get address from coordinates (reverse geocoding)
    
    - **lat**: Latitude
    - **lng**: Longitude
    """
    try:
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_location(query: str):
    """
    Search for a location by name
    
    - **query**: Location name (e.g., "Mumbai, India")
    """
    try:
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nearby")
async def get_nearby_places(lat: float, lng: float):
    """
    Get nearby places for given coordinates
    
    - **lat**: Latitude
    - **lng**: Longitude
    """
    try:
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def location_status():
    """Check Location service status"""
    return {
        "service": "Location Services",
        "provider": "OpenStreetMap (via geocoder)",
        "status": "operational",
        "capabilities": ["ip-location", "reverse-geocoding", "location-search", "nearby-places"]
    }
