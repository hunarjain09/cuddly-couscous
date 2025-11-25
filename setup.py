from setuptools import setup, find_packages

setup(
    name="keystroke-tracker",
    version="2.0.0",
    description="ZSA Voyager Keyboard Layout Optimizer via Keystroke Analysis",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "pynput>=1.7.6",
        "keyboard>=0.13.5",
        "numpy>=1.24.3",
        "pandas>=2.0.2",
        "matplotlib>=3.7.1",
        "scikit-learn>=1.2.2",
        "click>=8.1.3",
        "rich>=13.4.1",
        "tabulate>=0.9.0",
    ],
    entry_points={
        "console_scripts": [
            "keystroke-tracker=keystroke_tracker.cli:cli",
        ],
    },
    python_requires=">=3.8",
)
