import base64
import binascii
import json
import zlib
from pathlib import Path


class Records:
    """Best time trial times per course, stored as obfuscated JSON (zlib + base64)."""

    def __init__(self, file_path):
        self.file_path = Path(file_path)
        # course name -> {"race": {"time", "kart"}, "lap": {"time", "kart"}}
        self.data = {}
        self.load()


    def load(self):
        if not self.file_path.exists():
            return
        try:
            decoded = zlib.decompress(base64.b64decode(self.file_path.read_bytes()))
            self.data = json.loads(decoded)
        except (binascii.Error, zlib.error, json.JSONDecodeError):
            print(f"Warning: records file '{self.file_path}' is invalid, starting fresh")
            self.data = {}


    def save(self):
        encoded = base64.b64encode(zlib.compress(json.dumps(self.data).encode()))
        # write to a temp file first, so a crash can't corrupt the records
        temp_path = self.file_path.with_suffix(".tmp")
        temp_path.write_bytes(encoded)
        temp_path.replace(self.file_path)


    def best_time(self, course_name, key):
        # key: "race" or "lap", None if no record yet
        record = self.data.get(course_name, {}).get(key)
        return record["time"] if record else None


    def submit(self, course_name, kart_name, race_time, lap_times):
        # returns (is new race record, is new lap record)
        course_records = self.data.setdefault(course_name, {})
        is_race_record = self._update(course_records, "race", race_time, kart_name)
        is_lap_record = (self._update(course_records, "lap", min(lap_times), kart_name)
                         if lap_times else False)
        if is_race_record or is_lap_record:
            self.save()
        return is_race_record, is_lap_record


    @staticmethod
    def _update(course_records, key, time, kart_name):
        record = course_records.get(key)
        if record is not None and record["time"] <= time:
            return False
        course_records[key] = {"time": time, "kart": kart_name}
        return True