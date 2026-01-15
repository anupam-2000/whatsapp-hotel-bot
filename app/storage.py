import pandas as pd
from pathlib import Path

DATA_PATH = Path("data/bookings.xlsx")

class BookingStorage:
    def save(self, booking: dict):
        raise NotImplementedError


class ExcelStorage(BookingStorage):
    def save(self, booking: dict):
        df_new = pd.DataFrame([booking])

        if DATA_PATH.exists():
            df_old = pd.read_excel(DATA_PATH)
            df = pd.concat([df_old, df_new], ignore_index=True)
        else:
            DATA_PATH.parent.mkdir(exist_ok=True)
            df = df_new

        df.to_excel(DATA_PATH, index=False)
