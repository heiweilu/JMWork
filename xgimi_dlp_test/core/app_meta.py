# -*- coding: utf-8 -*-
"""应用元信息。"""

APP_NAME = 'DLP 自动化测试系统'
APP_VERSION = 'v0.1.6'
APP_SIGNATURE = 'by heiweilu'
APP_AUTHOR_EMAIL = '273925452@qq.com'
DEFAULT_ADMIN_PASSWORD = 'Gimier@0303'


def full_app_title() -> str:
    return f'{APP_NAME} {APP_VERSION} {APP_SIGNATURE}'.strip()