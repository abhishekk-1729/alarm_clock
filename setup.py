from setuptools import setup, find_packages

setup(
    name="alarm-clock",
    version="1.0.0",
    description="A terminal based alarm clock with recurring schedules.",
    packages=find_packages(include=["alarm_clock", "alarm_clock.*"]),
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "alarm=alarm_clock.cli:main",
        ],
    },
)
