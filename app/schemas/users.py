from pydantic import BaseModel


class UserPreferencesUpdateRequest(BaseModel):
    share_data_with_provider: bool
    automatic_sync: bool
    low_battery_notifications: bool