from grpc import aio

from proto import (
    distance_calculator_service_pb2_grpc,
    distance_calculator_service_pb2,
)


class DistanceCalculator:
    def __init__(self, host: str) -> None:
        self.host = host

    async def CalculateDistance(
        self,
        lat: float,
        lon: float,
        object: str,
        search_distance: int = 5000,
    ):
        async with aio.insecure_channel(
            self.host
        ) as channel:
            stub = distance_calculator_service_pb2_grpc.DistanceCalculatorServiceStub(
                channel
            )
            req = distance_calculator_service_pb2.CalculateDistanceRequest(
                latitude=lat,
                longitude=lon,
                object=object,
                search_distance=search_distance,
            )

            return await stub.CalculateDistance(
                req
            )
