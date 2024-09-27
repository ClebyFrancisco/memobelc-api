# Generated by the protocol buffer compiler.  DO NOT EDIT!
# sources: auth.proto
# plugin: python-betterproto
from dataclasses import dataclass

import betterproto


@dataclass
class RegisterRequest(betterproto.Message):
    name: str = betterproto.string_field(1)
    email: str = betterproto.string_field(2)
    password: str = betterproto.string_field(3)


@dataclass
class RegisterResponse(betterproto.Message):
    message: str = betterproto.string_field(1)


@dataclass
class LoginRequest(betterproto.Message):
    email: str = betterproto.string_field(1)
    password: str = betterproto.string_field(2)


@dataclass
class RefreshToken(betterproto.Message):
    token: str = betterproto.string_field(1)


@dataclass
class LoginResponse(betterproto.Message):
    token: str = betterproto.string_field(1)
    name: str = betterproto.string_field(2)
    email: str = betterproto.string_field(3)


@dataclass
class ErrorResponse(betterproto.Message):
    erro: str = betterproto.string_field(1)


@dataclass
class Empty(betterproto.Message):
    pass
