from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    code: str
    message: str

    def __str__(self):
        return f"ERROR [{self.code}] {self.message}"
