from dataclasses import dataclass


@dataclass
class JobFailure(Exception):
    job_name: str
    message: str

    def __str__(self) -> str:
        return f"Job {self.job_name} failed with error: `{self.message}`"
