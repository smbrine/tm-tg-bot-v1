from grpc import aio

from bot import schemas
from proto import (
    map_sessions_service_pb2,
    map_sessions_service_pb2_grpc,
)


class MapSessions:
    def __init__(self, host: str) -> None:
        self.host = host

    async def CreateSession(self, user_id: int, features: list[schemas.Feature]):
        async with aio.insecure_channel(
            self.host
        ) as channel:
            stub = map_sessions_service_pb2_grpc.MapSessionsServiceStub(
                channel
            )
            req = map_sessions_service_pb2.CreateSessionRequest(
                user_id=user_id,
                features=[
                    map_sessions_service_pb2.Feature(
                        type=feature.type,
                        name=feature.name,
                        geometry=map_sessions_service_pb2.Geometry(
                            points=[map_sessions_service_pb2.Point(
                                latitude=point.latitude,
                                longitude=point.longitude,
                            ) for point in feature.geometry.points]
                        )
                    ) for feature in features
                ]
            )
            return await stub.CreateSession(req)
