from wetterdienst.provider.dwd.observation import DwdObservationRequest

request = DwdObservationRequest(
    parameters=("daily", "precipitation_more"),
    periods="historical",
)

print(next(request.all().values.query()))