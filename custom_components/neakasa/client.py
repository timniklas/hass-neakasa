# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.
import time

from Tea.response import TeaResponse
from Tea.request import TeaRequest
from Tea.core import TeaCore
from Tea.exceptions import UnretryableException
try:
    from typing import Dict
except ImportError:
    pass

from alibabacloud_iot_api_gateway import models as iot_api_gateway_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient
from alibabacloud_apigateway_util.client import Client as APIGatewayUtilClient

import urllib.parse
import json
import hmac
import base64
import hashlib

class Client(object):
    """
    test
    """
    _app_key = None  # type: str
    _app_secret = None  # type: str
    _protocol = None  # type: str
    _user_agent = None  # type: str
    _read_timeout = None  # type: int
    _connect_timeout = None  # type: int
    _http_proxy = None  # type: str
    _https_proxy = None  # type: str
    _no_proxy = None  # type: str
    _max_idle_conns = None  # type: int
    _domain = None  # type: str

    def __init__(self, config):
        self._domain = config.domain
        self._app_key = config.app_key
        self._app_secret = config.app_secret
        self._protocol = config.protocol
        self._read_timeout = config.read_timeout
        self._connect_timeout = config.connect_timeout
        self._http_proxy = config.http_proxy
        self._https_proxy = config.https_proxy
        self._no_proxy = config.no_proxy
        self._max_idle_conns = config.max_idle_conns

    def do_request(self, pathname, protocol, method, header, body, runtime):
        """
        Send request

        @type pathname: str
        @param pathname: the url path

        @type protocol: str
        @param protocol: http or https

        @type method: str
        @param method: example GET

        @type header: Dict[str, str]
        @param header: request header

        @type body: iot_api_gateway_models.IoTApiRequest
        @param body: the object of IoTApiRequest

        @type runtime: util_models.RuntimeOptions
        @param runtime: which controls some details of call api, such as retry times

        @rtype: TeaResponse
        @return: the response
        """
        body.validate()
        runtime.validate()
        _runtime = {
            'timeouted': 'retry',
            'readTimeout': UtilClient.default_number(runtime.read_timeout, self._read_timeout),
            'connectTimeout': UtilClient.default_number(runtime.connect_timeout, self._connect_timeout),
            'httpProxy': UtilClient.default_string(runtime.http_proxy, self._http_proxy),
            'httpsProxy': UtilClient.default_string(runtime.https_proxy, self._https_proxy),
            'noProxy': UtilClient.default_string(runtime.no_proxy, self._no_proxy),
            'maxIdleConns': UtilClient.default_number(runtime.max_idle_conns, self._max_idle_conns),
            'retry': {
                'retryable': runtime.autoretry,
                'maxAttempts': UtilClient.default_number(runtime.max_attempts, 3)
            },
            'backoff': {
                'policy': UtilClient.default_string(runtime.backoff_policy, 'no'),
                'period': UtilClient.default_number(runtime.backoff_period, 1)
            },
            'ignoreSSL': runtime.ignore_ssl
        }
        _last_request = None
        _last_exception = None
        _now = time.time()
        _retry_times = 0
        while TeaCore.allow_retry(_runtime.get('retry'), _retry_times, _now):
            if _retry_times > 0:
                _backoff_time = TeaCore.get_backoff_time(_runtime.get('backoff'), _retry_times)
                if _backoff_time > 0:
                    TeaCore.sleep(_backoff_time)
            _retry_times = _retry_times + 1
            try:
                _request = TeaRequest()
                _request.protocol = UtilClient.default_string(self._protocol, protocol)
                _request.method = UtilClient.default_string(method, 'POST')
                _request.pathname = pathname
                _request.headers = TeaCore.merge({
                    'host': self._domain,
                    'date': UtilClient.get_date_utcstring(),
                    'x-ca-nonce': UtilClient.get_nonce(),
                    'x-ca-key': self._app_key,
                    'x-ca-signaturemethod': 'HmacSHA256',
                    'accept': 'application/json',
                    'user-agent': self.get_user_agent()
                }, header)
                if UtilClient.empty(body.id):
                    body.id = UtilClient.get_nonce()
                if not UtilClient.is_unset(body):
                    _request.headers['content-type'] = 'application/octet-stream'
                    _request.headers['content-md5'] = APIGatewayUtilClient.get_content_md5(UtilClient.to_jsonstring(TeaCore.to_map(body)))
                    _request.body = UtilClient.to_jsonstring(TeaCore.to_map(body))
                _request.headers['x-ca-signature'] = APIGatewayUtilClient.get_signature(_request, self._app_secret)
                _last_request = _request
                _response = TeaCore.do_action(_request, _runtime)
                return _response
            except Exception as e:
                if TeaCore.is_retryable(e):
                    _last_exception = e
                    continue
                raise e
        raise UnretryableException(_last_request, _last_exception)

    def do_request_raw(self, pathname, protocol, method, header, body, runtime):
        """
        Send request

        @type pathname: str
        @param pathname: the url path

        @type protocol: str
        @param protocol: http or https

        @type method: str
        @param method: example GET

        @type header: Dict[str, str]
        @param header: request header

        @type body: str
        @param body: the raw body data

        @type runtime: util_models.RuntimeOptions
        @param runtime: which controls some details of call api, such as retry times

        @rtype: TeaResponse
        @return: the response
        """
        runtime.validate()
        _runtime = {
            'timeouted': 'retry',
            'readTimeout': UtilClient.default_number(runtime.read_timeout, self._read_timeout),
            'connectTimeout': UtilClient.default_number(runtime.connect_timeout, self._connect_timeout),
            'httpProxy': UtilClient.default_string(runtime.http_proxy, self._http_proxy),
            'httpsProxy': UtilClient.default_string(runtime.https_proxy, self._https_proxy),
            'noProxy': UtilClient.default_string(runtime.no_proxy, self._no_proxy),
            'maxIdleConns': UtilClient.default_number(runtime.max_idle_conns, self._max_idle_conns),
            'retry': {
                'retryable': runtime.autoretry,
                'maxAttempts': UtilClient.default_number(runtime.max_attempts, 3)
            },
            'backoff': {
                'policy': UtilClient.default_string(runtime.backoff_policy, 'no'),
                'period': UtilClient.default_number(runtime.backoff_period, 1)
            },
            'ignoreSSL': runtime.ignore_ssl
        }
        _last_request = None
        _last_exception = None
        _now = time.time()
        _retry_times = 0
        while TeaCore.allow_retry(_runtime.get('retry'), _retry_times, _now):
            if _retry_times > 0:
                _backoff_time = TeaCore.get_backoff_time(_runtime.get('backoff'), _retry_times)
                if _backoff_time > 0:
                    TeaCore.sleep(_backoff_time)
            _retry_times = _retry_times + 1
            try:
                _request = TeaRequest()
                _request.protocol = UtilClient.default_string(self._protocol, protocol)
                _request.method = UtilClient.default_string(method, 'POST')
                _request.pathname = pathname
                _request.headers = TeaCore.merge({
                    'host': self._domain,
                    'date': UtilClient.get_date_utcstring(),
                    'x-ca-nonce': UtilClient.get_nonce(),
                    'x-ca-key': self._app_key,
                    'x-ca-signature-method': 'HmacSHA256',
                    'x-ca-signature-Headers': 'x-ca-nonce,x-ca-timestamp,x-ca-key,x-ca-signature-method',
                    'x-ca-timestamp': str(int(time.time())),
                    'accept': 'application/json',
                    'user-agent': self.get_user_agent()
                }, header)
                _request.headers['content-type'] = 'application/x-www-form-urlencoded'

                #body
                body_items = []
                for key in body:
                    body_items.append(key + "=" + urllib.parse.quote_plus(json.dumps(body[key])))
                _request.body = '&'.join(body_items)

                #signature
                body_items = []
                for key in body:
                    body_items.append(key + "=" + json.dumps(body[key]))
                string_to_sign = '%s\n%s\n\n%s\n%s\n%s\n%s\n%s\n%s\n%s' % (
                    _request.method,
                    _request.headers.get('accept'),
                    _request.headers.get('content-type'),
                    _request.headers.get('date'), 
                    f"x-ca-key:{_request.headers.get('x-ca-key')}",
                    f"x-ca-nonce:{_request.headers.get('x-ca-nonce')}",
                    f"x-ca-signature-method:{_request.headers.get('x-ca-signature-method')}",
                    f"x-ca-timestamp:{_request.headers.get('x-ca-timestamp')}",
                    _request.pathname + "?" + '&'.join(body_items)
                )
                hash_val = hmac.new(self._app_secret.encode('utf-8'), string_to_sign.encode('utf-8'), hashlib.sha256).digest()
                _request.headers['x-ca-signature'] = base64.b64encode(hash_val).decode('utf-8')

                _last_request = _request
                _response = TeaCore.do_action(_request, _runtime)
                return _response
            except Exception as e:
                if TeaCore.is_retryable(e):
                    _last_exception = e
                    continue
                raise e
        raise UnretryableException(_last_request, _last_exception)

    def get_user_agent(self):
        """
        Get user agent

        @rtype: str
        @return: user agent
        """
        user_agent = UtilClient.get_user_agent(self._user_agent)
        return user_agent
