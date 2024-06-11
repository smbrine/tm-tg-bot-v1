from pydantic import BaseModel, field_validator
from pydantic.main import Model


class Point(BaseModel):
    latitude: float
    longitude: float

    @field_validator("latitude")
    def latitude_real(
        cls: type[Model],
        v: float,
    ) -> float:
        if not (-90 < v < 90):
            raise ValueError(
                "Latitude must be between -90º and 90º."
            )
        return v

    @field_validator("longitude")
    def longitude_real(
        cls: type[Model],
        v: float,
    ) -> float:
        if not (-180 < v < 180):
            raise ValueError(
                "Longitude must be between -180º and 180º."
            )
        return v


class Geometry(BaseModel):
    points: list[Point]


class Feature(BaseModel):
    geometry: Geometry
    type: str
    name: str


class SessionRecommendedMapCenter(BaseModel):
    latitude: float
    longitude: float
    zoom: int


class CreateSessionRequest(BaseModel):
    user_id: int
    features: list[Feature]


class SessionResponse(BaseModel):
    features: list[Feature]
    recommended_map_center: (
        SessionRecommendedMapCenter
    )
