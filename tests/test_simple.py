from __future__ import annotations

from typing import Any

from tomlev import BaseConfigModel, TomlEv


class StripeConfig(BaseConfigModel):
    """Configuration for Stripe payment processing."""

    key: str
    domain: str
    product_prd1_price: str
    product_prd1_redirect: str


class DatabaseConfig(BaseConfigModel):
    """Database connection configuration."""

    uri: str
    host: str
    port: int
    user: str
    password: str
    name: str
    queries: dict[str, Any]


class RedisConfig(BaseConfigModel):
    """Redis cache configuration."""

    host: str
    port: int
    keys: list[str]
    nums: list[int]
    atts: list[dict[str, Any]]
    weight: int
    mass: float


class SimpleConfig(BaseConfigModel):
    """Main application configuration."""

    debug: bool
    environment: str
    temp: float
    stripe: StripeConfig
    database: DatabaseConfig
    redis: RedisConfig


def test_simple_env_files():
    env: SimpleConfig = TomlEv(SimpleConfig, "tests/envs/env.simple.toml", "tests/envs/.env.simple").validate()

    # assert variables
    assert env.debug is False
    assert env.environment == "develop"
    assert env.temp == -20.5

    # assert stripe
    assert env.stripe.key == "sk-test-00000"
    assert env.stripe.domain == "example.com"
    assert env.stripe.product_prd1_price == "pk-test-10001"
    assert env.stripe.product_prd1_redirect == "https://example.dev/submit"

    # assert database
    assert env.database.host == "localhost"
    assert env.database.port == 5432
    assert env.database.user == "UserUser"
    assert env.database.password == "PasswordPassword"
    assert env.database.name == "app_db"
    assert env.database.uri == "postgresql://UserUser:PasswordPassword@localhost:5432/app_db"
    assert env.database.queries["get_version"] == """SELECT version();"""
    assert env.database.queries["get_users"] == """SELECT * FROM "users";"""

    # assert redis
    assert env.redis.host == "127.0.0.1"
    assert env.redis.port == 6379
    assert env.redis.keys == ["one", "two", "three"]
    assert env.redis.nums == [10, 12, 99]
    assert env.redis.atts == [{"name": "one", "age": 10}, {"name": "two", "age": 12}]
    assert type(env.redis.weight) is int and env.redis.weight == 0
    assert type(env.redis.mass) is float and env.redis.mass == 0.78
