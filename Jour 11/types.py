"""
models/types.py
───────────────
Typed data models for every API response we handle.
Using TypedDict so we get IDE autocompletion with no runtime overhead.
"""

from typing import Optional, TypedDict


# GitHub
class GitHubUser(TypedDict):
    login:        str
    name:         Optional[str]
    location:     Optional[str]
    company:      Optional[str]
    public_repos: int
    followers:    int
    following:    int
    avatar_url:   str
    html_url:     str


class GitHubRepo(TypedDict):
    name:             str
    stargazers_count: int
    forks_count:      int
    language:         Optional[str]
    description:      Optional[str]
    html_url:         str


class GitHubData(TypedDict):
    user:  Optional[GitHubUser]
    repos: list[GitHubRepo]


# Weather 
class WeatherMain(TypedDict):
    temp:       float
    feels_like: float
    humidity:   int
    pressure:   int


class WindData(TypedDict):
    speed: float


class WeatherCondition(TypedDict):
    description: str
    icon:        str


class WeatherSys(TypedDict):
    country: str


class WeatherData(TypedDict):
    name:    str
    main:    WeatherMain
    wind:    WindData
    weather: list[WeatherCondition]
    sys:     WeatherSys
    cod:     int


# News
class NewsSource(TypedDict):
    name: str


class NewsArticle(TypedDict):
    title:       str
    source:      NewsSource
    publishedAt: str
    url:         str
    description: Optional[str]


class NewsData(TypedDict):
    status:   str
    articles: list[NewsArticle]


# Aggregated result 
class AllResults(TypedDict):
    github:  GitHubData
    weather: Optional[WeatherData]
    news:    Optional[NewsData]


# API Status (for circuit breaker) 
class APIStatus(TypedDict):
    name:     str
    healthy:  bool
    failures: int
    state:    str   # "CLOSED" | "OPEN" | "HALF-OPEN"
