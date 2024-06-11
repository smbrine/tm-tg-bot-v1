from grpc import aio

from proto import (
    density_calculator_service_pb2_grpc,
    density_calculator_service_pb2,
)


class DensityCalculator:
    def __init__(self, host: str) -> None:
        self.host = host

    async def CalculateDensity(
        self,
        lat: float,
        lon: float,
    ):
        async with aio.insecure_channel(
            self.host
        ) as channel:
            stub = density_calculator_service_pb2_grpc.DensityCalculatorServiceStub(
                channel
            )
            req = density_calculator_service_pb2.CalculateDensityRequest(
                latitude=lat,
                longitude=lon,
            )
            return await stub.CalculateDensity(
                req
            )
